#!/usr/bin/env python3
"""YANM item 4: decode the joint base-ID assignment scheme.
track_id = base_id XOR side_code. Streams yag list from ISO (hashes only)."""
import sys, struct
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32
from gcn_fst import read_header, read_entries, flat_listing

ISO = 'WWE Wrestlemania XIX (USA).iso'
with open(ISO, 'rb') as iso:
    h = read_header(iso); e, nm = read_entries(iso, h['fst_off'], h['fst_size'])
    listing = flat_listing(e, nm)
fmap = {p.strip('/').lstrip('/'): (o, l) for p, d, o, l in listing if not d}
_iso = open(ISO, 'rb')
def read(path):
    o, l = fmap[path]
    _iso.seek(o); return _iso.read(l)

def dir_hashes(data):
    out = []
    for r in range(29):
        o = 0x50 + r * 32
        if o + 32 > len(data): break
        hh, a, ks = u32(data, o), u32(data, o+4), u32(data, o+8)
        if hh == 0 and ks == 0: break
        out.append(hh)
    return out

universe = set()
for p in sorted(fmap):
    if p.startswith('ringmotion/') and p.endswith('.yag'):
        d = read(p)
        if d[:4] == b'YANM':
            universe |= set(dir_hashes(d))
print('ringmotion hash universe:', len(universe))

# pair-XOR census (popcount<=6), greedy pairing
hashes = sorted(universe)
def popcnt(x): return bin(x).count('1')
pairs = []
used = set()
for a in hashes:
    if a in used: continue
    best = None
    for b in hashes:
        if b <= a or b in used: continue
        x = a ^ b
        if popcnt(x) <= 6:
            if best is None or popcnt(x) < popcnt(best[1] ^ a):
                best = (b, x)
    if best:
        pairs.append((a, best[0], best[1])); used.add(a); used.add(best[0])
print('pairs found:', len(pairs))
from collections import Counter
print('side-code census:', Counter(f'{x:08X}' for _, _, x in pairs))

# assign side codes, compute roots
SIDE = {}
for a, b, x in pairs:
    # side code = xor; the member with the code's bits "less set" is base side
    SIDE[a] = x; SIDE[b] = x
roots = {}
for hh in hashes:
    if hh in SIDE:
        roots[hh] = hh & ~SIDE[hh]
    else:
        roots[hh] = hh  # unpaired: root unknown, keep raw
print()
print('=== roots (sorted) ===')
for hh in sorted(roots, key=lambda h: roots[h]):
    r = roots[hh]
    sc = SIDE.get(hh, 0)
    tag = 'pair' if hh in SIDE else 'SINGLE'
    print(f'  {hh:08X} ^ {sc:08X} = {r:08X}  {tag}  low16={r & 0xFFFF:04X}')
