#!/usr/bin/env python3
"""Item 2: A-stream first-8B header-vs-keys resolution via dt-sum test.

For each dual track, compute:
  D_H = dt-sum of keys from +8      (8B header interpretation, ca-2 keys)
  D_K = dt-sum of keys from 0       (2-keys interpretation, ca keys)
  D_B = dt-sum of B-stream (5B/key, dt at byte 2)
The correct interpretation minimizes |D_A - D_B|.

Measured (2026-10-13):
  a000_0a.yag 7CC9B660 (ca=248): D_H=494 ~= D_B=498 -> HEADER
  a000_0a.yag 64DB300F (ca=4):   D_K=497 ~= D_B=496 -> KEYS (no header)
  a.yag       7CC9B660 (ca=26):  2nd unit dt=0 -> HEADER (D matches neither;
                                 B=2394 authoritative or different sync)
  a.yag       64DB300F (ca=26):  2nd unit dt=0 -> HEADER
  ca=1 duals: bare 4B key, no header room (prior).

Structural rule (observed, needs more clips to confirm):
  header IFF ca > 4; ca <= 4 -> all ca units are keys.
"""
import struct, json, os

def u32(d,o): return struct.unpack('>I',d[o:o+4])[0]

def parse_tracks(data):
    ts=[]
    for r in range(29):
        o=0x50+r*32
        h,a,ks=u32(data,o),u32(data,o+4),u32(data,o+8)
        kw=u32(data,o+28)
        if a==0: ts.append(dict(h=h,kind='s',off=ks,n=kw))
        else: ts.append(dict(h=h,kind='d',a=a,b=ks,ca=kw>>16,cb=kw&0xFFFF))
    return ts

def dtsum_4B(raw,start=0):
    return sum(raw[i+3] for i in range(start,len(raw),4))

def dtsum_5B(raw):
    return sum(raw[i+2] for i in range(0,len(raw),5))

def main():
    out={}
    for fn in ['a.yag','a000_0a.yag']:
        fp=os.path.join('/tmp/wtx',fn)
        if not os.path.exists(fp): continue
        data=open(fp,'rb').read()
        ts=parse_tracks(data)
        res=[]
        for t in ts:
            if t['kind']!='d': continue
            A=data[t['a']:t['a']+t['ca']*4]
            B=data[t['b']:t['b']+t['cb']*5]
            dH=dtsum_4B(A,8) if t['ca']>=2 else 0
            dK=dtsum_4B(A,0)
            dB=dtsum_5B(B)
            # 2nd unit dt
            dt1=A[7] if len(A)>=8 else None
            if abs(dH-dB) < abs(dK-dB): verdict='HEADER'
            elif abs(dK-dB) < abs(dH-dB): verdict='KEYS'
            else: verdict='TIE'
            # ca=1: bare 4B key, no header room (definitive)
            if t['ca']==1: verdict='KEYS (ca=1 bare key)'
            # dt=0 is definitive for header
            elif dt1==0: verdict='HEADER (dt=0 definitive)'
            res.append(dict(hash=f'{t["h"]:08X}',ca=t['ca'],cb=t['cb'],
                            D_H=dH,D_K=dK,D_B=dB,dt1=dt1,verdict=verdict))
        out[fn]=res
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
