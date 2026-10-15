#!/usr/bin/env python3
"""Task-4 v1: retarget a YANM wrestling animation onto a Tekken 3 model.

Pipeline: YANM (.yag) -> per-group hinge series (x-channel, asin unit)
-> ycg-group -> Tekken-3 FK Euler joint map -> 49-channel Tekken pose
sequence (base = King stance0, YANM deltas mean-subtracted and added).

v1 SCOPE: FK Euler joints only (pelvis/chest/hips/head/shoulders).
Tekken-3 limbs are IK-driven (channels 3-14); leg/arm IK retarget is v2.
The 1-DOF YANM hinge is applied to the Tekken joint's local X channel
(axis mapping provisional -- documented open item).

Streams the .yag from ISO (never extracts). Reads King stance pose from
../../tekken3/models/king95/king95_stance0_pose.json.
"""
import struct, sys, math, json
import numpy as np
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32

def s16(b): return struct.unpack('>h', b)[0]

YAG = sys.argv[1] if len(sys.argv) > 1 else 'ringmotion/a000_0a.yag'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'docs/yanm_to_tekken3_v1.json'
FPS = 30.0

# ycg group -> Tekken 3 FK joint (jointN -> slots per n0madic docs)
# joint0->slot0 pelvis, joint1->slot1 chest, joint2->slot11 hips,
# joint3->slot2 head, joint4->slot3 R shoulder, joint5->slot7 L shoulder
GMAP = {
    0x099CD766: 'joint0',   # pelvis candidate
    0x613B75B7: 'joint1',   # torso 2-hinge (active side)
    0x095CD669: 'joint2',   # hips (static hold)
    0x5B214D4E: 'joint3',   # head/neck candidate (side B)
    0x6198F425: 'joint4',   # arm side-A -> R shoulder (L/R provisional)
    0x6198F4D5: 'joint5',   # arm side-B -> L shoulder (L/R provisional)
}

data, _ = stream_file(YAG)
s_per_tick = struct.unpack('>f', data[0x3C:0x40])[0]
print(f'{YAG}: s/tick={s_per_tick:.6f}')

def track_series(h):
    for r in range(29):
        o = 0x50 + r * 32
        if u32(data, o) == h:
            a, ks = u32(data, o + 4), u32(data, o + 8)
            kw = u32(data, o + 28)
            n = kw if a == 0 else kw & 0xFFFF
            raw = data[ks:ks + n * 5]
            xs = np.array([s16(raw[i:i + 2]) for i in range(0, len(raw), 5)], float) / 32767.0
            dts = np.array([raw[i + 2] for i in range(0, len(raw), 5)], float)
            t = np.concatenate([[0.0], np.cumsum(dts)])[:-1] * s_per_tick
            ang = np.arcsin(np.clip(xs, -1, 1))  # radians, absolute hinge
            return t, ang
    raise KeyError(f'track {h:08X} not found')

CH_NAMES = (['root_x', 'root_y', 'root_z']
            + [f'ik{i}_{a}' for i in range(4) for a in 'xyz']
            + [f'swivel{i}' for i in range(4)]
            + [f'joint{i}_{a}' for i in range(10) for a in 'xyz'])
assert len(CH_NAMES) == 49

import os
T3DIR = os.path.expanduser('~/workspace/game-reverse-engineering/tekken3')
stance = json.load(open(os.path.join(T3DIR, 'models/king95/king95_stance0_pose.json')))
base = np.array([stance['pose_channels'][c] for c in CH_NAMES], dtype=float)
print('base pose:', stance['note'][:80])

# decode + resample all mapped groups to common 30fps grid
series = {}
ends = []
tmp = {}
for h in GMAP:
    t, ang = track_series(h)
    tmp[h] = (t, ang)
    if len(t) > 1:
        ends.append(t[-1])
t_end = min(ends)
grid = np.arange(0, t_end, 1.0 / FPS)
print(f'duration {t_end:.2f}s -> {len(grid)} frames @ {FPS}fps')
for h, jname in GMAP.items():
    t, ang = tmp[h]
    if len(t) > 1:
        v = np.interp(grid, t, ang)
    else:
        v = np.full_like(grid, ang[0])  # static track: constant hold
    series[jname] = v - v.mean()  # mean-subtract: motion overlay on stance
    print(f'  {h:08X} -> {jname}: raw range {np.degrees(ang).min():+.1f}..{np.degrees(ang).max():+.1f} deg, '
          f'delta std {np.degrees(v - v.mean()).std():.2f} deg')

T3_PER_RAD = 65536.0 / (2 * math.pi)
poses = []
for f in range(len(grid)):
    p = base.copy()
    for jname, v in series.items():
        idx = CH_NAMES.index(jname + '_x')
        p[idx] = np.clip(p[idx] + v[f] * T3_PER_RAD, -32768, 32767)
    poses.append([int(round(x)) for x in p])

out = {
    'schema': 'yanm->tekken3 retarget v1',
    'source_yag': YAG,
    'source_duration_s': round(t_end, 3),
    'fps': FPS,
    'frames': len(grid),
    'tekken_model': 'tekken3/models/king95 (King, BNS record 95)',
    'tekken_angle_unit': '65536 = 360deg; base = king95_stance0_pose.json',
    'group_to_joint': {f'{h:08X}': j for h, j in GMAP.items()},
    'scope': 'FK Euler joints only (joint0-5). IK limbs (ik0-3, swivel) NOT driven in v1.',
    'caveats': [
        '1-DOF YANM hinge applied to Tekken joint local X (axis mapping provisional)',
        'ycg side-A/B -> Tekken R/L provisional',
        'mean-subtracted deltas: Tekken keeps its stance, gets YANM motion overlay',
        'legs (BD groups) not driven: Tekken legs are IK, needs FK->IK-target conversion (v2)',
    ],
    'channel_names': CH_NAMES,
    'poses': poses,
}
json.dump(out, open(OUT, 'w'))
print(f'wrote {OUT} ({len(grid)} frames)')

# verification: driven-channel stats
print('\n== verification: driven Tekken channels ==')
for h, jname in GMAP.items():
    idx = CH_NAMES.index(jname + '_x')
    col = np.array([p[idx] for p in poses], float)
    print(f'  {jname}_x: base={base[idx]:+.0f} range {col.min():+.0f}..{col.max():+.0f} '
          f'({np.degrees((col-base[idx])/T3_PER_RAD).min():+.1f}..{np.degrees((col-base[idx])/T3_PER_RAD).max():+.1f} deg delta)')
