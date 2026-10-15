#!/usr/bin/env python3
"""Task-4 v2: YANM -> Tekken3 retarget with leg/arm IK, corrected axes, resolved L/R.

v2 changes vs v1:
(a) LEG/ARM IK: FK the YANM ycg chains (hip=2*unwrap(atan2(c2,c1)) half-angle
    decode; arm shoulder/elbow=asin small-regime) -> ankle/wrist trajectories
    in ycg space -> map to Tekken3 normalized-skeleton IK target channels
    (overlay: base stance + R.(tip-mean).scale).
(b) HINGE->EULER AXIS: YANM hinge is about ycg lateral (local X -> world Y);
    in Tekken3 normalized space lateral = Z. FK Euler joints now driven on
    the Z channel (v1 used X = yaw, wrong for sagittal pitch).
(c) L/R: ycg y+ = R (Yukes authoring convention, cf. ymg local frames y+=R);
    ycg-R -> T3-R (ik0/ch3-5 R arm, ik2/ch9-11 R leg). ycg->T3 map
    T3=(-ycg_x,-ycg_z,-ycg_y) has det=+1 (chirality-preserving, no mirror).
    Arms are pure IK in v2 (v1 shoulder-Euler drive removed to avoid double-drive).
(d) Render verification: tools/render_retarget_v2.py (schematic stick figures).

Streams the .yag from ISO (never extracts). Reads King stance pose from
../../tekken3/models/king95/king95_stance0_pose.json.
"""
import struct, sys, math, json, os
import numpy as np
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32
from fk_ycg import YcgRig

def s16(b): return struct.unpack('>h', b)[0]

YAG = sys.argv[1] if len(sys.argv) > 1 else 'ringmotion/a000_0a.yag'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'docs/yanm_to_tekken3_v2.json'
FPS = 30.0

# ---------------- YANM decode ----------------
data, _ = stream_file(YAG)
s_per_tick = struct.unpack('>f', data[0x3C:0x40])[0]

def get_track(h):
    for r in range(29):
        o = 0x50 + r * 32
        if u32(data, o) == h:
            a, ks = u32(data, o + 4), u32(data, o + 8)
            kw = u32(data, o + 28)
            n = kw if a == 0 else kw & 0xFFFF
            raw = data[ks:ks + n * 5]
            c1 = np.array([s16(raw[i:i+2]) for i in range(0, len(raw), 5)], float)
            dts = np.array([raw[i+2] for i in range(0, len(raw), 5)], float)
            c2 = np.array([s16(raw[i+3:i+5]) for i in range(0, len(raw), 5)], float)
            t = np.concatenate([[0.0], np.cumsum(dts)])[:-1] * s_per_tick
            return t, c1, c2
    raise KeyError(f'{h:08X}')

def leg_hip_angle(t, c1, c2):
    mag = np.sqrt(c1**2 + c2**2)
    a = np.arctan2(c2, c1)
    good = mag > 20000
    nidx = np.arange(len(a)); m = ~good
    if m.any() and (~m).any():
        a[m] = np.interp(nidx[m], nidx[~m], a[~m])
    return (np.unwrap(2*a) + np.pi) % (2*np.pi) - np.pi

def small_angles(c1, c2):
    return np.arcsin(np.clip(c1/32767.0, -1, 1)), np.arcsin(np.clip(c2/32767.0, -1, 1))

# ---------------- ycg FK ----------------
rig = YcgRig()

def chain_tip_series(h, kind, grid):
    t, c1, c2 = get_track(h)
    if kind == 'leg':
        A1 = np.interp(grid, t, leg_hip_angle(t, c1, c2)); A2 = np.zeros_like(A1)
    else:
        a1, a2 = small_angles(c1, c2)
        A1 = np.interp(grid, t, a1); A2 = np.interp(grid, t, a2)
    tips = np.array([rig.fk_chain(h, [A1[f], A2[f]])[-1] for f in range(len(grid))])
    return tips, (A1, A2)

# duration from leg tracks
t0, _, _ = get_track(0xBD5B5259)
grid = np.arange(0, t0[-1], 1.0/FPS)
print(f'duration {t0[-1]:.2f}s -> {len(grid)} frames @ {FPS}fps')

# ycg side -> limb: (hash, kind, label)
LIMBS = [
    (0xBD5B5259, 'leg', 'R'),  # y+ = R
    (0xBD5B2A59, 'leg', 'L'),  # y- = L
    (0x6198F425, 'arm', 'R'),  # y+ = R
    (0x6198F4D5, 'arm', 'L'),  # y- = L
]
tips = {}
for h, kind, side in LIMBS:
    tp, (A1, A2) = chain_tip_series(h, kind, grid)
    tips[(kind, side)] = tp
    print(f'  {h:08X} {kind}-{side}: hip/sh range {np.degrees(A1).min():+.1f}..{np.degrees(A1).max():+.1f} deg')

