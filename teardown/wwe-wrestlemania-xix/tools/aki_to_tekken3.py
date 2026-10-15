#!/usr/bin/env python3
"""AKI (No Mercy) -> Tekken 3 retarget test.

Decodes a No Mercy AkiAnimation (19x 1-DOF s8 hinge joints + root movement)
and retargets it onto the Tekken 3 King skeleton (49-channel pose).

Pipeline (follows the proven YANM->Tekken3 pattern):
1. Decode AKI: s8 rotation -> radians (s8 * (180/128) deg; s8*256 = Tekken s16).
2. Map AKI joints -> Tekken 3 FK Euler joints (joint0-9).
3. Overlay: tekken(t) = stance0 + (aki(t) - mean(aki)) on X channel
   (provisional axis, like YANM v1; sagittal hinges -> X).
4. Root: AKI OverallMovement -> Tekken root_x/y/z (scaled).
5. Output JSON + verification plot.

Usage: python3 aki_to_tekken3.py [fileid_hex] [out_json]
"""
import struct, sys, math, json, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               '../../wwf-no-mercy/tools'))
from anim_extract import load_anim, ROM as AKI_ROM
import numpy as np

FID = int(sys.argv[1], 16) if len(sys.argv) > 1 else 0x339A
OUT = sys.argv[2] if len(sys.argv) > 2 else 'docs/aki_to_tekken3_v1.json'

CH_NAMES = (['root_x', 'root_y', 'root_z']
            + [f'ik{i}_{a}' for i in range(4) for a in 'xyz']
            + [f'swivel{i}' for i in range(4)]
            + [f'joint{i}_{a}' for i in range(10) for a in 'xyz'])
assert len(CH_NAMES) == 49

# AKI joint -> Tekken FK joint (provisional anatomical mapping)
# Tekken joint0=pelvis, joint1=chest, joint2=?, joint3=head,
# joint4=R shoulder, joint5=L shoulder (per YANM v1 mapping)
AKI_TO_T3 = {
    'Pelvis': 'joint0',
    'LowerAb': 'joint1',
    'UpperBody': 'joint1',
    'Neck': 'joint3',
    'Head': 'joint3',
    'UpperRightArm': 'joint4',
    'UpperLeftArm': 'joint5',
    'LowerRightArm': 'joint6',
    'LowerLeftArm': 'joint7',
    'UpperRightLeg': 'joint8',
    'UpperLeftLeg': 'joint9',
    'LowerRightLeg': 'joint8',
    'LowerLeftLeg': 'joint9',
}

T3DIR = os.path.expanduser('~/workspace/game-reverse-engineering/tekken3')
stance = json.load(open(os.path.join(T3DIR, 'models/king95/king95_stance0_pose.json')))
base = np.array([stance['pose_channels'][c] for c in CH_NAMES], dtype=float)

data = open(AKI_ROM, 'rb').read()
anim = load_anim(data, FID)
frames = anim['frames']
n = len(frames)
print(f"AKI file {FID:04X}: {n} frames, toki2={anim['toki2']}")

# Extract s8 rotations per mapped joint
series = {}
for aki_joint, t3_joint in AKI_TO_T3.items():
    vals = np.array([f[aki_joint]['rot'] for f in frames], dtype=float)
    series.setdefault(t3_joint, []).append(vals)

# Root movement (OverallMovement)
root_vals = np.array([f['OverallMovement']['overall'] for f in frames], dtype=float)
print(f"root movement range: x {root_vals[:,0].min():.0f}..{root_vals[:,0].max():.0f}, "
      f"y {root_vals[:,1].min():.0f}..{root_vals[:,1].max():.0f}, "
      f"z {root_vals[:,2].min():.0f}..{root_vals[:,2].max():.0f}")

# s8 -> Tekken s16: s8 * 256 (s8 -128..127 = -180..180 deg; T3 65536 = 360 deg)
S8_TO_T3 = 65536.0/360.0  # s8 = degrees, T3 65536 = 360 deg

poses = []
for fi in range(n):
    p = base.copy()
    for t3_joint, vlist in series.items():
        # average if multiple AKI joints map to one T3 joint
        v = np.mean(vlist, axis=0)
        delta = (v - v.mean()) * S8_TO_T3
        idx = CH_NAMES.index(t3_joint + '_x')
        p[idx] = np.clip(p[idx] + delta[fi], -32768, 32767)
    # root: scale AKI units to Tekken (provisional: AKI ~ /4?)
    # AKI overall movement is in pivot units; scale down
    for j, ax in enumerate('xyz'):
        idx = CH_NAMES.index(f'root_{ax}')
        rv = root_vals[:, j]
        delta = (rv - rv.mean()) * 0.5  # provisional scale
        p[idx] = np.clip(p[idx] + delta[fi], -32768, 32767)
    poses.append([int(round(x)) for x in p])

out = {
    'schema': 'aki->tekken3 retarget v1',
    'source_file': f'No Mercy anim {FID:04X}',
    'source_frames': n,
    'toki2': anim['toki2'],
    'tekken_model': 'tekken3/models/king95 (King, BNS record 95)',
    'joint_map': AKI_TO_T3,
    'axis_map': 'AKI s8 hinge -> Tekken joint X channel (provisional, cf. YANM v1)',
    'scale': 's8 * 182.04 = Tekken s16 (s8 IS degrees; T3 65536 = 360 deg)',
    'overlay': 'tekken(t) = stance0 + (aki(t) - mean(aki))',
    'caveats': [
        'AKI hinge axis (which Euler axis) is provisional; using X for all',
        'Multiple AKI joints averaged when mapping to one T3 joint (e.g. LowerAb+UpperBody->joint1)',
        'Root movement scale (0.5) is provisional',
        'Legs/arms: AKI has separate upper/lower; T3 FK joints may not match 1:1',
    ],
    'channel_names': CH_NAMES,
    'poses': poses,
}
os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
json.dump(out, open(OUT, 'w'))
print(f"wrote {OUT} ({n} frames)")

# verification: check driven channels move
for t3_joint in sorted(set(AKI_TO_T3.values())):
    idx = CH_NAMES.index(t3_joint + '_x')
    vals = [p[idx] for p in poses]
    base_v = base[idx]
    deltas = [v - base_v for v in vals]
    print(f"  {t3_joint}_x: delta {min(deltas):+.0f}..{max(deltas):+.0f} (base {base_v:.0f})")
