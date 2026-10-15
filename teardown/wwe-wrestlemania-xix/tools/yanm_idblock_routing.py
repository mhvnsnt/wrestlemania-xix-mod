#!/usr/bin/env python3
"""Item-8(b): ID-block -> POF0 segment routing test.

For each wrestler ymg: extract the 12-word ID block (after 0C5BF279) and the
12 POF0 segments (14B each). Tests:
 1. Does byte-region equality track ID-block equality? (pairwise)
 2. Per-word routing: does segment s differ iff ID word k differs?
    (contingency over wrestler pairs; perfect routing = diagonal contingency)
 3. Flat-0x44 segments: are they literally identity in any testable sense?
"""
import struct, os, itertools
import numpy as np

SCRATCH = ('/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/'
           'wwe-wrestlemania-xix/.scratch/files')

def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]

def parse_ymg(path):
    d = open(path, 'rb').read()
    j = d.find(struct.pack('>I', 0x0C5BF279))
    if j < 0:
        return {'idblock': None, 'segs': None}
    idblock = [u32(d, j+4+k*4) for k in range(12)]
    i = d.find(b'POF0')
    if i < 0:
        return {'idblock': idblock, 'segs': None}
    ln = u32(d, i+4)
    reg = d[i+8:i+8+ln]
    nseg = ln // 14
    segs = [reg[s*14:(s+1)*14] for s in range(nseg)]
    return {'idblock': idblock, 'segs': segs, 'poflen': ln}

names = ['000_0', '047_0', '045_0', '016_0', '002_0', '001_0']
P = {n: parse_ymg(os.path.join(SCRATCH, f'model__wrestler__{n}.ymg')) for n in names}

for n in names:
    p = P[n]
    ib = ' '.join(f'{w:08X}' for w in p['idblock']) if p['idblock'] else 'NONE'
    ns = len(p['segs']) if p['segs'] else 0
    print(f'{n}: idblock=[{ib}] nseg={ns} poflen={p.get("poflen")}')

print('\n== pairwise: ID-block equal? region equal? ==')
for a, b in itertools.combinations(names, 2):
    pa, pb = P[a], P[b]
    if pa['idblock'] is None or pb['idblock'] is None:
        print(f'{a}-{b}: missing idblock'); continue
    if pa['segs'] is None or pb['segs'] is None:
        print(f'{a}-{b}: missing segs'); continue
    ib_eq = pa['idblock'] == pb['idblock']
    # region compare over min segments
    ns = min(len(pa['segs']), len(pb['segs']))
    seg_eq = [pa['segs'][s] == pb['segs'][s] for s in range(ns)]
    print(f'{a}-{b}: idblock_eq={ib_eq} segs_eq={seg_eq} '
          f'nsegs={len(pa["segs"])}/{len(pb["segs"])}')

print('\n== per-word routing contingency (seg s differs iff word k differs) ==')
# over all pairs with both idblock+segs, 12 words x 12 segs
pairs = [(a, b) for a, b in itertools.combinations(names, 2)
         if P[a]['idblock'] and P[b]['idblock'] and P[a]['segs'] and P[b]['segs']
         and len(P[a]['segs']) == 12 and len(P[b]['segs']) == 12]
print(f'{len(pairs)} usable pairs')
if pairs:
    # contingency[k][s] = (both_same, word_differs_seg_same, word_same_seg_differs, both_differ)
    cont = np.zeros((12, 12, 4), int)
    for a, b in pairs:
        wd = [1 if P[a]['idblock'][k] != P[b]['idblock'][k] else 0 for k in range(12)]
        sd = [1 if P[a]['segs'][s] != P[b]['segs'][s] else 0 for s in range(12)]
        for k in range(12):
            for s in range(12):
                cont[k, s, wd[k]*2 + sd[s]] += 1
    # print agreement rate per (k,s): (both_same+both_differ)/total
    tot = len(pairs)
    print('agreement[word k][seg s] (1.00 = perfect routing/deterministic link):')
    hdr = '     ' + ' '.join(f's{s:2d}' for s in range(12))
    print(hdr)
    for k in range(12):
        row = ' '.join(f'{((cont[k,s,0]+cont[k,s,3])/tot):.2f}' for s in range(12))
        print(f'w{k:2d}: {row}')
    # also: which segs EVER differ, which words EVER differ
    print('\nwords that ever differ:', [k for k in range(12) if cont[k, :, 2:].sum() > 0 or True])
    wdiff = [k for k in range(12) if any(P[a]['idblock'][k] != P[b]['idblock'][k] for a, b in pairs)]
    sdiff = [s for s in range(12) if any(P[a]['segs'][s] != P[b]['segs'][s] for a, b in pairs)]
    print('words ever differing across pairs:', wdiff)
    print('segs ever differing across pairs:', sdiff)

print('\n== flat-0x44 segment check ==')
for n in names:
    p = P[n]
    if not p['segs']: continue
    flat = [s for s in range(len(p['segs'])) if set(p['segs'][s]) == {0x44}]
    print(f'{n}: flat-0x44 segs = {flat}')
