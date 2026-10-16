#!/usr/bin/env python3
"""Render batches with full zyx bone matrices."""
import struct, math
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
names=[]; pars=[]; poss=[]; euls=[]
for i in range(NB):
    o=0xf3b4+i*64
    names.append(d[o+8:o+24].split(b'\x00')[0].decode('ascii','replace'))
    pars.append(u32(o+24)); poss.append(np.array([f32(o+28+j*4) for j in range(3)])); euls.append([f32(o+40+j*4) for j in range(3)])
def emat(e):
    cx,sx=math.cos(e[0]),math.sin(e[0]); cy,sy=math.cos(e[1]),math.sin(e[1]); cz,sz=math.cos(e[2]),math.sin(e[2])
    Rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]); Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]); Rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return Rz@Ry@Rx
world=[None]*NB
def gw(i):
    if world[i] is not None: return world[i]
    p=pars[i]; R=emat(euls[i])
    M=np.eye(4); M[:3,:3]=R; M[:3,3]=poss[i]
    world[i]=M if (p==0xFFFFFFFF or p>=NB) else gw(p)@M
    return world[i]
for i in range(NB): gw(i)

bt=0x7ca0
batches=[]
for r in range(1,14):
    o=bt+r*8
    idx,c1=d[o],d[o+1]; off=u32(o+4)
    base=0x80+off
    verts=np.array([(i16(base+i*12)/64.0, i16(base+i*12+2)/64.0, i16(base+i*12+4)/64.0) for i in range(c1)])
    batches.append(dict(idx=idx, verts=verts))

# batch->bone hypothesis
bmap = {0:4, 1:20, 2:23, 3:2, 4:66, 5:68, 6:69, 7:6, 8:6, 9:6, 10:6, 11:6, 12:6}
fig=plt.figure(figsize=(12,10))
ax=fig.add_subplot(111,projection='3d')
colors=plt.cm.tab10(np.linspace(0,1,13))
for bi,b in enumerate(batches):
    M=world[bmap[bi]]
    homo=np.hstack([b['verts'], np.ones((len(b['verts']),1))])
    wpts=(M@homo.T).T[:,:3]
    ax.scatter(wpts[:,0],wpts[:,1],wpts[:,2],s=4,c=[colors[bi]])
ax.set_title('Batches via zyx bone matrices')
plt.savefig('/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis/body_zyx.png', dpi=70)
print('saved body_zyx.png')
