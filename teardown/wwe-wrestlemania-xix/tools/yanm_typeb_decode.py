#!/usr/bin/env python3
"""YANM Type-B record decode (item 2 of the cycle).

Type-B dir record (a!=0, w28=0x0001xxxx), 32B:
  [+0 hash][+4 a][+8 w8][+12 w12][+16 X][+20 Y][+16 Z][+28 w28]
Probes:
 1. Full 8-word dump of every Type-B record in the extracted .yag set.
 2. X/Y/Z as u32/s32/f32/s16x2 — per-hash constancy vs per-clip variation.
 3. w8 == a+4 claim? w12 content?
 4. The a-offset table: dump bytes at [a, a+64), test 12-byte stride structure.
 5. Cross-check X/Y/Z against known quantities (ycg offsets, ymg offsets).
Works on extracted files in /tmp/wmxix_files (or $WMXIX_FILES).
"""
import os, struct, glob, math
from collections import defaultdict

FDIR = os.environ.get('WMXIX_FILES', '/tmp/wmxix_files')
def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]
def s32(b, i): return struct.unpack('>i', b[i:i+4])[0]
def f32(b, i): return struct.unpack('>f', b[i:i+4])[0]
def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]

def load(name):
    with open(os.path.join(FDIR, name.replace('/', '__')), 'rb') as f:
        return f.read()

def dir_records(data):
    recs = []
    for r in range(60):
        o = 0x50 + r * 32
        if o + 32 > len(data): break
        w = [u32(data, o + i*4) for i in range(8)]
        if w[0] == 0 and w[2] == 0: break
        recs.append((r, w))
    return recs

yags = sorted(glob.glob(os.path.join(FDIR, '*.yag')))
print(f'== files: {len(yags)} ==')

# 1+2. census
typeb = defaultdict(list)  # hash -> [(clipname, r, words)]
for fp in yags:
    name = os.path.basename(fp)
    data = load(name)
    if data[:4] != b'YANM': print('NOT YANM', name); continue
    for r, w in dir_records(data):
        hh, a, w8, w12, X, Y, Z, w28 = w
        if a != 0 and (w28 >> 16) == 1:
            typeb[hh].append((name, r, w, data))

print(f'distinct Type-B hashes: {len(typeb)}')
for hh in sorted(typeb):
    print(f'  {hh:08X}: n={len(typeb[hh])}')

print('\n== full record dumps (first 2 clips per hash) ==')
def fnum(v):
    s = s32(struct.pack('>I', v), 0)
    f = f32(struct.pack('>I', v), 0)
    return f'u32={v:#010x} s32={s} f32={f}'
for hh in sorted(typeb):
    occ = typeb[hh]
    print(f'--- {hh:08X} (n={len(occ)}) ---')
    for name, r, w, data in occ[:2]:
        _, a, w8, w12, X, Y, Z, w28 = w
        print(f'  {name} rec{r}: a={a:#x} w8={w8:#x}(a+4={a+4:#x}) w12={w12:#x} w28={w28:#x}')
        print(f'    X: {fnum(X)}')
        print(f'    Y: {fnum(Y)}')
        print(f'    Z: {fnum(Z)}')

print('\n== X/Y/Z per-hash constancy ==')
for hh in sorted(typeb):
    occ = typeb[hh]
    xs = {w[4] for _, _, w, _ in occ}
    ys = {w[5] for _, _, w, _ in occ}
    zs = {w[6] for _, _, w, _ in occ}
    const = 'CONST' if len(xs) == len(ys) == len(zs) == 1 else 'VARIES'
    print(f'  {hh:08X}: n={len(occ)} {const} dX={len(xs)} dY={len(ys)} dZ={len(zs)}')

print('\n== a-offset table dumps (12-byte stride test) ==')
for hh in sorted(typeb):
    name, r, w, data = typeb[hh][0]
    _, a, w8, w12, X, Y, Z, w28 = w
    seg = data[a:a+64]
    print(f'--- {hh:08X} {name} rec{r} a={a:#x} (file len {len(data)}) ---')
    for i in range(0, min(48, len(seg)), 12):
        chunk = seg[i:i+12]
        words = [u32(chunk, j) for j in range(0, 12, 4)] if len(chunk) == 12 else []
        hexs = ' '.join(f'{x:08X}' for x in words)
        asc = ''.join(chr(c) if 32 <= c < 127 else '.' for c in chunk)
        print(f'    +{i:02d}: {hexs}  |{asc}|')
    # stride test: autocorrelation of the 64B at lag 12
    if len(seg) >= 48:
        m12 = sum(1 for i in range(36) if seg[i] == seg[i+12])
        m4 = sum(1 for i in range(60) if seg[i] == seg[i+4])
        print(f'    lag-12 byte match: {m12}/36, lag-4 byte match: {m4}/60')
