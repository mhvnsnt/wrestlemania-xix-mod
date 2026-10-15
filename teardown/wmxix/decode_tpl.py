#!/usr/bin/env python3
"""GameCube TPL texture decoder -> PNG.

TPL layout (measured on WMXIX, matches standard GC TPL):
  u32 magic 0x0020AF30, u32 numImages, u32 imageTableOffset
  image table: numImages x u32 -> image header offset
  image header (36B):
    u16 height, u16 width, u32 format, u32 dataOffset,
    u32 wrapS, u32 wrapT, u32 minFilter, u32 magFilter,
    f32 lodBias, u8 edgeLOD, u8 minLOD, u8 maxLOD, u8 unpacked
  palette header (after image headers, for C4/C8/C14X2):
    u16 numEntries, u16 pad?, u32 palFormat(0=IA8,1=RGB565,2=RGB5A3), u32 palOffset

Formats: 0=I4 1=I8 2=IA4 3=IA8 4=RGB565 5=RGB5A3 6=RGBA8
         8=C4 9=C8 10=C14X2 14=CMPR(S3TC/DXT1)
Tiles are Z-ordered 8x8 (I4/C4/CMPR) or 8x4 (I8/IA4/C8) or 4x4 (others).

Usage: decode_tpl.py <in.tpl> [out.png]   (decodes first image)
       as module: decode_tpl_image(data) -> PIL Image list
"""
import struct, sys, os

def u16(b, i): return struct.unpack('>H', b[i:i+2])[0]
def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]

