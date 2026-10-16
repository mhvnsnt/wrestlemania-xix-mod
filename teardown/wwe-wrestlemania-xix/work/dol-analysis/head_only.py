#!/usr/bin/env python3
import struct, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
P='/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/.scratch/files/model__wrestler__000_0.ymg'
d=open(P,'rb').read()
def u32(o): return struct.unpack('>I',d[o:o+4])[0]
def f32(o): return struct.unpack('>f',d[o:o+4])[0]
def i16(o): return struct.unpack('>h',d[o:o+2])[0]
NB=71
pars=[]; poss=[]; euls=[]
for i in range(NB):
    o=0xf3b4+i*64
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
M=world[6]
bt=0x7ca0
fig=plt.figure(figsize=(10,8))
ax=fig.add_subplot(111,projection='3d')
for r in range(1,14):
    o=bt+r*8
    idx=d[o]
    if idx in (7,8,9,10,11,12):
        c1=d[o+1]; off=u32(o+4); base=0x80+off
        verts=np.array([(i16(base+i*12)/64.0, i16(base+i*12+2)/64.0, i16(base+i*12+4)/64.0) for i in range(c1)])
        homo=np.hstack([verts,np.ones((len(verts),1))])
        wpts=(M@homo.T).T[:,:3]
        ax.scatter(wpts[:,0],wpts[:,1],wpts[:,2],s=12,label=f'idx{idx}')
ax.legend(fontsize=8)
ax.set_title('Head batches via Bip Head')
plt.savefig('/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis/head_only.png', dpi=80)
print('done')
