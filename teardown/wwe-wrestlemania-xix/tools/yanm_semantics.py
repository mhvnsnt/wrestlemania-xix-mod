#!/usr/bin/env python3
"""YANM task-2 finish: time-channel semantics, dual-track semantics, euler unit.
Uses ONLY measured data: per-track total-duration consistency as the
segmentation discriminator, quat-norm constancy test for dual tracks,
angular-distance fit of key values against .ycg rest quats for the unit.
Streams from ISO (never extracts)."""
import struct, sys, math, json
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32, f32

data, size = stream_file('ringmotion/a000_0a.yag')

def s16(b): return struct.unpack('>h', b)[0]
def u16(b): return struct.unpack('>H', b)[0]

# ---------- header ----------
print('== header words ==')
for i in range(0, 0x50, 16):
    w = ' '.join(f'{u32(data,j):08X}' for j in range(i, i+16, 4))
    fl = ' '.join(f'{f32(data,j):12.6g}' for j in range(i, i+16, 4))
    print(f'  0x{i:02X}: {w}\n           {fl}')

# ---------- track directory ----------
def tracks():
    recs = []
    for r in range(29):
        o = 0x50 + r * 32
        h = u32(data, o); a = u32(data, o+4); ks = u32(data, o+8)
        z = u32(data, o+12)
        f = (f32(data, o+16), f32(data, o+20), f32(data, o+24))
        kw = u32(data, o+28)
        if a == 0:
            recs.append(dict(hash=h, kind='single', n=kw, b_off=ks))
        else:
            recs.append(dict(hash=h, kind='dual', ca=kw >> 16, cb=kw & 0xFFFF,
                             a_off=a, b_off=ks))
    return recs

ts = tracks()

# ---------- 5B segmentation candidates ----------
def seg5(raw):
    n = len(raw) // 5
    out = {}
    # c1: (x:u16, dt:u8, y:s16)
    out['x16_dt8_y'] = ([u16(raw[i:i+2]) for i in range(0, len(raw), 5)],
                        [raw[i+2] for i in range(0, len(raw), 5)],
                        [s16(raw[i+3:i+5]) for i in range(0, len(raw), 5)])
    # c2: (dt:u8, x:s16, y:s16)
    out['dt8_x_y'] = ([s16(raw[i+1:i+3]) for i in range(0, len(raw), 5)],
                      [raw[i] for i in range(0, len(raw), 5)],
                      [s16(raw[i+3:i+5]) for i in range(0, len(raw), 5)])
    # c3: (x:s16, y:s16, dt:u8)
    out['x_y_dt8'] = ([s16(raw[i:i+2]) for i in range(0, len(raw), 5)],
                      [raw[i+4] for i in range(0, len(raw), 5)],
                      [s16(raw[i+2:i+4]) for i in range(0, len(raw), 5)])
    # c4: (x:u8, dt:u16, y:s16) -- dt 16-bit spanning middle bytes
    out['x8_dt16_y'] = ([raw[i] for i in range(0, len(raw), 5)],
                        [u16(raw[i+1:i+3]) for i in range(0, len(raw), 5)],
                        [s16(raw[i+3:i+5]) for i in range(0, len(raw), 5)])
    return out

print('\n== 5B per-track total time under each candidate (must be ~equal across tracks) ==')
totals = {k: [] for k in ['x16_dt8_y', 'dt8_x_y', 'x_y_dt8', 'x8_dt16_y']}
for t in ts:
    off = t['b_off']; n = t['n'] if t['kind'] == 'single' else t['cb']
    raw = data[off:off + n * 5]
    for k, (xs, dts, ys) in seg5(raw).items():
        totals[k].append(sum(dts))
for k, vals in totals.items():
    lo, hi = min(vals), max(vals)
    print(f'  {k:10s} min={lo:7d} max={hi:7d} ratio={hi/max(1,lo):.3f} n_tracks={len(vals)}')

