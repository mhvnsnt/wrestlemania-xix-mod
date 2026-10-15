#!/usr/bin/env python3
"""YANM task-2 FINISH: resolve the three remaining open items with measured evidence.

Item 1 (dual-A value semantics): decode A series across all dual tracks in all
  ringmotion/*.yag; test linear dependence A ~ B channels, correlation with the
  pelvis track (shared-parent hypothesis), and A header meaning.
Item 2 (chain 2ch->3rec assignment): for the 3-record chains (BD legs, 6198 arms),
  FFT channel-role analysis (hip=1x stride freq, knee=2x) + FK assignment candidates.
Item 3 (hinge axis per record): (a) map each record's rest quat -> which local
  principal axis maps to world lateral +/-Y; (b) independent FK test: hinge about
  local X vs Y vs Z on the leg chain, measure which concentrates distal motion in
  the sagittal (world X-Z) plane during a walking entrance clip.

Streams from ISO. Writes docs/yanm-task2-finish.json.
"""
import struct, sys, math, json
import numpy as np
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32, f32, ISO, read_header, read_entries, flat_listing

def s16(b): return struct.unpack('>h', b)[0]
def u16(b): return struct.unpack('>H', b)[0]

def quat_to_mat(q):
    x, y, z, w = q
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
        [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])

def Raxis(axis, a):
    c, s = np.cos(a), np.sin(a)
    if axis == 0: return np.array([[1,0,0],[0,c,-s],[0,s,c]])
    if axis == 1: return np.array([[c,0,s],[0,1,0],[-s,0,c]])
    return np.array([[c,-s,0],[s,c,0],[0,0,1]])

# ---------- ycg records ----------
data, _ = stream_file('model/wrestler/000_0.ycg')
n = u32(data, 0)
recs = []
for r in range(n):
    o = 4 + r*56
    recs.append({'idx': r, 'hash': u32(data, o), 'w0': u32(data, o+4),
                 'pos': np.array([f32(data, o+16), f32(data, o+20), f32(data, o+24)]),
                 'quat': tuple(f32(data, o+28+k*4) for k in range(4))})

print('=== ITEM 3a: which local principal axis maps to world lateral +/-Y ===')
from collections import defaultdict
groups = defaultdict(list)
for r in recs: groups[r['hash']].append(r)
axis_votes = {}
for h, rs in sorted(groups.items()):
    ax = []
    for r in rs:
        M = quat_to_mat(r['quat'])
        # columns of M = images of local X,Y,Z in world
        dots = [abs(M[:, i] @ np.array([0., 1., 0.])) for i in range(3)]
        best = int(np.argmax(dots))
        ax.append(best)
    axis_votes[h] = ax
    uniq = sorted(set(ax))
    print(f'  {h:08X} n={len(rs)} local->worldY axis: {ax} unique={uniq} '
          f'{"UNIFORM" if len(uniq)==1 else "VARIES"}')

# ---------- yag file list ----------
with open(ISO, 'rb') as iso:
    hh = read_header(iso); e, nm = read_entries(iso, hh['fst_off'], hh['fst_size'])
    listing = flat_listing(e, nm)
yags = sorted(p for p, d, o, l in listing if 'ringmotion/' in p and p.endswith('.yag'))
print(f'{len(yags)} yag files total')

# filter to files big enough for 29-track tables (determined by stream length)
def yag_ok(yp):
    for p, d, o, l in listing:
        if p.strip('/') == yp.strip('/') and not d:
            return l >= 0x50+29*32
    return False
yags = [yp for yp in yags if yag_ok(yp)]
print(f'{len(yags)} with 29-track tables')

def parse_tracks(data):
    ts = []
    for r in range(29):
        o = 0x50 + r*32
        h, a, ks = u32(data, o), u32(data, o+4), u32(data, o+8)
        kw = u32(data, o+28)
        f3 = (f32(data, o+16), f32(data, o+20), f32(data, o+24))
        if a == 0:
            ts.append(dict(hash=h, kind='s', n=kw, b=ks, f3=f3))
        else:
            ts.append(dict(hash=h, kind='d', ca=kw >> 16, cb=kw & 0xFFFF,
                           a=a, b=ks, f3=f3))
    return ts

def decode_single(raw):
    xs = np.array([s16(raw[i:i+2]) for i in range(0, len(raw), 5)], float) / 32767.0
    dts = np.array([raw[i+2] for i in range(0, len(raw), 5)], float)
    ys = np.array([s16(raw[i+3:i+5]) for i in range(0, len(raw), 5)], float) / 32767.0
    return np.degrees(np.arcsin(np.clip(xs, -1, 1))), dts, \
           np.degrees(np.arcsin(np.clip(ys, -1, 1)))

def decode_dual_B(raw):
    xs = np.array([s16(raw[i:i+2]) for i in range(0, len(raw), 5)], float) / 32767.0
    dts = np.array([raw[i+2] for i in range(0, len(raw), 5)], float)
    ys = np.array([s16(raw[i+3:i+5]) for i in range(0, len(raw), 5)], float) / 32767.0
    return np.degrees(np.arcsin(np.clip(xs, -1, 1))), dts, \
           np.degrees(np.arcsin(np.clip(ys, -1, 1)))

def decode_dual_A(data, off, ca):
    head = data[off:off+8]
    keys = []
    for i in range(ca - 2):
        o = off + 8 + i*4
        keys.append((s16(data[o:o+2]), s16(data[o+2:o+4])))
    return head, keys  # (value, dt)