def rgb5a3(px):
    if px & 0x8000:
        r = (px >> 10) & 0x1F; g = (px >> 5) & 0x1F; b = px & 0x1F
        return (r*255//31, g*255//31, b*255//31, 255)
    a = (px >> 12) & 0x7; r = (px >> 8) & 0xF; g = (px >> 4) & 0xF; b = px & 0xF
    return (r*17, g*17, b*17, a*255//7)

def rgb565(px):
    r = (px >> 11) & 0x1F; g = (px >> 5) & 0x3F; b = px & 0x1F
    return (r*255//31, g*255//63, b*255//31, 255)

def ia8(px):
    return (px & 0xFF,)*3 + ((px >> 8),)

def ia4(px):
    a = (px >> 4) & 0xF; i = px & 0xF
    return (i*17, i*17, i*17, a*17)

PAL_DECODERS = {0: ia8, 1: rgb565, 2: rgb5a3}

def decode_tile(data, off, fmt, pal):
    """Decode one tile at off; returns list of (tile_w*tile_h) RGBA tuples in row-major."""
    if fmt == 0:  # I4, 8x8, 32B: 2 px/byte
        px = []
        for i in range(32):
            b = data[off+i]
            v = (b >> 4)*17; px.append((v, v, v, 255))
            v = (b & 0xF)*17; px.append((v, v, v, 255))
        return px, 8, 8
    if fmt == 1:  # I8, 8x4, 32B
        return [(b, b, b, 255) for b in data[off:off+32]], 8, 4
    if fmt == 2:  # IA4, 8x4, 32B
        return [ia4(b) for b in data[off:off+32]], 8, 4
    if fmt == 3:  # IA8, 4x4, 64B
        px = [ia8(u16(data, off+i*2)) for i in range(32)]
        return px, 4, 4
    if fmt == 4:  # RGB565, 4x4, 64B... actually 32B
        px = [rgb565(u16(data, off+i*2)) for i in range(16)]
        return px, 4, 4
    if fmt == 5:  # RGB5A3, 4x4, 32B
        px = [rgb5a3(u16(data, off+i*2)) for i in range(16)]
        return px, 4, 4
    if fmt == 6:  # RGBA8, 4x4, 64B (AR block then GB block)
        px = []
        for i in range(16):
            a = data[off+i*2]; r = data[off+i*2+1]
            b = data[off+32+i*2]; g = data[off+32+i*2+1]
            px.append((r, g, b, a))
        return px, 4, 4
    if fmt in (8, 9, 10):  # paletted
        bpp = {8: 4, 9: 8, 10: 8}[fmt]
        tw, th = (8, 8) if fmt == 8 else (8, 4)
        npx = tw*th
        idx = []
        raw = data[off:off+npx*bpp//8]
        if bpp == 4:
            for b in raw:
                idx += [b >> 4, b & 0xF]
        else:
            idx = list(raw)
        return [pal[i] for i in idx], tw, th
    if fmt == 14:  # CMPR, 8x8, 32B = 4 DXT1 sub-blocks
        px = [(0, 0, 0, 0)]*64
        for s in range(4):
            so = off + s*8
            c0 = rgb565(u16(data, so)); c1 = rgb565(u16(data, so+2))
            bits = u32(data, so+4)
            if u16(data, so) > u16(data, so+2):
                lut = [c0, c1,
                       tuple((2*c0[i]+c1[i])//3 for i in range(3)) + (255,),
                       tuple((c0[i]+2*c1[i])//3 for i in range(3)) + (255,)]
            else:
                lut = [c0, c1,
                       tuple((c0[i]+c1[i])//2 for i in range(3)) + (255,),
                       (0, 0, 0, 0)]
            for p in range(16):
                c = lut[(bits >> (p*2)) & 3]
                sx, sy = (s % 2)*4 + p % 4, (s // 2)*4 + p // 4
                px[sy*8+sx] = c
        return px, 8, 8
    raise ValueError(f'unsupported format {fmt}')

TILE_GEOM = {0: (8, 8, 32), 1: (8, 4, 32), 2: (8, 4, 32), 3: (4, 4, 64),
             4: (4, 4, 32), 5: (4, 4, 32), 6: (4, 4, 64),
             8: (8, 8, 32), 9: (8, 4, 32), 10: (8, 4, 32), 14: (8, 8, 32)}

def parse_tpl(data):
    assert u32(data, 0) == 0x0020AF30, 'not TPL'
    n = u32(data, 4); toff = u32(data, 8)
    imgs = []
    for i in range(n):
        h = u32(data, toff + i*4)
        height, width = u16(data, h), u16(data, h+2)
        fmt = u32(data, h+4); doff = u32(data, h+8)
        imgs.append(dict(height=height, width=width, format=fmt,
                         data_off=doff, hdr_off=h))
    # palette headers follow the last image header (36B each)
    if imgs and imgs[0]['format'] in (8, 9, 10):
        ph = imgs[-1]['hdr_off'] + 36
        nent = u16(data, ph); pfmt = u32(data, ph+4); poff = u32(data, ph+8)
        dec = PAL_DECODERS[pfmt]
        pal = [dec(u16(data, poff+i*2)) for i in range(nent)]
        for im in imgs:
            im['palette'] = pal
    return imgs

def decode_image(data, im):
    from PIL import Image
    w, h, fmt = im['width'], im['height'], im['format']
    tw, th, tb = TILE_GEOM[fmt]
    pal = im.get('palette')
    img = Image.new('RGBA', (w, h))
    px = img.load()
    off = im['data_off']
    for ty in range(0, h, th):
        for tx in range(0, w, tw):
            tile, _, _ = decode_tile(data, off, fmt, pal)
            off += tb
            for y in range(th):
                for x in range(tw):
                    if tx+x < w and ty+y < h:
                        px[tx+x, ty+y] = tile[y*tw+x]
    return img

def decode_tpl_image(data, idx=0):
    return decode_image(data, parse_tpl(data)[idx])

def main():
    src = sys.argv[1]
    data = open(src, 'rb').read()
    imgs = parse_tpl(data)
    print(f'{src}: {len(imgs)} image(s)')
    for i, im in enumerate(imgs):
        img = decode_image(data, im)
        out = sys.argv[2] if len(sys.argv) > 2 and len(imgs) == 1 \
            else os.path.splitext(src)[0] + (f'_img{i}' if len(imgs) > 1 else '') + '.png'
        img.save(out)
        print(f'  img{i}: {im["width"]}x{im["height"]} fmt={im["format"]} -> {out}')

if __name__ == '__main__':
    main()
