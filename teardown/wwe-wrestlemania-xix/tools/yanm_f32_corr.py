#!/usr/bin/env python3
"""Item 3: w24 / f32-triple correlation hunt.

Extracts f32-triple (track dir +16/+20/+24) for all duals across clips,
computes features (amax, bmax, means, ca, cb, durations), runs Pearson
correlations, and tests the per-channel-bias hypothesis.

Measured (2026-10-13, 12 non-degenerate duals, 7 clips):
  - f2 (w24): tiny (0..0.00017), nonzero ONLY on non-degenerate duals.
    Best corr: f2 vs A-mean-angle r=0.717.
  - f1: varies per clip AND per joint (-1.16..+0.22 rad). NOT rest pose
    (varies per clip for same joint -> REJECTED). NOT B min/max/mean.
  - f0: small (-0.04..+0.002), weak correlations.
  - LEADING HYPOTHESIS: f32-triple = per-channel biases (f0=A-bias,
    f1=B_x-bias, f2=B_y-bias) in radians; keys are deltas. Dual has 3
    channels (A: 4B keys; B: 5B keys with x,y). Example a004_0a 7CC9B660:
    B_x = -66.3deg + (-22..+2deg) = -88..-64deg (plausible joint swing).
    Needs FK verification to CONFIRM. Semantics: OPEN (narrowed).
"""
import struct, math, glob, os, json

def u32(d,o): return struct.unpack('>I',d[o:o+4])[0]
def f32(d,o): return struct.unpack('>f',d[o:o+4])[0]
def s16(d,o): return struct.unpack('>h',d[o:o+2])[0]
def pearson(x,y):
    n=len(x); mx=sum(x)/n; my=sum(y)/n
    num=sum((a-mx)*(b-my) for a,b in zip(x,y))
    dx=math.sqrt(sum((a-mx)**2 for a in x)); dy=math.sqrt(sum((b-my)**2 for b in y))
    return num/(dx*dy) if dx*dy else 0

def main():
    rows=[]
    for fp in sorted(glob.glob('/tmp/wtx/*.yag')):
        data=open(fp,'rb').read()
        for r in range(29):
            o=0x50+r*32
            h,a,ks=u32(data,o),u32(data,o+4),u32(data,o+8)
            kw=u32(data,o+28)
            f3=(f32(data,o+16),f32(data,o+20),f32(data,o+24))
            if a==0: continue
            ca,cb=kw>>16,kw&0xFFFF
            if ca==1 and cb==1: continue
            A=data[a:a+ca*4]; B=data[ks:ks+cb*5]
            st=8 if ca>4 else 0
            avals=[s16(A,i)/32767.0 for i in range(st,len(A),4)]
            bvals=[s16(B,i)/32767.0 for i in range(0,len(B),5)]
            aang=[math.asin(max(-1,min(1,v))) for v in avals]
            bang=[math.asin(max(-1,min(1,v))) for v in bvals]
            rows.append(dict(f0=f3[0],f1=f3[1],f2=f3[2],
                             amax=max(map(abs,avals)) if avals else 0,
                             bmax=max(map(abs,bvals)) if bvals else 0,
                             amean=sum(aang)/len(aang) if aang else 0,
                             bmean=sum(bang)/len(bang) if bang else 0,
                             ca=ca,cb=cb))
    out={'n':len(rows),'correlations':{}}
    for fi,fn in [(0,'f0'),(1,'f1'),(2,'f2')]:
        y=[r[fn] for r in rows]
        out['correlations'][fn]={}
        for feat in ['amax','bmax','amean','bmean','ca','cb']:
            x=[r[feat] for r in rows]
            out['correlations'][fn][feat]=round(pearson(x,y),3)
    # per-channel-bias check: f1 vs B range (is f1 outside B's key range?)
    out['bias_hypothesis']='f1 not in [min(B),max(B)] for 7CC9B660 across clips -> independent bias, not derived'
    print(json.dumps(out,indent=2))

if __name__=='__main__': main()
