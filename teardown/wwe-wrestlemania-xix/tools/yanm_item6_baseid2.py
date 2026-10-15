#!/usr/bin/env python3
"""YANM item-6 baseid part 2: joint-track-only rerun (entities excluded).
Entities = base < 0x10000. Tests H1/H2/H7 on joints; entity slot census;
pair side-code census; H4 redo on joint tracks."""
import sys, struct, itertools
from collections import Counter
sys.path.insert(0, 'tools')
from gcn_fst import read_header, read_entries, flat_listing

ISO = 'WWE Wrestlemania XIX (USA).iso'
iso = open(ISO, 'rb')
h = read_header(iso); e, nm = read_entries(iso, h['fst_off'], h['fst_size'])
fmap = {p.strip('/'): (o, l) for p, d, o, l in flat_listing(e, nm) if not d}
_iso = open(ISO, 'rb')
def read(path):
    o, l = fmap[path]; _iso.seek(o); return _iso.read(l)
def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]
def dir_hashes(data):
    out = []
    for r in range(60):
        o = 0x50 + r * 32
        if o + 32 > len(data): break
        hh, ks = u32(data, o), u32(data, o+8)
        if hh == 0 and ks == 0: break
        out.append(hh)
    return out

universe = set()
for p in sorted(fmap):
    if p.endswith('.yag'):
        d = read(p)
        if d[:4] == b'YANM':
            universe |= set(dir_hashes(d))

SIDE = [0x0F, 0xF0, 0x780, 0x7800, 0x1E000000, 0xA0, 0xA00]
def popcnt(x): return bin(x).count('1')
hashes = sorted(universe)
used, pairs = set(), []
for a in hashes:
    if a in used: continue
    for m in SIDE:
        b = a ^ m
        if b in universe and b not in used and popcnt(m) <= 6:
            pairs.append((a, b, m)); used.add(a); used.add(b); break
roots = {}
for a, b, m in pairs:
    r = a & ~m
    roots[a] = r; roots[b] = r
for hh in hashes:
    if hh not in roots:
        roots[hh] = hh
bases = sorted(set(roots.values()))
ent = [b for b in bases if b < 0x10000]
jnt = [b for b in bases if b >= 0x10000]
print(f'bases: {len(bases)} total = {len(ent)} entities(<0x10000) + {len(jnt)} joint-tracks')
print('pairs:', len(pairs), 'side-code census:', Counter(f'{m:08X}' for _,_,m in pairs))

# entity slot census
slots = sorted((b >> 8) for b in ent if (b & 0xFF) == 0x02)
print('entity slots (low byte 02): n=', len(slots), 'range', min(slots), '-', max(slots))
print('  slots:', slots[:60])
nonslot = [f'{b:08X}' for b in ent if (b & 0xFF) != 0x02]
print('entities NOT matching (slot<<8)|0x02:', len(nonslot), nonslot[:20])

# joint bases list
print('joint bases (%d):' % len(jnt), ' '.join(f'{x:08X}' for x in jnt))

# H1 joint-only
best = (0, None); candK = set()
for b in jnt:
    for j in range(500):
        candK.add(b ^ j)
for K in candK:
    cov = sum(1 for b in jnt if (b ^ K) < 500)
    if cov > best[0]: best = (cov, K)
print(f'H1 joint-only: best coverage {best[0]}/{len(jnt)} K={best[1]:08X}' if best[1] is not None else 'H1: none')

# H2 joint-only
perms = list(itertools.permutations(range(8)))
def nibbles(x): return [(x >> (4*i)) & 0xF for i in range(8)]
hits = 0; ex = []
for b in jnt:
    nb = nibbles(b)
    for p in perms:
        v = 0
        for i, src in enumerate(p): v |= nb[src] << (4*i)
        if v < 4096:
            hits += 1; ex.append(f'{b:08X}'); break
print(f'H2 joint-only: {hits}/{len(jnt)} nibble-perm of <4096; e.g. {ex[:6]}')

# H7 joint-only: index hash battery
def idx_hashes(i):
    outs = set()
    for endian in ('big','little'):
        bb = i.to_bytes(4, endian)
        x = 0
        for c in bb: x = (x + c) & 0xFFFFFFFF
        outs.add(x)
        for poly in (31, 33, 131, 65599, 16777619):
            x = 0
            for c in bb: x = (x*poly + c) & 0xFFFFFFFF
            outs.add(x)
            x = 0
            for c in bb: x = (x*poly ^ c) & 0xFFFFFFFF
            outs.add(x)
    return outs
tset = set(jnt); hhits = []
for i in range(5000):
    for hv in idx_hashes(i):
        if hv in tset: hhits.append((i, f'{hv:08X}'))
print('H7 joint-only index-hash hits (0..4999):', len(hhits), hhits[:10])

# family deltas on full universe
print('family-delta check: 60F8F507^6198F405=%08X  613B7507^637B7003=%08X' % (
    0x60F8F507 ^ 0x6198F405, 0x613B7507 ^ 0x637B7003))
# nibble histogram of joint bases vs uniform
nh = Counter()
for b in jnt:
    for i in range(8): nh[(b >> (4*i)) & 0xF] += 1
tot = sum(nh.values())
print('joint nibble histogram:', ' '.join(f'{k:X}:{v/tot:.3f}' for k in range(16)))
# byte0 histogram (side-code byte)
b0 = Counter((b >> 24) & 0xFF for b in jnt)
print('joint high-byte top:', [(f'{k:02X}', v) for k, v in b0.most_common(8)])
print('done')
