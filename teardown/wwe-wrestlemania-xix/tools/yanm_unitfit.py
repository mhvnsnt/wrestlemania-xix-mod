#!/usr/bin/env python3
"""Fit YANM single-track key channels against .ycg rest quats to find the
angle unit and channel->rotation mapping. Metric: angular distance (degrees)
between candidate rotation-from-keys and ycg rest quat, median over tracks.
Streams from ISO; reads ycg via tools/ycg_parse."""
import struct, sys, math
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32, f32
from ycg_parse import parse as ycg_parse

data, size = stream_file('ringmotion/a000_0a.yag')
def s16(b): return struct.unpack('>h', b)[0]

# ycg: hash -> list of (pos, quat); use FIRST record's quat as rest
ycg = ycg_parse('model/wrestler/000_0.ycg')
rest = {}
for r in ycg:
    rest.setdefault(r['hash'], []).append(r['quat'])
print(f'ycg: {len(ycg)} records, {len(rest)} unique hashes')

# yag single tracks: hash -> (first_key_xy, mean_xy, n)
trk = {}
for r in range(29):
    o = 0x50 + r * 32
    h, a, ks, kw = u32(data, o), u32(data, o+4), u32(data, o+8), u32(data, o+28)
    if a != 0: continue
    n = kw
    xs = [s16(data[ks+i*5:ks+i*5+2]) for i in range(n)]
    ys = [s16(data[ks+i*5+3:ks+i*5+5]) for i in range(n)]
    trk[h] = dict(first=(xs[0], ys[0]),
                  mean=(sum(xs)/n, sum(ys)/n), n=n)

matched = [h for h in trk if h in rest]
print(f'matched single tracks: {len(matched)} of {len(trk)}')

def quat_mul(a, b):
    x1,y1,z1,w1 = a; x2,y2,z2,w2 = b
    return (w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2,
            w1*z2+x1*y2-y1*x2+z1*w2, w1*w2-x1*x2-y1*y2-z1*z2)

def euler_xyz(ex, ey, ez):
    cx, sx = math.cos(ex/2), math.sin(ex/2)
    cy, sy = math.cos(ey/2), math.sin(ey/2)
    cz, sz = math.cos(ez/2), math.sin(ez/2)
    qx = (sx, 0, 0, cx); qy = (0, sy, 0, cy); qz = (0, 0, sz, cz)
    return quat_mul(qx, quat_mul(qy, qz))

def ang_dist(a, b):
    d = abs(sum(p*q for p, q in zip(a, b)))
    d = min(1.0, d)
    return 2*math.degrees(math.acos(d))

units = {
    'deg180': lambda v: math.radians(v*180.0/32767),
    'rad_pi': lambda v: v*math.pi/32767,
    'decideg': lambda v: math.radians(v/10.0),
    'centideg': lambda v: math.radians(v/100.0),
    'deg360': lambda v: math.radians(v*360.0/65536),
}
placements = {
    '(x,y,0)': lambda x, y: (x, y, 0.0),
    '(x,0,y)': lambda x, y: (x, 0.0, y),
    '(0,x,y)': lambda x, y: (0.0, x, y),
    '(y,x,0)': lambda x, y: (y, x, 0.0),
}
keysrc = {
    'first': lambda t: t['first'],
    'mean': lambda t: t['mean'],
}

print('\nmedian angular distance (deg) key-euler vs ycg rest quat:')
print(f'{"unit":10s} {"place":9s} {"key":6s} {"median":>8s} {"p25":>7s} {"p75":>7s} n')
for uname, u in units.items():
    for pname, p in placements.items():
        for kname, ks in keysrc.items():
            ds = []
            for h in matched:
                x, y = ks(trk[h])
                ex, ey, ez = p(u(x), u(y))
                q = euler_xyz(ex, ey, ez)
                ds.append(ang_dist(q, rest[h][0]))
            ds.sort()
            n = len(ds)
            med = ds[n//2]; p25 = ds[n//4]; p75 = ds[3*n//4]
            flag = ' <<<' if med < 20 else ''
            print(f'{uname:10s} {pname:9s} {kname:6s} {med:8.1f} {p25:7.1f} {p75:7.1f} {n}{flag}')

# delta hypothesis: keys as rotation DELTA from rest -> mean key values should be ~0
print('\nmean key values (delta hypothesis: mean ~ 0 if deltas):')
for h in matched[:8]:
    print(f'  {h:08X} n={trk[h]["n"]:3d} mean=({trk[h]["mean"][0]:8.1f},{trk[h]["mean"][1]:8.1f}) first=({trk[h]["first"][0]:6d},{trk[h]["first"][1]:6d})')
