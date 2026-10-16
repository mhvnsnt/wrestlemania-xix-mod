#!/usr/bin/env python3
"""Render batches with TRANSLATION-ONLY bone matrices (no rotation)."""
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
    verts=np.array([(i16(base+i*6)/64.0, i16(base+i*6+2)/64.0, i16(base+i*6+4)/64.0) for i in range(c1)])
    batches.append(dict(idx=idx, verts=verts))

# body-part -> YMG bone index (my hypothesis)
# batch file-order: 0:body,1:arm,2:hand,3:waists,4:l_leg,5:knee,6:foot,7:face,8:head_back,9:eye,10:head_top,11:tooth,12:mouth
bmap = {
    0: 4,   # body -> Bip Spine1
    1: 20,  # arm -> Bip R UpperArm (guess R)
    2: 23,  # hand -> Bip R Hand
    3: 2,   # waists -> Bip Pelvis
    4: 66,  # l_leg -> Bip L Thigh
    5: 68,  # knee -> Bip L Calf
    6: 69,  # foot -> Bip L Foot
    7: 6, 8: 6, 9: 6, 10: 6, 11: 6, 12: 6,  # head parts -> Bip Head
}
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection='3d')
colors = plt.cm.tab10(np.linspace(0,1,13))
for bi, b in enumerate(batches):
    bone = bmap[bi]
    wpts = b['verts'] + acc[bone]
    ax.scatter(wpts[:,0], wpts[:,1], wpts[:,2], s=3, c=[colors[bi]], label=f"b{bi}->{names[bone]}")
ax.set_title('Full body, translation-only, hypothesized batch->bone')
plt.savefig('/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-analysis/body_transonly.png', dpi=70)
print('saved body_transonly.png')
