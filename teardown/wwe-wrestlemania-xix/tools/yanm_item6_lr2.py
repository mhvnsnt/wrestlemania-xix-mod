#!/usr/bin/env python3
"""YANM item-6: DEFINITIVE anatomical L/R test.
ycg record pos ~= ymg bone LOCAL pos (mean 2.5) => nearest-neighbor
correspondence; then ycg-y-sign vs ymg bone-name side gives the
side-bit -> anatomical mapping with NO frame-alignment assumption."""
import json, sys
from collections import Counter
import numpy as np
sys.path.insert(0, 'tools')
from ycg_parse import parse

skel = json.load(open('docs/wrestler-skeleton-000.json'))
ycg = parse('model/wrestler/000_0.ycg')
yl = np.array([b['pos'] for b in skel])

def side_of(name):
    n = ' ' + name + ' '
    if ' L ' in n: return 'L'
    if ' R ' in n: return 'R'
    return 'C'

agree = Counter(); rows = []
for r in ycg:
    p = np.array(r['pos'])
    d = np.linalg.norm(yl - p, axis=1)
    j = int(np.argmin(d))
    nm = skel[j]['name']; s = side_of(nm)
    ysign = 'neg' if p[1] < -0.05 else ('pos' if p[1] > 0.05 else 'zero')
    exp = {'L': 'neg', 'R': 'pos'}.get(s)
    ok = (exp == ysign) if exp and ysign != 'zero' else None
    agree[ok] += 1
    rows.append((r['hash'], nm, s, ysign, round(float(d[j]), 2), ok))

print('side agreement (ycg-y-sign vs ymg-name-side):', dict(agree))
print('\nall 42 records:')
for h, nm, s, ys, dd, ok in rows:
    print('  hash=%08X ycg_y=%-4s -> ymg=%-26s side=%s dist=%5.2f agree=%s' % (h, ys, nm, s, dd, ok))
print('done')
