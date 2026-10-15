#!/usr/bin/env python3
"""FK the ycg anim rig chains. Hinge about local X (maps to world lateral Y)."""
import struct, sys
import numpy as np
sys.path.insert(0, '/home/hatch/workspace/game-reverse-engineering/wwe-wrestlemania-xix/tools')
from yukes_fmt import stream_file, u32, f32

def s16(b): return struct.unpack('>h', b)[0]

def quat_to_mat(q):
    x,y,z,w = q
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])

def Rx(a):
    c,s=np.cos(a),np.sin(a)
    return np.array([[1,0,0],[0,c,-s],[0,s,c]])

class YcgRig:
    def __init__(self, path='model/wrestler/000_0.ycg'):
        import os
        os.chdir('/home/hatch/workspace/game-reverse-engineering/wwe-wrestlemania-xix')
        data,_=stream_file(path)
        n=u32(data,0)
        self.recs={}
        for r in range(n):
            o=4+r*56
            h=u32(data,o)
            self.recs.setdefault(h,[]).append({
                'idx':r,'w0':u32(data,o+4),
                'pos':np.array([f32(data,o+16),f32(data,o+20),f32(data,o+24)]),
                'quat':tuple(f32(data,o+28+k*4) for k in range(4))})
        # order each chain proximal->distal (by distance from pelvis-ish origin)
        # leg: hip near (12.6), ankle at (46.15); arm: shoulder near (15.6), wrist at (41.6)
    def chain(self, h):
        recs=sorted(self.recs[h], key=lambda r: r['pos'][0])
        # for BD (leg): hip x=12.6 < ankle x=46 -> ascending x = proximal->distal ✓
        # for 6198 (arm): shoulder x=15.6 < wrist x=41.6 -> ascending x ✓
        return recs

    def fk_chain(self, h, angles):
        """angles: list of hinge radians, one per record except last (tip). Returns joint world positions."""
        ch=self.chain(h)
        # root of chain: first record's bind pos; orientation from bind quat
        pts=[ch[0]['pos'].copy()]
        R=quat_to_mat(ch[0]['quat'])
        for i,ang in enumerate(angles):
            R=R @ Rx(ang)  # hinge about local X
            seg=ch[i+1]['pos']-ch[i]['pos']
            # segment in parent bind frame -> rotate by current R (approx: use bind segment rotated by accumulated hinge)
            # Better: express seg in local frame of joint i, then apply
            # Local frame of joint i: R_bind_i; seg_local = R_bind_i.T @ seg
            Rb=quat_to_mat(ch[i]['quat'])
            seg_local=Rb.T @ seg
            pts.append(pts[-1]+R @ seg_local)
        return pts

if __name__=='__main__':
    rig=YcgRig()
    for h in [0xBD5B2A59,0xBD5B5259,0x6198F425,0x6198F4D5]:
        ch=rig.chain(h)
        print(f'{h:08X}:')
        for r in ch:
            print(f'   pos=({r["pos"][0]:6.2f},{r["pos"][1]:6.2f},{r["pos"][2]:6.2f})')
    # bind FK sanity (zero angles)
    pts=rig.fk_chain(0xBD5B5259,[0.0,0.0])
    print('BD5B5259 bind FK:', [np.round(p,2).tolist() for p in pts])
