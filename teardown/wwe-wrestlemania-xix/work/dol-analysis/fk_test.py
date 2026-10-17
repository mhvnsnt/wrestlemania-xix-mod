#!/usr/bin/env python3
"""FK world matrices from YMG skeleton + batch->bone render test."""
import struct, math
import numpy as np

P = '/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/.scratch/files/model__wrestler__000_0.ymg'
d = open(P,'rb').read()
def u32(o): return struct.unpack('>I', d[o:o+4])[0]
def f32(o): return struct.unpack('>f', d[o:o+4])[0]
def i16(o): return struct.unpack('>h', d[o:o+2])[0]

NB = 71
names, parents, poss, eulers = [], [], [], []
for i in range(NB):
    o = 0xf3b4 + i*64
    names.append(d[o+8:o+24].split(b'\x00')[0].decode('ascii','replace'))
    parents.append(u32(o+24))
    poss.append([f32(o+28+j*4) for j in range(3)])
    eulers.append([f32(o+40+j*4) for j in range(3)])

def euler_xyz_matrix(e):
    # R = Rx @ Ry @ Rz
    cx, sx = math.cos(e[0]), math.sin(e[0])
    cy, sy = math.cos(e[1]), math.sin(e[1])
    cz, sz = math.cos(e[2]), math.sin(e[2])
    Rx = np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    Ry = np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    Rz = np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return Rx @ Ry @ Rz

world = [None]*NB
def get_world(i):
    if world[i] is not None: return world[i]
    p = parents[i]
    R = euler_xyz_matrix(eulers[i])
    t = np.array(poss[i])
    M = np.eye(4); M[:3,:3] = R; M[:3,3] = t
    if p == 0xFFFFFFFF or p >= NB:
        world[i] = M
    else:
        world[i] = get_world(p) @ M
    return world[i]

for i in range(NB):
    get_world(i)

# Bip Head = bone 6
print('Bip Head world pos:', world[6][:3,3])
print('Bip Pelvis world pos:', world[2][:3,3])

# batches: parse
bt = 0x7ca0
batches = []
o = bt + 8  # skip header record
while True:
    c1 = d[o+1]; off = struct.unpack('>I', d[o+4:o+8])[0]
    idx = d[o]
    if c1 == 0 and off == 0: break
    base = 0x80 + off
    verts = [(i16(base+i*6)/64.0, i16(base+i*6+2)/64.0, i16(base+i*6+4)/64.0) for i in range(c1)]
    batches.append(dict(idx=idx, count=c1, verts=verts))
    o += 8
    if len(batches) > 20: break
print('batches:', [(b['idx'], b['count']) for b in batches])

# head batches: file order 8-13 (face, head_back, eye, head_top, tooth, mouth)
# transform by Bip Head world matrix
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 2, figsize=(12, 6))
M = world[6]
for ax, (elev, azim) in zip(axes, [(10, -60), (10, 60)]):
    for b in batches[7:13]:  # batches 8-13 (0-based 7:13)
        pts = np.array(b['verts'])
        homo = np.hstack([pts, np.ones((len(pts),1))])
        wpts = (M @ homo.T).T[:,:3]
        ax.scatter(wpts[:,0], wpts[:,1], s=1)
    ax.set_aspect('equal'); ax.set_title(f'head batches via Bip Head (el{elev} az{azim})')
    ax.view_init = None
plt.savefig('/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis/head_test.png', dpi=80)
print('saved head_test.png')
