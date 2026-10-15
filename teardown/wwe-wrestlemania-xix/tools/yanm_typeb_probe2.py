#!/usr/bin/env python3
"""Type-B probe 2: w28 low16 meaning, X/Y/Z asin-angle test, 5D9B table variance,
12-byte stride retest, X/Y/Z vs ECD correlation.
"""
import os, struct, glob, math

FDIR = os.environ.get('WMXIX_FILES', '/tmp/wmxix_files')
def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]
def s32v(v): return struct.unpack('>i', struct.pack('>I', v))[0]
def load(n):
    with open(os.path.join(FDIR, n), 'rb') as f: return f.read()
def asin_deg(v):
    s = s32v(v) / 2147483648.0
    s = max(-1.0, min(1.0, s))
    return math.degrees(math.asin(s))
def dir_recs(data):
    out = []
    for r in range(60):
        o = 0x50 + r * 32
        if o + 32 > len(data): break
        w = [u32(data, o+i*4) for i in range(8)]
        if w[0] == 0 and w[2] == 0: break
        out.append((r, w))
    return out
def typeb_recs(data):
    return [(r, w) for r, w in dir_recs(data) if w[1] != 0 and (w[7] >> 16) == 1]

print('== 1. w28 low16 vs a-table extent ==')
# For each Type-B record in FACE.yag: dump table, look for structure end.
data = load('viewer__motion__FACE.yag')
for r, w in typeb_recs(data)[:6]:
    hh, a = w[0], w[1]
    lo = w[7] & 0xFFFF
    seg = data[a:a+lo+32]
    # find first run of 8+ zero bytes or non-curve bytes after offset 16
    print(f'{hh:08X} rec{r} a={a:#x} w28lo={lo} ({lo}B)')
    # print first 24 bytes as words + byte at position lo
    print('   head:', ' '.join(f'{u32(seg,i):08X}' for i in range(0, 24, 4)))
    print(f'   byte[{lo}]..byte[{lo+8}]:', seg[lo:lo+8].hex(), '| ascii:', ''.join(chr(c) if 32<=c<127 else '.' for c in seg[lo:lo+8]))

print('\n== 2. X/Y/Z as asin-degrees (all Type-B, all clips) ==')
for fp in sorted(glob.glob(os.path.join(FDIR, '*.yag'))):
    name = os.path.basename(fp)
    d = load(name)
    if d[:4] != b'YANM': continue
    for r, w in typeb_recs(d):
        hh = w[0]
        if hh in (0x0C5BF279,) or (w[4] | w[5] | w[6]):
            ax, ay, az = asin_deg(w[4]), asin_deg(w[5]), asin_deg(w[6])
            print(f'{name} {hh:08X}: X={ax:7.2f} Y={ay:7.2f} Z={az:7.2f}')

print('\n== 3. 5D9B family: table identical FACE vs HAND? ==')
for clip in ['viewer__motion__FACE.yag', 'viewer__motion__HAND.yag']:
    d = load(clip)
    for r, w in typeb_recs(d):
        if (w[0] >> 8) == 0x5D9B19 or (w[0] >> 8) in (0x5D9B1A, 0x5D9B1B):
            a = w[1]
            print(f'{clip.split("__")[-1]} {w[0]:08X} a={a:#x} tablehead={data[a:a+16].hex() if False else d[a:a+16].hex()}')

print('\n== 4. ECD pose vs 0C5BF279 X/Y/Z per clip ==')
ECD = 0xECD28978
def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]
for fp in sorted(glob.glob(os.path.join(FDIR, '*.yag'))):
    name = os.path.basename(fp)
    d = load(name)
    if d[:4] != b'YANM': continue
    recs = {w[0]: (r, w) for r, w in dir_recs(d)}
    if ECD in recs and 0x0C5BF279 in recs:
        _, we = recs[ECD]
        _, wb = recs[0x0C5BF279]
        # ECD is Type-A static: ks at w[2], w28=key count
        ks, n = we[2], we[7]
        if we[1] == 0 and n >= 1:
            e1, e2 = s16(d, ks), s16(d, ks+3)
            ea = (math.degrees(math.asin(max(-1,min(1,e1/32767.0)))),
                  math.degrees(math.asin(max(-1,min(1,e2/32767.0)))))
            ba = (asin_deg(wb[4]), asin_deg(wb[5]), asin_deg(wb[6]))
            print(f'{name}: ECD=({ea[0]:6.1f},{ea[1]:6.1f})  0C5B=({ba[0]:6.1f},{ba[1]:6.1f},{ba[2]:6.1f})')
