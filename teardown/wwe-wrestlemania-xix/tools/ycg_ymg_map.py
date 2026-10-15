#!/usr/bin/env python3
"""Task 3: ycg-group -> ymg-bone anatomical mapping.
Compute ymg 70-bone WORLD positions (proper euler composition) and
nearest-neighbor match each ycg record position, trying coordinate-frame
permutations. Streams ycg from ISO; reads docs/wrestler-skeleton-000.json."""
import json, math, sys
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
    return Rx @ Ry @ Rz  # XYZ order

world = {}
def wpos(i):
    if i in world: return world[i]
    b = skel[i]
    p = np.array(b['pos'], float)
    if b['parent'] < 0:
        world[i] = p
    else:
        pp, pr = wpos(b['parent']), wmat(b['parent'])
        world[i] = pp + pr @ p
    return world[i]

def wmat(i):
    b = skel[i]
    m = euler_mat(*b['euler_xyz'])
    if b['parent'] < 0: return m
    return wmat(b['parent']) @ m

for i in range(len(skel)):
    wpos(i)

print('ymg world positions (first 12 + a few):')
for i in [0,1,2,3,4,5,6,10,20,30,40,50,60,69]:
    b = skel[i]
    print(f'  {i:2d} {b["name"]:22s} parent={b["parent"]:2d} world=({world[i][0]:7.2f},{world[i][1]:7.2f},{world[i][2]:7.2f})')

ycg = ycg_parse('model/wrestler/000_0.ycg')
print(f'\nycg records: {len(ycg)}')
# try identity frame match first: for each ycg rec, nearest ymg world pos
yp = np.array([world[i] for i in range(len(skel))])
for r in ycg[:6]:
    p = np.array(r['pos'])
    d = np.linalg.norm(yp - p, axis=1)
    j = int(np.argmin(d))
    print(f'  ycg hash={r["hash"]:08X} pos=({p[0]:6.2f},{p[1]:6.2f},{p[2]:6.2f}) -> nearest ymg {j} {skel[j]["name"]} dist={d[j]:.2f}')
