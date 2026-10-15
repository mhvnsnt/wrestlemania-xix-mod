#!/usr/bin/env python3
"""Item-8(d): base-ID generation fn — hierarchical field decomposition test.

Hypothesis: base IDs are tool-assigned hierarchical (family | group | sub |
variant | side), NOT hashes. Decisive tests:
 1. Side-pair XOR codes should use CONSISTENT bit positions within a family
    (the side field lives at fixed bits).
 2. Low-16-bit fields should decompose into small ranges (like 4AAF:
    group{5,6,7} x sub{6,E} x variant{0,3}).
 3. If hierarchical structure holds across all 445 bases, the "generation fn"
    is a namespaced ID scheme — no hash to reverse.
"""
import struct, sys, os
import numpy as np
sys.path.insert(0, 'tools')
from wmxix_range_iso import RangeISO
from gcn_fst import read_header, read_entries, flat_listing

os.environ.setdefault('WMXIX_CACHE',
    '/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/.scratch/cache')

def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]

iso = RangeISO()
h = read_header(iso)
e, nm = read_entries(iso, h['fst_off'], h['fst_size'])
fmap = {p.strip('/'): (o, l) for p, d, o, l in flat_listing(e, nm) if not d}
yags = sorted(p for p in fmap if p.endswith('.yag'))

# collect all track hashes
allh = set()
per_clip = {}
for p in yags:
    o, l = fmap[p]
    iso.seek(o); data = iso.read(min(l, 0x6000))
    hs = set()
    for r in range(29):
        oo = 0x50 + r*32
        if oo + 32 > len(data): break
        hh = u32(data, oo)
        if hh == 0: break
        hs.add(hh); allh.add(hh)
    per_clip[p] = hs
iso.close()
print(f'clips={len(yags)} distinct_hashes={len(allh)}')

# side pairs: exact-XOR pairing (from item-6: codes 0x0F/0xF0/0x780/0x7800/0x1E000000/0xA0/0xA00)
CODES = [0x0F, 0xF0, 0x780, 0x7800, 0x1E000000, 0xA0, 0xA00]
s = set(allh)
pairs = []
used = set()
for hh in sorted(s):
    if hh in used: continue
    for c in CODES:
        if (hh ^ c) in s and (hh ^ c) not in used:
            pairs.append((hh, hh ^ c, c))
            used.add(hh); used.add(hh ^ c)
            break
print(f'side pairs: {len(pairs)}')
for a, b, c in pairs:
    print(f'  {a:08X} ^ {b:08X} = {c:08X} (bits {bin(c)})')

# TEST 1: side-code bit positions consistent within family?
from collections import defaultdict
fam = defaultdict(list)
for a, b, c in pairs:
    fam[a >> 16].append((a, b, c))
print('\n== TEST 1: side-code consistency within family ==')
for f in sorted(fam):
    codes = set(c for _, _, c in fam[f])
    ok = len(codes) == 1
    print(f'  family {f:04X}: {len(fam[f])} pairs, codes={[hex(c) for c in codes]} {"CONSISTENT" if ok else "MIXED!"}')

# TEST 2: hierarchical decomposition of all bases
print('\n== TEST 2: family field analysis ==')
bases = sorted(allh)
fam_all = defaultdict(list)
for b in bases:
    fam_all[b >> 16].append(b & 0xFFFF)
for f in sorted(fam_all):
    lo = fam_all[f]
    if len(lo) >= 3:
        # try: low16 = (group<<12)|(sub<<8)|(variant<<4)|side ?
        print(f'  {f:04X} x{len(lo)}: {sorted(f"0x{v:04X}" for v in lo)[:12]}{"..." if len(lo)>12 else ""}')
        # bit-popcount of pairwise XORs: small = structured
        xors = [bin(a ^ b).count('1') for i, a in enumerate(lo) for b in lo[i+1:]]
        print(f'      pairwise XOR popcount: min={min(xors)} max={max(xors)} mean={np.mean(xors):.1f}')
