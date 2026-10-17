#!/usr/bin/env python3
"""Render YMG skeleton with different euler orders to find correct convention."""
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
NB=71
names=[]; pars=[]; poss=[]; euls=[]
for i in range(NB):
    o=0xf3b4+i*64
    names.append(d[o+8:o+24].split(b'\x00')[0].decode('ascii','replace'))
    pars.append(u32(o+24)); poss.append(np.array([f32(o+28+j*4) for j in range(3)])); euls.append([f32(o+40+j*4) for j in range(3)])

def emat(e, order):
    cx,sx=math.cos(e[0]),math.sin(e[0]); cy,sy=math.cos(e[1]),math.sin(e[1]); cz,sz=math.cos(e[2]),math.sin(e[2])
    Rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]); Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]); Rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return {'xyz':Rx@Ry@Rz,'zyx':Rz@Ry@Rx,'yxz':Ry@Rx@Rz,'xzy':Rx@Rz@Ry,'zxy':Rz@Rx@Ry,'yzx':Ry@Rz@Rx}[order]

fig, axes = plt.subplots(2, 3, figsize=(18,12), subplot_kw={'projection':'3d'})
orders = ['xyz','zyx','yxz','xzy','zxy','yzx']
for ax, order in zip(axes.flat, orders):
    world=[None]*NB
    def gw(i):
        if world[i] is not None: return world[i]
        p=pars[i]; R=emat(euls[i],order)
        M=np.eye(4); M[:3,:3]=R; M[:3,3]=poss[i]
        world[i]=M if (p==0xFFFFFFFF or p>=NB) else gw(p)@M
        return world[i]
    for i in range(NB): gw(i)
    pts=np.array([world[i][:3,3] for i in range(NB)])
    ax.scatter(pts[:,0], pts[:,1], pts[:,2], s=10)
    # draw bones as lines
    for i in range(NB):
        p=pars[i]
        if p!=0xFFFFFFFF and p<NB:
            ax.plot([world[p][0,3],world[i][0,3]],[world[p][1,3],world[i][1,3]],[world[p][2,3],world[i][2,3]],'b-',lw=0.5)
    ax.set_title(order)
plt.savefig('/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis/skeleton_orders.png', dpi=70)
print('saved')
