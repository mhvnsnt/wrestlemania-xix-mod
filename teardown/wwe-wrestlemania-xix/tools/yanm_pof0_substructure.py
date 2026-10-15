#!/usr/bin/env python3
"""Item-10(1) part 2: POF0 sub-structure / linearity / 045.

Reads ymg from .scratch (range-ISO extracts). Probes:
(a) 14B segment internal structure: marker-byte positions, active-tail split.
(b) linearity: fit line to active bytes per segment; report R^2 / residuals.
(c) 045_0 264B POF0 + 002_0 268B: marker map, segmentation hypotheses,
    relation to the longer ID list.
"""
import os, struct, json, math
from collections import Counter

SCR = '/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/.scratch/files'
OUT = {}

def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]

def record14(data):
    hdrs = [o for o in range(0, len(data)-8, 4) if u32(data, o) == o and u32(data, o+4) == 0]
    for hi, o in enumerate(hdrs):
        end = hdrs[hi+1] if hi+1 < len(hdrs) else len(data)
        if (end-o)//4 == 66:
            return o, [u32(data, o+k*4) for k in range(66)]
    return None, None

def pof0_bytes(data):
    i = data.find(b'POF0')
    assert i != -1
    ln = u32(data, i+4)
    return data[i+8:i+8+ln]

def analyze_std(name, byts, idblock):
    """14B segmentation analysis."""
    segs = [byts[k*14:(k+1)*14] for k in range(len(byts)//14)]
    res = {'nseg': len(segs), 'segs': []}
    for k, seg in enumerate(segs):
        # marker bytes: >= 0x80
        markers = [(j, v) for j, v in enumerate(seg) if v >= 0x80]
        active = [v for v in seg if 0x40 <= v < 0x80]
        flat = [v for v in seg if v == 0x44]
        # linearity of active bytes in order
        acts = [(j, v) for j, v in enumerate(seg) if 0x40 <= v < 0x80]
        lin = None
        if len(acts) >= 3:
            xs = [j for j, _ in acts]; ys = [v for _, v in acts]
            n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
            den = sum((x-mx)**2 for x in xs)
            if den:
                slope = sum((x-mx)*(y-my) for x, y in zip(xs, ys))/den
                ss_res = sum((y-(my+slope*(x-mx)))**2 for x, y in zip(xs, ys))
                ss_tot = sum((y-my)**2 for y in ys)
                lin = {'slope': round(slope, 3),
                       'r2': round(1-ss_res/ss_tot, 3) if ss_tot else 1.0,
                       'n': n}
        res['segs'].append({'k': k, 'id': ('%08X' % idblock[k]) if (idblock and k < len(idblock)) else None,
                            'hex': seg.hex(),
                            'markers': [(j, '%02x' % v) for j, v in markers],
                            'n_active': len(active), 'n_flat': len(flat),
                            'linearity': lin})
    return res

def analyze_045(name, data, byts):
    res = {'len': len(byts), 'distinct': len(set(byts))}
    # marker map: positions of bytes >= 0x80
    markers = [(i, v) for i, v in enumerate(byts) if v >= 0x80]
    res['n_markers'] = len(markers)
    res['marker_positions'] = [i for i, _ in markers][:60]
    res['marker_values'] = sorted(set('%02x' % v for _, v in markers))
    # byte value histogram
    c = Counter(byts)
    res['top10'] = [(hex(v), n) for v, n in c.most_common(10)]
    # try segmentation: every 14B?
    n14 = len(byts)//14
    doms = []
    for k in range(n14):
        seg = byts[k*14:(k+1)*14]
        mc = Counter(seg).most_common(1)[0]
        doms.append((mc[0], mc[1]))
    res['seg14_dom'] = [(hex(v), n) for v, n in doms]
    # try every 12B? every 21B? (045 ID list ~13-18 words; 264/18=14.67, 264/12=22)
    for seglen in (14, 22, 12, 24, 11, 21):
        nseg = len(byts)//seglen
        mks = [sum(1 for v in byts[k*seglen:(k+1)*seglen] if v >= 0x80) for k in range(nseg)]
        res['seg%d_markers_per_seg' % seglen] = mks
    return res

ymgs = {}
for fn in ['model__wrestler__000_0.ymg', 'model__wrestler__002_0.ymg',
           'model__wrestler__016_0.ymg', 'model__wrestler__045_0.ymg']:
    p = os.path.join(SCR, fn)
    if os.path.exists(p):
        ymgs[fn] = open(p, 'rb').read()

for fn, data in ymgs.items():
    byts = pof0_bytes(data)
    o, w = record14(data)
    idblock = w[8:20] if (w and w[7] == 0x0C5BF279) else None
    if fn in ('model__wrestler__000_0.ymg', 'model__wrestler__002_0.ymg',
              'model__wrestler__016_0.ymg'):
        OUT[fn] = analyze_std(fn, byts, idblock)
        OUT[fn]['idblock'] = ['%08X' % x for x in idblock] if idblock else None
    else:
        OUT[fn] = analyze_045(fn, data, byts)
        # 045 ID list: words after 5D98B7F1 lead? dump record14 words
        if w:
            OUT[fn]['record14_words'] = ['%08X' % x for x in w[:24]]

print(json.dumps(OUT, indent=1))
