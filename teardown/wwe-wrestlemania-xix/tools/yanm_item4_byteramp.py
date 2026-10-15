#!/usr/bin/env python3
"""YANM item-4 (cycle): record-14 byte-region characterization.
Record 14 (66 words) = [selfptr,0] [00000003,00000032] [3 byte-packed words]
[0C5BF279 hash slot] [12-word ID block] [4 words] [byte region to end].
Probe: extract the byte region for several wrestlers, compare per-wrestler
variance, characterize runs/distinct values. Measured only, streams from ISO.
"""
import sys, struct
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

def record14(data):
    hdrs = [o for o in range(0, len(data)-8, 4) if u32(data, o) == o and u32(data, o+4) == 0]
    for hi, o in enumerate(hdrs):
        end = hdrs[hi+1] if hi+1 < len(hdrs) else len(data)
        if (end-o)//4 == 66:
            return o, [u32(data, o+k*4) for k in range(66)]
    return None, None

wrestlers = ['model/wrestler/000_0.ymg', 'model/wrestler/002_0.ymg',
             'model/wrestler/016_0.ymg', 'model/wrestler/045_0.ymg',
             'model/wrestler/045_1.ymg', 'model/wrestler/047_0.ymg',
             'model/wrestler/001_0.ymg']
recs = {}
for wp in wrestlers:
    try:
        data = read(wp)
    except KeyError:
        print(wp, 'MISSING'); continue
    o, w = record14(data)
    if w is None:
        print(wp.split('/')[-1], 'no 66-word record'); continue
    recs[wp] = (o, w)
    # words 20-23 + byte region from word 24
    byts = b''.join(struct.pack('>I', x) for x in w[24:])
    print(f"{wp.split('/')[-1]}: w2-3={[hex(x) for x in w[2:4]]} "
          f"packed={' '.join('%08X'%x for x in w[4:7])} w20-23={' '.join('%08X'%x for x in w[20:24])}")
    print(f"   byte region: {len(byts)}B distinct={len(set(byts))} "
          f"top={Counter(byts).most_common(6)}")

print('\n== byte-region identical across wrestlers? ==')
sigs = {}
for wp, (o, w) in recs.items():
    byts = b''.join(struct.pack('>I', x) for x in w[24:])
    sigs.setdefault(byts, []).append(wp.split('/')[-1])
for s, names in sigs.items():
    print(f'  {len(s)}B sig x{len(names)}: {names}')

print('\n== run-length structure of 000_0 byte region ==')
byts = b''.join(struct.pack('>I', x) for x in recs['model/wrestler/000_0.ymg'][1][24:])
runs = []
cur, n = byts[0], 1
for b in byts[1:]:
    if b == cur: n += 1
    else: runs.append((cur, n)); cur, n = b, 1
runs.append((cur, n))
print('nruns:', len(runs))
print('runs:', [(hex(v), c) for v, c in runs])
