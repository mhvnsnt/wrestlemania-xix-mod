#!/usr/bin/env python3
"""ECD marginal distribution + variant-pair analysis across all 215 yag clips.

Tests whether ECD channels look like (yaw, pitch): yaw should spread wide /
uniform-ish, pitch should cluster near low elevations. Symmetric marginals
would argue against a yaw/pitch reading.
"""
import struct, sys, os, math
import numpy as np
sys.path.insert(0, 'tools')
from wmxix_range_iso import RangeISO
from gcn_fst import read_header, read_entries, flat_listing

os.environ.setdefault('WMXIX_CACHE',
    '/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/.scratch/cache')

def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]
def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]
def adeg(v): return math.degrees(math.asin(max(-1.0, min(1.0, v/32767.0))))

iso = RangeISO()
h = read_header(iso)
e, nm = read_entries(iso, h['fst_off'], h['fst_size'])
fmap = {p.strip('/:'): (o, l) for p, d, o, l in flat_listing(e, nm) if not d}
yags = sorted(p for p in fmap if p.endswith('.yag'))
print(f'{len(yags)} yag clips')

def get_ecd(path):
    o, l = fmap[path]
    iso.seek(o); data = iso.read(min(l, 0x5000))
    for r in range(29):
        oo = 0x50 + r*32
        if oo + 32 > len(data):
            break
        if u32(data, oo) == 0xECD28978:
            a, b, w28 = u32(data, oo+4), u32(data, oo+8), u32(data, oo+28)
            if a != 0 or w28 != 1:
                return None
            iso.seek(o+b); raw = iso.read(5)
            return adeg(s16(raw, 0)), adeg(s16(raw, 3))
    return None

rows = []
for p in yags:
    v = get_ecd(p)
    rows.append((p, v))
iso.close()

have = [(p, v) for p, v in rows if v]
print(f'ECD present: {len(have)}/{len(rows)}')
c1 = np.array([v[0] for _, v in have]); c2 = np.array([v[1] for _, v in have])
for nm_, c in (('ch1', c1), ('ch2', c2)):
    hist, edges = np.histogram(c, bins=18, range=(-90, 90))
    print(f'--- {nm_} ---')
    for i in range(18):
        print(f'  {edges[i]:+6.1f}..{edges[i+1]:+6.1f}: {hist[i]:3d} {"#"*hist[i]}')
print('ch1: mean=%+.1f std=%.1f |ch|>45: %d/%d' % (c1.mean(), c1.std(), (np.abs(c1)>45).sum(), len(c1)))
print('ch2: mean=%+.1f std=%.1f |ch|>45: %d/%d' % (c2.mean(), c2.std(), (np.abs(c2)>45).sum(), len(c2)))

# variant pairs: same letter+number, different _Na suffix
from collections import defaultdict
fam = defaultdict(list)
for p, v in have:
    base = p.split('/')[-1]
    # key: strip trailing _Na (e.g. c200_0a -> c200)
    import re
    m = re.match(r'([a-z]+\d+)(_\da)?\.yag', base)
    if m:
        fam[m.group(1)].append((base, v))
print('\n--- variant families with differing ECD ---')
for k in sorted(fam):
    if len(fam[k]) > 1:
        vs = set((round(v[0],1), round(v[1],1)) for _, v in fam[k])
        if len(vs) > 1:
            print(f'  {k}: ' + ' '.join(f'{b}=({v[0]:.1f},{v[1]:.1f})' for b, v in sorted(fam[k])))

# save
import json
json.dump([{'clip': p, 'ecd': list(v) if v else None} for p, v in rows],
          open('docs/ecd-render-test/ecd_all_clips.json', 'w'), indent=0)
print('\nsaved docs/ecd-render-test/ecd_all_clips.json')
