#!/usr/bin/env python3
"""YANM Type-B record decode probe.

Type B (from YANM-ITEM6-CYCLE.md): dir record with a!=0, w28=0x0001xxxx.
32B layout per cycle-2 doc: [hash][a][a+4][0][X][Y][Z][0x00010001].
Probes:
 1. Dump every Type-B record in the 215-clip universe: full 8 words.
 2. Per-hash: are X/Y/Z constant across clips (per-hash) or varying (per-clip)?
 3. Interpret X/Y/Z as u32/s32/f32/s16x2/s8x4.
 4. Read the a-offset table: entry count, stride, entry contents; also w8=a+4 claim.
All streamed from ISO.
"""
import sys, struct, math
from collections import defaultdict
sys.path.insert(0, 'tools')
from gcn_fst import read_header, read_entries, flat_listing

ISO = 'WWE Wrestlemania XIX (USA).iso'
_iso = open(ISO, 'rb')
h = read_header(_iso); e, nm = read_entries(_iso, h['fst_off'], h['fst_size'])
fmap = {p.strip('/'): (o, l) for p, d, o, l in flat_listing(e, nm) if not d}
def read(path):
    o, l = fmap[path]; _iso.seek(o); return _iso.read(l)
def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]
def s32(b, i): return struct.unpack('>i', b[i:i+4])[0]
def f32(b, i): return struct.unpack('>f', b[i:i+4])[0]
def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]
OC5B = 0x0C5BF279

def dir_records(data):
    recs = []
    for r in range(60):
        o = 0x50 + r * 32
        if o + 32 > len(data): break
        words = [u32(data, o+i*4) for i in range(8)]
        hh = words[0]
        if hh == 0 and words[2] == 0: break
        recs.append(words)
    return recs

yags = [p for p in sorted(fmap) if p.endswith('.yag')]
data0 = read(yags[0])
assert data0[:4] == b'YANM'

# --- 1. census of Type-B records ---
typeb = defaultdict(list)   # hash -> list of (clip, words)
w28vals = defaultdict(int)
for p in yags:
    data = read(p)
    if data[:4] != b'YANM': continue
    for w in dir_records(data):
        hh, a, w8, w12, X, Y, Z, w28 = w
        w28vals[w28] += 1
        if a != 0 and (w28 >> 16) == 1:
            typeb[hh].append((p, w))
print('== Type-B census ==')
print(f'clips={len(yags)} distinct Type-B hashes={len(typeb)}')
for hh, occ in sorted(typeb.items()):
    print(f'  {hh:08X}: n={len(occ)} e.g. {occ[0][0].split("/")[-1]}')
print('top w28 values:', sorted(w28vals.items(), key=lambda x: -x[1])[:8])

# --- 2. full record dump for 0C5BF279 in several clips ---
def fmts(words):
    out = []
    for v in words:
        out.append(f'{v:#010x} s32={s32_val(v)} f32={f32_val(v)}')
    return out
def s32_val(v): return struct.unpack('>i', struct.pack('>I', v))[0]
def f32_val(v): return struct.unpack('>f', struct.pack('>I', v))[0]
print('\n== 0C5BF279 full records ==')
for p, w in typeb[OC5B][:8]:
    hh, a, w8, w12, X, Y, Z, w28 = w
    print(f'{p.split("/")[-1]}: a={a:#x} w8={w8:#x} w12={w12:#x} w28={w28:#x}')
    print(f'   X={X:#010x} s32={s32_val(X):d} f32={f32_val(X)}')
    print(f'   Y={Y:#010x} s32={s32_val(Y):d} f32={f32_val(Y)}')
    print(f'   Z={Z:#010x} s32={s32_val(Z):d} f32={f32_val(Z)}')
print('\n== X/Y/Z variance per hash: distinct count ==')
for hh, occ in sorted(typeb.items()):
    xs = {w[4] for _, w in occ}; ys = {w[5] for _, w in occ}; zs = {w[6] for _, w in occ}
    print(f'  {hh:08X}: n={len(occ)} dX={len(xs)} dY={len(ys)} dZ={len(zs)}')
