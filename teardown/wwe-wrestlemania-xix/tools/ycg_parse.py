#!/usr/bin/env python3
"""Parse .ycg 42-joint files: u32 count + 42 x 56B records.
Record: [u32 hash][u32 5][u32 0][u32 0][f32 x][f32 y][f32 z][f32 quat x4][f32 w][u32 0][u32 0]
Status 2026-10-12: positions near .ymg bones but quats match no convention;
likely the 42-joint ANIMATION rig (vs 70-bone render rig)."""
import struct, sys
sys.path.insert(0,'tools')
from yukes_fmt import stream_file, u32, f32
def parse(path):
    data,_=stream_file(path)
    n=u32(data,0); recs=[]
    for r in range(n):
        o=4+r*56
        recs.append({'hash':u32(data,o),'pos':(f32(data,o+16),f32(data,o+20),f32(data,o+24)),
                     'quat':tuple(f32(data,o+28+k*4) for k in range(4)),'w':f32(data,o+44)})
    return recs
if __name__=='__main__':
    recs=parse(sys.argv[1] if len(sys.argv)>1 else 'model/wrestler/000_0.ycg')
    print('joints:',len(recs))
    for i,r in enumerate(recs[:5]):
        print(i,'hash=%08X pos=(%.2f,%.2f,%.2f) quat=(%.3f,%.3f,%.3f,%.3f)'%(r['hash'],*r['pos'],*r['quat']))
