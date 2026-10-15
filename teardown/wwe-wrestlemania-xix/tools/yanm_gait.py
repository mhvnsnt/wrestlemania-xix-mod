#!/usr/bin/env python3
"""Task-3 support: decode hinge-angle series per YANM track (21 ycg groups)
from an entrance clip, print per-group motion stats to identify limbs by gait.
5B key = (s16 sin-hinge, u8 dt, s16 sin-hinge); hinge = asin(s16/32767).
Dual tracks: B channel used (same dt-sum as A). Streams from ISO."""
import struct, sys, math
import numpy as np
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32

def s16(b): return struct.unpack('>h', b)[0]

YAG = sys.argv[1] if len(sys.argv) > 1 else 'ringmotion/a000_0a.yag'
data, _ = stream_file(YAG)

tracks = []
for r in range(29):
    o = 0x50 + r * 32
    h, a, ks = u32(data, o), u32(data, o+4), u32(data, o+8)
    kw = u32(data, o+28)
    if a == 0:
        tracks.append(dict(hash=h, kind='s', n=kw, b=ks))
    else:
        tracks.append(dict(hash=h, kind='d', cb=kw & 0xFFFF, b=ks))

known = {}
for t in tracks:
    n = t['n'] if t['kind'] == 's' else t['cb']
    raw = data[t['b']:t['b'] + n * 5]
    xs = np.array([s16(raw[i:i+2]) for i in range(0, len(raw), 5)], float) / 32767.0
    xs = np.clip(xs, -1, 1)
    ang = np.degrees(np.arcsin(xs))
    known[t['hash']] = ang

print(f'{YAG}: decoded {len(known)} tracks')
print(f'{"hash":10s} {"n":>4s} {"mean":>7s} {"std":>7s} {"range":>7s} {"min":>7s} {"max":>7s}')
for h in sorted(known):
    a = known[h]
    print(f'{h:08X}   {len(a):4d} {a.mean():7.2f} {a.std():7.2f} {a.max()-a.min():7.2f} {a.min():7.2f} {a.max():7.2f}')