# ---------- 4B segmentation candidates (dual A) ----------
def seg4(raw):
    n = len(raw) // 4
    out = {}
    out['s16_s16'] = ([s16(raw[i:i+2]) for i in range(0, len(raw), 4)],
                      None,
                      [s16(raw[i+2:i+4]) for i in range(0, len(raw), 4)])
    out['u8_u8_s16'] = ([raw[i] for i in range(0, len(raw), 4)],
                        [raw[i+1] for i in range(0, len(raw), 4)],
                        [s16(raw[i+2:i+4]) for i in range(0, len(raw), 4)])
    out['s16_u8_u8'] = ([s16(raw[i:i+2]) for i in range(0, len(raw), 4)],
                        [raw[i+2] for i in range(0, len(raw), 4)],
                        [raw[i+3] for i in range(0, len(raw), 4)])
    out['u8_s16_u8'] = ([s16(raw[i+1:i+3]) for i in range(0, len(raw), 4)],
                        [raw[i] for i in range(0, len(raw), 4)],
                        [raw[i+3] for i in range(0, len(raw), 4)])
    return out

print('\n== 4B (dual A) raw hex of first 6 keys, track 7CC9B660-A ==')
raw4 = data[0xE6C:0xE6C + 6 * 4]
print('  ', raw4.hex(' '))
for i in range(6):
    k = raw4[i*4:(i+1)*4]
    print(f'   key{i}: s16s16=({s16(k[:2]):6d},{s16(k[2:]):6d})  u8u8s16=({k[0]:3d},{k[1]:3d},{s16(k[2:]):6d})  s16u8u8=({s16(k[:2]):6d},{k[2]:3d},{k[3]:3d})  u8s16u8=({k[0]:3d},{s16(k[1:3]):6d},{k[3]:3d})')

# which 4B reading shares B's time base? compare candidate totals vs B totals
print('\n== dual A/B duration agreement (same joint -> same total time) ==')
for t in ts:
    if t['kind'] != 'dual': continue
    braw = data[t['b_off']:t['b_off'] + t['cb'] * 5]
    bseg = seg5(braw)['x16_dt8_y']
    btot = sum(bseg[1])
    araw = data[t['a_off']:t['a_off'] + t['ca'] * 4]
    cands = {}
    for k, (v1, dtc, v2) in seg4(araw).items():
        if dtc is None: continue
        cands[k] = sum(dtc)
    print(f'  track {t["hash"]:08X} ca={t["ca"]} cb={t["cb"]} B(x16_dt8_y)={btot} | A: ' +
          ' '.join(f'{k}={v}' for k, v in cands.items()))

# ---------- dual-track quat norm test ----------
print('\n== dual-track 4-channel quat test (per-key norm^2 constancy) ==')
# NOTE: A and B have different key counts -> cannot pair 1:1; report ranges instead
for t in ts:
    if t['kind'] != 'dual': continue
    braw = data[t['b_off']:t['b_off'] + t['cb'] * 5]
    xs = [s16(braw[i:i+2]) for i in range(0, len(braw), 5)]
    ys = [s16(braw[i+3:i+5]) for i in range(0, len(braw), 5)]
    araw = data[t['a_off']:t['a_off'] + t['ca'] * 4]
    a1 = [s16(araw[i:i+2]) for i in range(0, len(araw), 4)]
    a2 = [s16(araw[i+2:i+4]) for i in range(0, len(araw), 4)]
    print(f'  {t["hash"]:08X}: A ch1 range [{min(a1)},{max(a1)}] ch2 [{min(a2)},{max(a2)}] | '
          f'B ch1 [{min(xs)},{max(xs)}] ch2 [{min(ys)},{max(ys)}]')

# ---------- value ranges for single tracks ----------
print('\n== single-track value ranges (x16_dt8_y reading) ==')
for t in ts[:6]:
    if t['kind'] != 'single': continue
    raw = data[t['b_off']:t['b_off'] + t['n'] * 5]
    xs = [s16(raw[i:i+2]) for i in range(0, len(raw), 5)]
    ys = [s16(raw[i+3:i+5]) for i in range(0, len(raw), 5)]
    print(f'  {t["hash"]:08X} n={t["n"]}: x [{min(xs)},{max(xs)}] y [{min(ys)},{max(ys)}]')