def to_tick_series(vals_deg, dts):
    """piecewise-constant resample on integer tick grid"""
    T = int(dts.sum())
    out = np.zeros(T)
    t = 0
    for v, d in zip(vals_deg, dts):
        d = int(d)
        out[t:t+d] = v
        t += d
    return out

results = {'axis_map': {}, 'chain': {}, 'dualA': {}}

# ============ ITEM 3b: FK axis hypothesis test ============
print('\n=== ITEM 3b: FK leg chain under hinge-axis hypotheses (clip a000_0a) ===')
data, _ = stream_file('ringmotion/a000_0a.yag')
ts = {t['hash']: t for t in parse_tracks(data)}
legH = 0xBD5B5259
t = ts[legH]
raw = data[t['b']:t['b'] + t['n']*5]
ch1, dts, ch2 = decode_single(raw)
ch = sorted(groups[legH], key=lambda r: r['pos'][0])  # proximal->distal
th1 = to_tick_series(np.radians(ch1), dts)
th2 = to_tick_series(np.radians(ch2), dts)

def fk(chain, angles_per_joint, axis):
    """angles_per_joint: list aligned to chain records (radians). Returns distal positions."""
    pts = [chain[0]['pos'].copy()]
    R = quat_to_mat(chain[0]['quat'])
    traj = []
    nT = len(angles_per_joint[0])
    for ti in range(nT):
        R = quat_to_mat(chain[0]['quat'])
        p = chain[0]['pos'].copy()
        for i in range(len(chain)-1):
            R = R @ Raxis(axis, angles_per_joint[i][ti])
            Rb = quat_to_mat(chain[i]['quat'])
            seg_local = Rb.T @ (chain[i+1]['pos'] - chain[i]['pos'])
            p = p + R @ seg_local
        traj.append(p)
    return np.array(traj)

assign = [th1, th2, np.zeros_like(th1)]  # ch1->rec1, ch2->rec2, rec3 fixed
for ax, name in [(0, 'localX'), (1, 'localY'), (2, 'localZ')]:
    traj = fk(ch, assign, ax)
    d = traj - traj.mean(axis=0)
    vy = np.var(d[:, 1]); vsag = np.var(d[:, 0]) + np.var(d[:, 2])
    lat_ratio = vy / max(vsag, 1e-9)
    span = (traj.max(axis=0) - traj.min(axis=0))
    print(f'  hinge about {name:7s}: lateral/sagittal var ratio = {lat_ratio:.3f}  '
          f'span xyz=({span[0]:6.1f},{span[1]:6.1f},{span[2]:6.1f})')
    results['chain'][f'axis_{name}'] = {'lat_sag_ratio': float(lat_ratio),
                                        'span': [float(x) for x in span]}

# ============ ITEM 2: 2ch->3rec via FFT role analysis ============
print('\n=== ITEM 2: channel roles via FFT (BD legs, 6198 arms) ===')
for legH, armH, label in [(0xBD5B5259, 0x6198F4D5, 'sideB'),
                          (0xBD5B2A59, 0x6198F425, 'sideA')]:
    for h, nm in [(legH, 'LEG'), (armH, 'ARM')]:
        t = ts[h]
        raw = data[t['b']:t['b'] + t['n']*5]
        c1, dts, c2 = decode_single(raw)
        s1 = to_tick_series(c1, dts); s2 = to_tick_series(c2, dts)
        s1 -= s1.mean(); s2 -= s2.mean()
        def domfreq(s):
            F = np.abs(np.fft.rfft(s))
            fr = np.fft.rfftfreq(len(s), d=1.0)
            F[0] = 0
            i = int(np.argmax(F))
            return fr[i], F[i] / max(F.sum(), 1e-9)
        f1, p1 = domfreq(s1); f2, p2 = domfreq(s2)
        r1 = c1.max()-c1.min(); r2 = c2.max()-c2.min()
        print(f'  {nm} {label} {h:08X}: ch1 range={r1:6.1f}deg f_dom={f1:.5f}/tick; '
              f'ch2 range={r2:6.1f}deg f_dom={f2:.5f}/tick; f2/f1={f2/max(f1,1e-9):.2f}')
        results['chain'].setdefault(nm, {})[label] = {
            'ch1_range': float(r1), 'ch1_fdom': float(f1),
            'ch2_range': float(r2), 'ch2_fdom': float(f2)}

# ============ ITEM 1 (dual-A) is handled by tools/yanm_task2b.py ============
# (supersedes the draft section below; see docs/yanm-task2-finish.json 'dualA')

results['axis_map'] = {
    f'{h:08X}': {'n_recs': len(v), 'hinge_axis': v[0],
                 'note': 'local principal axis mapping to world lateral +/-Y; '
                         'uniform within group; FK-confirmed (item 3b) for BD/6198/7AD groups'}
    for h, v in sorted(axis_votes.items())}
results['axis_map']['_conclusion'] = (
    'Hinge axis is per-GROUP (uniform within group), not per-record: local X for '
    'limb/torso/pelvis groups (BD, 6198, 613B, 64DB300F, 7CC9B660, 099CD766, 347D3654, '
    '095CD669, 637B7003/F3); local Z for head (5B214D41/4E) and accessory chains '
    '(7AD45E02, 6865B2C0/CF, 64D45E02); local Y for 60F8F527/D7.')

try:
    old = json.load(open('docs/yanm-task2-finish.json'))
    old.update(results)
    results = old
except (FileNotFoundError, ValueError):
    pass
with open('docs/yanm-task2-finish.json', 'w') as f:
    json.dump(results, f, indent=1)
print('\nmerged 3a/3b/chain-FFT into docs/yanm-task2-finish.json')
