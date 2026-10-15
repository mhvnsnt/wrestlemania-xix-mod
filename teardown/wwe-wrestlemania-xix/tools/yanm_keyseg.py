#!/usr/bin/env python3
"""Score candidate 5B/4B key segmentations by curve smoothness.
Correct absolute-value layout => small frame-to-frame deltas."""
import sys, struct
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32

data, size = stream_file('ringmotion/a000_0a.yag')

def keys5(off, n):
    return data[off:off + n * 5]

def s16(b): return struct.unpack('>h', b)[0]
def u8(b): return b[0]

def smoothness(vals):
    return sum(abs(b - a) for a, b in zip(vals, vals[1:])) / max(1, len(vals) - 1)

def test5(off, n, name):
    raw = keys5(off, n)
    cands = {}
    # (s16 x, u8 dt, s16 y)
    xs = [s16(raw[i:i+2]) for i in range(0, len(raw), 5)]
    dts = [u8(raw[i+2:i+3]) for i in range(0, len(raw), 5)]
    ys = [s16(raw[i+3:i+5]) for i in range(0, len(raw), 5)]
    cands['x=u16,dt=u8,y=s16'] = (smoothness(xs), smoothness(ys), sum(dts)/len(dts))
    # (u8 dt, s16 x, s16 y)
    dts2 = [u8(raw[i:i+1]) for i in range(0, len(raw), 5)]
    xs2 = [s16(raw[i+1:i+3]) for i in range(0, len(raw), 5)]
    ys2 = [s16(raw[i+3:i+5]) for i in range(0, len(raw), 5)]
    cands['dt=u8,x=s16,y=s16'] = (smoothness(xs2), smoothness(ys2), sum(dts2)/len(dts2))
    # (s16 x, s16 y, u8 dt)
    xs3 = [s16(raw[i:i+2]) for i in range(0, len(raw), 5)]
    ys3 = [s16(raw[i+2:i+4]) for i in range(0, len(raw), 5)]
    dts3 = [u8(raw[i+4:i+5]) for i in range(0, len(raw), 5)]
    cands['x=s16,y=s16,dt=u8'] = (smoothness(xs3), smoothness(ys3), sum(dts3)/len(dts3))
    print(f'--- {name} off=0x{off:X} n={n}')
    for k, (sx, sy, mdt) in cands.items():
        print(f'  {k:22s} smooth_x={sx:9.1f} smooth_y={sy:9.1f} mean_dt={mdt:.2f}')

def test4(off, n, name):
    raw = data[off:off + n * 4]
    xs = [s16(raw[i:i+2]) for i in range(0, len(raw), 4)]
    ys = [s16(raw[i+2:i+4]) for i in range(0, len(raw), 4)]
    print(f'--- {name} off=0x{off:X} n={n} (s16,s16): smooth_x={smoothness(xs):.1f} smooth_y={smoothness(ys):.1f}')
    print(f'    first 8 pairs: {list(zip(xs,ys))[:8]}')

if __name__ == '__main__':
    test5(0xCC8, 84, 'track 347D3654 (single)')
    test5(0x124C, 158, 'track 7CC9B660-B (dual B)')
    test5(0x1574, 131, 'track 64DB300F-B (dual B)')
    test4(0xE6C, 248, 'track 7CC9B660-A (dual A)')
    test4(0x1564, 4, 'track 64DB300F-A (dual A)')
