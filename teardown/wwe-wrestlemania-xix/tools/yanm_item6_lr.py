#!/usr/bin/env python3
"""YANM item-6: anatomical L/R via ycg<->ymg frame alignment.
Test: nearest-neighbor match each ycg bind position to ymg bone WORLD
positions; check whether ycg-y-sign agrees with ymg bone-name side (L/R).
If frames align: 0x04000000-bit (ycg y<0) <-> ymg 'L' bones => A4955E6E=LEFT.
Streams ISO for ycg; ymg skeleton from docs/wrestler-skeleton-000.json."""
import json, math, sys
from collections import Counter
import numpy as np
sys.path.insert(0, 'tools')
from ycg_parse import parse as ycg_parse

skel = json.load(open('docs/wrestler-skeleton-000.json'))

def euler_mat(ex, ey, ez):
    cx, sx = math.cos(ex), math.sin(ex)
    cy, sy = math.cos(ey), math.sin(ey)
    cz, sz = math.cos(ez), math.sin(ez)
    Rx = np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    Ry = np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    Rz = np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return Rx @ Ry @ Rz

world, wmat_c = {}, {}
def wmat(i):
    if i in wmat_c: return wmat_c[i]
    b = skel[i]
    m = euler_mat(*b['euler_xyz'])
    wmat_c[i] = m if b['parent'] < 0 else wmat(b['parent']) @ m
    return wmat_c[i]
def wpos(i):
    if i in world: return world[i]
    b = skel[i]
    p = np.array(b['pos'], float)
    world[i] = p if b['parent'] < 0 else wpos(b['parent']) + wmat(b['parent']) @ p
    return world[i]
for i in range(len(skel)):
    wpos(i)

def side_of(name):
    n = ' ' + name + ' '
    if ' L ' in n: return 'L'
    if ' R ' in n: return 'R'
    return 'C'

# ymg side check: world y-sign of L vs R bones
ly = [world[i][1] for i in range(len(skel)) if side_of(skel[i]['name']) == 'L']
ry = [world[i][1] for i in range(len(skel)) if side_of(skel[i]['name']) == 'R']
print('ymg L bones: n=%d y<0: %d/%d' % (len(ly), sum(1 for y in ly if y < 0), len(ly)))
print('ymg R bones: n=%d y>0: %d/%d' % (len(ry), sum(1 for y in ry if y > 0), len(ry)))

ycg = ycg_parse('model/wrestler/000_0.ycg')
print('ycg records:', len(ycg))
yp = np.array([world[i] for i in range(len(skel))])

agree = 0; total = 0; rows = []
for r in ycg:
    p = np.array(r['pos'])
    d = np.linalg.norm(yp - p, axis=1)
    j = int(np.argmin(d))
    nm = skel[j]['name']; s = side_of(nm)
    ysign = 'neg' if p[1] < 0 else 'pos'
    expect = {'L': 'neg', 'R': 'pos'}.get(s)
    ok = (expect == ysign) if expect else None
    if ok is not None:
        total += 1; agree += int(ok)
    rows.append((r['hash'], nm, s, ysign, round(float(d[j]), 2), ok))

print(f'\nnearest-neighbor side agreement: {agree}/{total}')
print('mean nearest distance: %.2f' % np.mean([x[4] for x in rows]))
print('\nworst 12 matches:')
for x in sorted(rows, key=lambda t: -t[4])[:12]:
    print('  hash=%08X ymg=%-24s side=%s ycg_y=%s dist=%.2f agree=%s' % x)
print('\ndisagreements:')
nd = [x for x in rows if x[5] is False]
print(' ', len(nd))
for x in nd[:12]:
    print('  hash=%08X ymg=%-24s side=%s ycg_y=%s dist=%.2f' % x[:5])

# finger/thumb/toe side-bit mapping recap
print('\nside-bit recap (0x04000000 set => ycg y<0, proven 6/6):')
for name, hh in [('A4955E6E finger', 0xA4955E6E), ('BA955E6E finger', 0xBA955E6E),
                 ('579B8E50 thumb', 0x579B8E50), ('579B89D0 thumb', 0x579B89D0),
                 ('007FD58C toe', 0x007FD58C), ('1E7FD58C toe', 0x1E7FD58C)]:
    print(f'  {name}: bit04000000={"SET" if hh & 0x04000000 else "clear"}')
print('done')
