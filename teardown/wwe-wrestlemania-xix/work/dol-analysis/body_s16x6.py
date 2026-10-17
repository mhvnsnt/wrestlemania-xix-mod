#!/usr/bin/env python3
"""Render batches as s16x6 (12B/vert), translation-only."""
import struct
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

P = '/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/.scratch/files/model__wrestler__000_0.ymg'
d = open(P,'rb').read()
def u32(o): return struct.unpack('>I', d[o:o+4])[0]
def f32(o): return struct.unpack('>f', d[o:o+4])[0]
def i16(o): return struct.unpack('>h', d[o:o+2])[0]

NB=71
names=[]; pars=[]; poss=[]
for i in range(NB):
    o=0xf3b4+i*64
    names.append(d[o+8:o+24].split(b'\x00')[0].decode('ascii','replace'))
    pars.append(u32(o+24)); poss.append(np.array([f32(o+28+j*4) for j in range(3)]))
acc=[None]*NB
def get(i):
    if acc[i] is not None: return acc[i]
    p=pars[i]
    acc[i]=poss[i] if (p==0xFFFFFFFF or p>=NB) else get(p)+poss[i]
    return acc[i]
for i in range(NB): get(i)

bt=0x7ca0
batches=[]
for r in range(1,14):
    o=bt+r*8
    idx,c1=d[o],d[o+1]; off=u32(o+4)
    base=0x80+off
    # 12 bytes/vert: pos.xyz (s16x3) + nrm.xyz (s16x3)
    verts=np.array([(i16(base+i*12)/64.0, i16(base+i*12+2)/64.0, i16(base+i*12+4)/64.0) for i in range(c1)])
    batches.append(dict(idx=idx, verts=verts))

bmap = {0:4, 1:20, 2:23, 3:2, 4:66, 5:68, 6:69, 7:6, 8:6, 9:6, 10:6, 11:6, 12:6}
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection='3d')
colors = plt.cm.tab10(np.linspace(0,1,13))
for bi, b in enumerate(batches):
    bone = bmap[bi]
    wpts = b['verts'] + acc[bone]
    ax.scatter(wpts[:,0], wpts[:,1], wpts[:,2], s=3, c=[colors[bi]])
ax.set_title('Full body s16x6, translation-only')
plt.savefig('/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis/body_s16x6.png', dpi=70)
print('saved body_s16x6.png')
# also print bbox of all
allpts = np.vstack([b['verts']+acc[bmap[bi]] for bi,b in enumerate(batches)])
print('overall bbox:', allpts.min(axis=0), allpts.max(axis=0))
