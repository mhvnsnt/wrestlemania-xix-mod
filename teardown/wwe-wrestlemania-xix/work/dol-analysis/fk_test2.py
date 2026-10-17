#!/usr/bin/env python3
"""FK + head batch render test (fixed batch parsing, 3D)."""
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

def euler_matrix(e, order='xyz'):
    cx, sx = math.cos(e[0]), math.sin(e[0])
    cy, sy = math.cos(e[1]), math.sin(e[1])
    cz, sz = math.cos(e[2]), math.sin(e[2])
    Rx = np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    Ry = np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    Rz = np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    if order == 'xyz': return Rx @ Ry @ Rz
    if order == 'zyx': return Rz @ Ry @ Rx
    if order == 'yxz': return Ry @ Rx @ Rz
    raise ValueError

def compute_world(order):
    world = [None]*NB
    def gw(i):
        if world[i] is not None: return world[i]
        p = parents[i]
        R = euler_matrix(eulers[i], order)
        M = np.eye(4); M[:3,:3] = R; M[:3,3] = np.array(poss[i])
        world[i] = M if (p == 0xFFFFFFFF or p >= NB) else gw(p) @ M
        return world[i]
    for i in range(NB): gw(i)
    return world

# batches: exactly 14 records (1 header + 13)
bt = 0x7ca0
batches = []
for r in range(14):
    o = bt + r*8
    idx, c1 = d[o], d[o+1]
    off = u32(o+4)
    if c1 == 0 and off == 0: continue
    base = 0x80 + off
    verts = [(i16(base+i*6)/64.0, i16(base+i*6+2)/64.0, i16(base+i*6+4)/64.0) for i in range(c1)]
    batches.append(dict(idx=idx, count=c1, verts=np.array(verts)))
print('batches:', [(b['idx'], b['count']) for b in batches])

# try euler orders, render head batches (file-order idx 7..12 = batches[7:13]) via Bip Head
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

for order in ['xyz', 'zyx', 'yxz']:
    world = compute_world(order)
    M = world[6]  # Bip Head
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')
    for b in batches[7:13]:
        pts = b['verts']
        homo = np.hstack([pts, np.ones((len(pts),1))])
        wpts = (M @ homo.T).T[:,:3]
        ax.scatter(wpts[:,0], wpts[:,1], wpts[:,2], s=2)
    # also plot bone positions
    bp = np.array([world[i][:3,3] for i in [2,3,4,5,6]])
    ax.scatter(bp[:,0], bp[:,1], bp[:,2], s=50, c='red')
    ax.set_title(f'order={order} head batches via Bip Head')
    plt.savefig(f'/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis/head_{order}.png', dpi=70)
    plt.close()
    print(f'saved head_{order}.png, head pos {world[6][:3,3]}')
