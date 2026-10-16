#!/usr/bin/env python3
"""Build bone matrices from YCG pos+quat, YMG hierarchy. Render batches."""
import struct, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def rol7(h): return ((h<<7)|(h>>25))&0xFFFFFFFF
def nhash(n):
    h=0
    for ch in n.encode('ascii'): h=rol7(h)^ch
    return h

P='/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/.scratch/files/model__wrestler__000_0.ymg'
d=open(P,'rb').read()
def u32(o,b=d): return struct.unpack('>I',b[o:o+4])[0]
def f32(o,b=d): return struct.unpack('>f',b[o:o+4])[0]
def i16(o): return struct.unpack('>h',d[o:o+2])[0]
Q='/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/.scratch/files/model__wrestler__000_0.ycg'
e=open(Q,'rb').read()
def e_u32(o): return struct.unpack('>I',e[o:o+4])[0]
def e_f32(o): return struct.unpack('>f',e[o:o+4])[0]

# YCG: map hash -> (pos, quat) from FIRST record
ycg={}
for j in range(42):
    o=4+j*56; h=e_u32(o)
    if h not in ycg:
        pos=[e_f32(o+16+k*4) for k in range(3)]
        quat=[e_f32(o+16+3+k*4) for k in range(4)]
        ycg[h]=(pos,quat)

NB=71
names=[]; pars=[]
for i in range(NB):
    o=0xf3b4+i*64
    names.append(d[o+8:o+24].split(b'\x00')[0].decode('ascii','replace'))
    pars.append(u32(o+24))

def quat_mat(q):
    # q = [x,y,z,w] or [w,x,y,z]? try both
    # YCG quat e.g. (0.5,-0.5,0.5,-0.5) - assume (x,y,z,w)
    x,y,z,w=q
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])

world=[None]*NB
def gw(i):
    if world[i] is not None: return world[i]
    h=nhash(names[i])
    if h in ycg:
        pos,quat=ycg[h]
        R=quat_mat(quat)
    else:
        # fallback: use YMG pos, identity rot
        o=0xf3b4+i*64
        pos=[f32(o+28+k*4) for k in range(3)]
        R=np.eye(3)
    M=np.eye(4); M[:3,:3]=R; M[:3,3]=pos
    p=pars[i]
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
    batches.append(dict(idx=idx,verts=verts))
bmap={0:4,1:20,2:23,3:2,4:66,5:68,6:69,7:6,8:6,9:6,10:6,11:6,12:6}
fig=plt.figure(figsize=(12,10))
ax=fig.add_subplot(111,projection='3d')
colors=plt.cm.tab10(np.linspace(0,1,13))
for bi,b in enumerate(batches):
    M=world[bmap[bi]]
    homo=np.hstack([b['verts'],np.ones((len(b['verts']),1))])
    wpts=(M@homo.T).T[:,:3]
    ax.scatter(wpts[:,0],wpts[:,1],wpts[:,2],s=4,c=[colors[bi]])
ax.set_title('Batches via YCG quat matrices')
plt.savefig('/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis/body_ycg.png', dpi=70)
print('saved')
