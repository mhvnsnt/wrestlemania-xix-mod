#!/usr/bin/env python3
"""YOBJ v3 vertex/index probe - documents 2026-10-12 findings.
Streams from ISO (disk-safe). Key results:
- batch table @0x7CA0: 14 recs x 8B (rec0=null sentinel): u8 bone,u8 vcount,u8 0,u8 vcount,u32 vert_off(rel 0x80)
  -> per-batch VERTEX runs (s16x3 positions, 6B/vert), NOT index triplets.
- index buffers are separate u16 runs (elbow part: 150-tri u16 list @0x4C8, max idx 1224).
- material records are 20B: [rgba x3][u32 0][u16 1][u16 idx_off rel 0x7CA0].
- vertex POSITION array for full models still OPEN (index max exceeds s16x3 candidates).
Usage: python3 tools/yobj_v3_probe.py [batch|elbow|render]"""
import struct, sys
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32
def u16(b,i): return struct.unpack('>H',b[i:i+2])[0]
def s16(b,i): return struct.unpack('>h',b[i:i+2])[0]

def batch_table(data):
    recs=[]
    for r in range(14):
        o=0x7CA0+r*8
        recs.append((data[o],data[o+1],data[o+3],u32(data,o+4)))
    return recs

def cmd_batch():
    data,_=stream_file('model/wrestler/000_0.ymg')
    tot=0
    for b,c1,c2,off in batch_table(data):
        if c1==0: continue
        tot+=c1
        print('bone=%2d verts=%3d file_off=0x%05X-0x%05X'%(b,c1,0x80+off,0x80+off+c1*6))
    print('total verts:',tot)

def cmd_elbow():
    data,size=stream_file('edit_data/MODEL/Man/Elbow/me0_000/l0.ymg')
    idx=[u16(data,0x4C8+i*2) for i in range(450)]
    print('elbow index 0x4C8-0x84C: n=450 max=%d'%(max(idx)))
    print('as triangles (first 6):',[tuple(idx[t*3+k] for k in range(3)) for t in range(6)])

if __name__=='__main__':
    {'batch':cmd_batch,'elbow':cmd_elbow}[sys.argv[1]]()
