#!/usr/bin/env python3
"""YANM item-6: base-ID generation function hypotheses.
H1 fixed-key XOR with small index set; H2 nibble-permutation of small ints;
H3 relation to (slot<<8)|0x02 entities; H4 base-ID order vs ycg/ymg bone order;
H5 verbatim base-ID occurrence in ymg/ycg tables; H6 DDF67B-run relation;
H7 poly/additive hash of small integers (index-hash battery)."""
import sys, struct, itertools, math
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
print('full hash universe:', len(universe))

SIDE = [0x0F, 0xF0, 0x780, 0x7800, 0x1E000000, 0xA0, 0xA00]
def popcnt(x): return bin(x).count('1')
hashes = sorted(universe)
used, pairs = set(), []
for a in hashes:
    if a in used: continue
    best = None
    for m in SIDE:
        b = a ^ m
        if b in universe and b not in used and popcnt(m) <= 6:
            best = (b, m); break
    if best:
        pairs.append((a, best[0], best[1])); used.add(a); used.add(best[0])
print('pairs:', len(pairs))
roots = {}
for a, b, m in pairs:
    r = a & ~m
    roots[a] = r; roots[b] = r
for hh in hashes:
    if hh not in roots:
        roots[hh] = hh
base_ids = sorted(set(roots.values()))
print('distinct base IDs:', len(base_ids))
print('bases:', ' '.join(f'{x:08X}' for x in base_ids[:40]))

# ---------- H1: base = index XOR K ----------
print('\n== H1: exists K with {base XOR K} subset of small ints ==')
best = (0, None)
candK = set()
for b in base_ids:
    for j in range(300):
        candK.add(b ^ j)
for K in candK:
    cov = sum(1 for b in base_ids if (b ^ K) < 300)
    if cov > best[0]:
        best = (cov, K)
print(f'  best coverage: {best[0]}/{len(base_ids)} with K={best[1]:08X}' if best[1] is not None else '  none')

# ---------- H2: nibble permutation of small int ----------
print('== H2: nibble-permutation of small int (<4096) ==')
perms = list(itertools.permutations(range(8)))
def nibbles(x): return [(x >> (4*i)) & 0xF for i in range(8)]
hits = 0
hit_ex = []
for b in base_ids:
    nb = nibbles(b)
    found = False
    for p in perms:
        v = 0
        for i, src in enumerate(p):
            v |= nb[src] << (4*i)
        if v < 4096:
            found = True; break
    if found:
        hits += 1; hit_ex.append(f'{b:08X}')
print(f'  {hits}/{len(base_ids)} base IDs are a nibble-permutation of a <4096 int; e.g. {hit_ex[:8]}')

# ---------- H3: entity relation ----------
print('== H3: low-word / slot relation ==')
ENT = {0x8102,0x9202,0x9302,0x9D02,0x9E02,0xD402,0xD502}
lo = Counter(b & 0xFFFF for b in base_ids)
print('  base IDs with low16 in entity set:', sum(1 for b in base_ids if (b & 0xFFFF) in ENT))
print('  base IDs with low byte 0x02:', sum(1 for b in base_ids if (b & 0xFF) == 0x02))
print('  distinct low16 values:', len(lo), 'top:', lo.most_common(6))
hi = Counter((b >> 16) & 0xFFFF for b in base_ids)
print('  distinct high16 values:', len(hi), 'top:', hi.most_common(6))
# low byte distribution
lob = Counter(b & 0xFF for b in base_ids)
print('  low-byte values:', sorted(f'{k:02X}' for k in lob))

# ---------- H4: order correlation with ycg record order ----------
print('== H4: base-ID sort order vs ycg record order ==')
ycg = read('model/wrestler/000_0.ycg')
n = u32(ycg, 0)
ych = [u32(ycg, 4+r*56) for r in range(n)]
seq = [(r, ych[r], roots.get(ych[r])) for r in range(n) if ych[r] in roots]
print(f'  ycg records with known base: {len(seq)}/{n}')
if len(seq) > 3:
    order_ycg = [r for r, _, _ in seq]
    order_base = sorted(range(len(seq)), key=lambda i: seq[i][2])
    rk = {v: i for i, v in enumerate(order_ycg)}
    xs = list(range(len(seq))); ys = [rk[order_ycg[i]] for i in order_base]
    # spearman
    n2 = len(xs)
    mx, my = sum(xs)/n2, sum(ys)/n2
    cov = sum((x-mx)*(y-my) for x, y in zip(xs, ys))/n2
    sx = (sum((x-mx)**2 for x in xs)/n2)**0.5; sy = (sum((y-my)**2 for y in ys)/n2)**0.5
    print(f'  spearman(base-sort, ycg-order) = {cov/(sx*sy):.3f} (n={n2})')

# ---------- H5: verbatim base-ID scan in ymg/ycg ----------
print('== H5: verbatim base-ID words in model files ==')
targets = set(base_ids)
for name in ('model/wrestler/000_0.ymg', 'model/wrestler/000_0.ycg',
             'model/wrestler/045_0.ymg', 'model/wrestler/016_0.ymg'):
    try: data = read(name)
    except KeyError: print('  ', name, 'missing'); continue
    found = Counter()
    for i in range(0, len(data)-4, 4):
        v = u32(data, i)
        if v in targets:
            found[v] += 1
    print(f'  {name}: {len(found)} distinct base IDs present verbatim, total hits={sum(found.values())}')
    for v, c in found.most_common(8):
        print(f'     {v:08X} x{c}')

# ---------- H6: DDF67B run relation ----------
print('== H6: XOR distance to 045 ID-block run ==')
run = [0xDDF67B76+i for i in range(10)] + [0xDDF67BFE, 0x5D98B7F1]
bestd = None
for b in base_ids:
    for r in run:
        d = popcnt(b ^ r)
        if bestd is None or d < bestd[0]:
            bestd = (d, b, r)
print(f'  min popcount(base XOR runword) = {bestd[0]} for base {bestd[1]:08X} ^ run {bestd[2]:08X}')
close = sum(1 for b in base_ids for r in run if popcnt(b ^ r) <= 8)
print(f'  pairs with popcount<=8: {close}')

# ---------- H7: index-hash battery ----------
print('== H7: poly/additive hash of small ints ==')
def idx_hashes(i):
    b = i.to_bytes(4, 'big')
    out = set()
    out.add(sum(b) & 0xFFFFFFFF)
    x = 0
    for c in b: x = (x + c) & 0xFFFFFFFF
    out.add(x)
    x = 0
    for c in b: x ^= c
    out.add(x)
    for poly in (31, 33, 131, 65599, 16777619):
        x = 0
        for c in b: x = (x * poly + c) & 0xFFFFFFFF
        out.add(x)
        x = 0
        for c in b: x = (x * poly ^ c) & 0xFFFFFFFF
        out.add(x)
    # also LE
    bl = i.to_bytes(4, 'little')
    x = 0
    for c in bl: x = (x * 31 + c) & 0xFFFFFFFF
    out.add(x)
    return out
tset = set(base_ids)
hits = []
for i in range(2000):
    for hv in idx_hashes(i):
        if hv in tset:
            hits.append((i, f'{hv:08X}'))
print('  index-hash hits:', len(hits), hits[:10])
print('done')