# ---------------- Tekken3 pose ----------------
CH_NAMES = (['root_x', 'root_y', 'root_z']
            + [f'ik{i}_{a}' for i in range(4) for a in 'xyz']
            + [f'swivel{i}' for i in range(4)]
            + [f'joint{i}_{a}' for i in range(10) for a in 'xyz'])
assert len(CH_NAMES) == 49
# ik0=R arm (ch3-5), ik1=L arm (ch6-8), ik2=R leg (ch9-11), ik3=L leg (ch12-14)

T3DIR = os.path.expanduser('~/workspace/game-reverse-engineering/tekken3')
stance = json.load(open(os.path.join(T3DIR, 'models/king95/king95_stance0_pose.json')))
base = np.array([stance['pose_channels'][c] for c in CH_NAMES], dtype=float)

# ycg -> T3 root-frame rotation (det=+1): T3 = (-x, -z, -y)
R_YCG_T3 = np.array([[-1., 0., 0.], [0., 0., -1.], [0., -1., 0.]])
assert abs(np.linalg.det(R_YCG_T3) - 1.0) < 1e-9
S_LEG = 895.0 / 34.06   # T3 normalized leg / ycg leg length
S_ARM = 533.0 / 26.08   # T3 normalized arm / ycg arm length
print(f'scales: leg {S_LEG:.2f}, arm {S_ARM:.2f}')

IK_CH = {('arm','R'): ('ik0', 0), ('arm','L'): ('ik1', 1),
         ('leg','R'): ('ik2', 2), ('leg','L'): ('ik3', 3)}

T3_PER_RAD = 65536.0 / (2*math.pi)
poses = []
for f in range(len(grid)):
    p = base.copy()
    for (kind, side), tp in tips.items():
        ikname, iki = IK_CH[(kind, side)]
        s = S_LEG if kind == 'leg' else S_ARM
        delta = R_YCG_T3 @ (tp[f] - tp.mean(axis=0)) * s
        for j, ax in enumerate('xyz'):
            idx = CH_NAMES.index(f'{ikname}_{ax}')
            p[idx] = np.clip(p[idx] + delta[j], -32768, 32767)
    # FK Euler: pelvis/chest/hips/head -> Z channel (sagittal pitch)
    for h, jname in [(0x099CD766, 'joint0'), (0x613B75B7, 'joint1'),
                     (0x095CD669, 'joint2'), (0x5B214D4E, 'joint3')]:
        t, c1, c2 = get_track(h)
        a1, _ = small_angles(c1, c2)
        v = np.interp(grid, t, a1) - np.interp(grid, t, a1).mean()
        idx = CH_NAMES.index(jname + '_z')
        p[idx] = np.clip(p[idx] + v[f]*T3_PER_RAD, -32768, 32767)
    poses.append([int(round(x)) for x in p])

out = {
    'schema': 'yanm->tekken3 retarget v2',
    'source_yag': YAG, 'source_duration_s': round(float(t0[-1]), 3),
    'fps': FPS, 'frames': len(grid),
    'tekken_model': 'tekken3/models/king95 (King, BNS record 95)',
    'limb_map': {'BD5B5259':'R leg->ik2/ch9-11', 'BD5B2A59':'L leg->ik3/ch12-14',
                 '6198F425':'R arm->ik0/ch3-5', '6198F4D5':'L arm->ik1/ch6-8'},
    'axis_map': 'T3=(-ycg_x,-ycg_z,-ycg_y), det=+1',
    'scales': {'leg': S_LEG, 'arm': S_ARM},
    'fk_euler': 'joint0-3 driven on Z channel (sagittal pitch); joint4/5 at base (arms pure IK)',
    'yanm_decode': {'leg_hip': '2*unwrap(atan2(c2,c1)) wrapped to +-180 (half-angle)',
                    'arm': 'asin(c1/32767), asin(c2/32767)',
                    'hinge_axis': 'ycg local X -> world lateral Y'},
    'caveats': ['ycg y+ = R assumed from Yukes ymg authoring convention (y+=R in bone locals)',
                'ycg forward/back sign provisional in axis map',
                'knee fixed at bind (YANM leg track carries 1 DOF); T3 IK solves knee',
                'swivels at stance base'],
    'channel_names': CH_NAMES, 'poses': poses,
}
json.dump(out, open(OUT, 'w'))
print(f'wrote {OUT} ({len(grid)} frames)')

# verification stats
print('\n== v2 driven-channel stats ==')
for (kind, side), tp in tips.items():
    ikname, iki = IK_CH[(kind, side)]
    s = S_LEG if kind == 'leg' else S_ARM
    d = (R_YCG_T3 @ (tp - tp.mean(axis=0)).T).T * s
    print(f'  {ikname} ({kind}-{side}): base=({base[3+iki*3]:+.0f},{base[4+iki*3]:+.0f},{base[5+iki*3]:+.0f}) '
          f'delta std=({d[:,0].std():.0f},{d[:,1].std():.0f},{d[:,2].std():.0f}) range=({d.min(axis=0).round(0)},{d.max(axis=0).round(0)})')
