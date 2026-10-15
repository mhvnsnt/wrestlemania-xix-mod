#!/usr/bin/env python3
"""Arena texture extractor: bg/*.tex -> TPL carve -> PNG.

.tex container (measured): [u32 LE count][u32 0x10000][u32 0][u32 0x10]
  + count x [16B name]["tpl\\0"][u32 LE size][u32 LE offset][u32 0]
Each entry is a standard GameCube TPL (magic 0020AF30) -> decode_tpl.py -> PNG.

For each of the 43 arena .ymg files (same filter as extract_all_arenas.py),
takes the same-basename .tex and decodes every TPL entry.
Writes textures/<arena>/<entry>.png + textures/TEX-README.md.

Usage: python3 extract_arena_textures.py [outdir]
"""
import struct, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from extract_yanm import ISOReader
from decode_tpl import parse_tpl, decode_image

def u32le(b, i): return struct.unpack('<I', b[i:i+4])[0]

def parse_tex_container(data):
    n = u32le(data, 0)
    entries = []
    for i in range(n):
        e = 0x10 + i*32
        if e + 32 > len(data):
            break
        name = data[e:e+16].split(b'\x00')[0].decode('ascii', errors='replace')
        magic = data[e+16:e+20]
        size = u32le(data, e+20); off = u32le(data, e+24)
        entries.append((name, magic, size, off))
    return entries

def arena_ymg_list(rdr):
    return sorted(p for p in rdr.files
                  if p.startswith('bg/') and p.endswith('.ymg')
                  and not any(s in p for s in
                              ('_light', '_scr', '_ent', '_gt', '_add', 'sc2', 'ight')))

def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'textures')
    os.makedirs(outdir, exist_ok=True)
    rdr = ISOReader()
    arenas = arena_ymg_list(rdr)
    print(f'{len(arenas)} arenas')
    total_png = 0
    manifest = []
    for ap in arenas:
        base = os.path.basename(ap).replace('.ymg', '')
        texp = ap.replace('.ymg', '.tex')
        adir = os.path.join(outdir, base)
        if texp not in rdr.files:
            manifest.append(f'{base}: NO .tex companion')
            continue
        o, l = rdr.files[texp]
        rdr.f.seek(o)
        data = rdr.f.read(l)
        entries = parse_tex_container(data)
        ok = 0
        for name, magic, size, off in entries:
            if magic != b'tpl\0' or off + size > len(data):
                continue
            tpl = data[off:off+size]
            if len(tpl) < 12 or struct.unpack('>I', tpl[:4])[0] != 0x0020AF30:
                continue
            try:
                imgs = parse_tpl(tpl)
            except Exception:
                continue
            for i, im in enumerate(imgs):
                try:
                    img = decode_image(tpl, im)
                except Exception:
                    continue
                os.makedirs(adir, exist_ok=True)
                fn = f'{name}.png' if len(imgs) == 1 else f'{name}_img{i}.png'
                img.save(os.path.join(adir, fn))
                ok += 1
        total_png += ok
        manifest.append(f'{base}: {texp} ({l} B) -> {ok} PNGs from {len(entries)} entries')
        print(f'  {base}: {ok} PNGs', flush=True)
    rdr.f.close()
    with open(os.path.join(outdir, 'TEX-MANIFEST.txt'), 'w') as f:
        f.write('\n'.join(manifest) + '\n')
    print(f'DONE: {total_png} PNGs')

if __name__ == '__main__':
    main()
