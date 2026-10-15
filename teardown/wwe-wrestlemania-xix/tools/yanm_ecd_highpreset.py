#!/usr/bin/env python3
"""Item-10(1): ECD (0,~75) high-preset role + elevation sign.

High-preset clips (ch1~=0, ch2~=70-80): what poses do they hold at mid-frame?
Test the star-shape hypothesis: high preset <-> wide/spread poses that read
well from a near-top-down camera (showcases, taunts), NOT aerial elevation
(root translation is not animated in YANM FK - the root is pinned - so a
pelvis-height test is impossible; spread is the measurable proxy).

Measures at mid-frame, in display frame (x=fwd, y=lateral, z=up):
  - foot_spread: distance between the two leg-chain tips (ankles)
  - hand_spread: distance between the two arm-chain tips
  - body_len: pelvis-root (347D3654 first joint) to head tip (5B214D41 last)
Reports spreads normalized by body_len, by ECD preset class.
Renders 3 high-preset clips from their ECD view for eye verification.

Elev sign: FACE_ecd_view.png (elev=+79.9) shows a near-top-down mugshot of
the performer - sensible as an above-horizon camera; a below-ring camera is
physically implausible (ring floor). Confirm by rendering c139 at elev=-80
(absurd control) vs elev=+80.
"""
import struct, math, json, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# reuse FK machinery from the render test
import importlib.util
spec = importlib.util.spec_from_file_location(
    "rt", os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "yanm_ecd_render_test.py"))
rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)

SCR = rt.SCRATCH
REPO = rt.REPO
OUTDIR = os.path.join(REPO, 'docs', 'ecd-render-test')

LEG_L, LEG_R = 0xBD5B2A59, 0xBD5B5259
ARM_L, ARM_R = 0x6198F425, 0x6198F4D5
PELVIS = 0x347D3654
HEAD = 0x5B214D41

def mid_pose(path, groups, axismap):
    data, spt, tracks = rt.load_yag(path)
    dur = rt.clip_duration_ticks(data, tracks)
    pose = rt.pose_at(data, spt, tracks, groups, axismap, dur / 2.0)
    ecd = next(t for t in tracks if t['hash'] == 0xECD28978)
    a1, a2 = rt.sample_single(data, ecd, dur / 2.0)
    return pose, (a1, a2)

def spread(pose, h1, h2):
    if h1 not in pose or h2 not in pose:
        return None
    p1 = rt.to_display(pose[h1])[-1]
    p2 = rt.to_display(pose[h2])[-1]
    return float(np.linalg.norm(p1 - p2))

def body_len(pose):
    if PELVIS not in pose or HEAD not in pose:
        return None
    return float(np.linalg.norm(rt.to_display(pose[PELVIS])[0] -
                                rt.to_display(pose[HEAD])[-1]))

CLIPS = {
    # high preset
    'a004_0a': 'high', 'a021_0a': 'high', 'b012_0a': 'high',
    'c139_0a': 'high', 'c140_0a': 'high', 'c226_0a': 'high',
    'c102_0a': 'high', 'd000_0a': 'high', 'c': 'high',
    # default preset
    'c004_0a': 'default', 'c007_0a': 'default', 'c103_0a': 'default',
    'c105_0a': 'default', 'c108_0a': 'default', 'c111_0a': 'default',
    # reference (already extracted)
    'c200_0a': 'side', 'FACE': 'high', '8503_0a': 'high',
}

def main():
    axismap = json.load(open(os.path.join(REPO, 'docs', 'yanm-task2-finish.json')))['axis_map']
    groups = rt.load_ycg(os.path.join(SCR, 'model__wrestler__000_0.ycg'))
    rows = []
    for name, cls in CLIPS.items():
        fn = ('viewer__motion__%s.yag' % name if name in ('FACE', '8503_0a')
              else 'ringmotion__%s.yag' % name)
        path = os.path.join(SCR, fn)
        if not os.path.exists(path):
            rows.append({'clip': name, 'class': cls, 'missing': True})
            continue
        pose, ecd = mid_pose(path, groups, axismap)
        bl = body_len(pose)
        fs = spread(pose, LEG_L, LEG_R)
        hs = spread(pose, ARM_L, ARM_R)
        rows.append({'clip': name, 'class': cls, 'ecd': [round(ecd[0], 1), round(ecd[1], 1)],
                     'body_len': round(bl, 1) if bl else None,
                     'foot_spread': round(fs / bl, 3) if (fs and bl) else None,
                     'hand_spread': round(hs / bl, 3) if (hs and bl) else None})
    json.dump(rows, open(os.path.join(OUTDIR, 'highpreset_metrics.json'), 'w'), indent=1)
    for r in rows:
        print(r)
    # renders: 3 high-preset clips from ECD view + c139 elev=-80 absurd control
    renders = [('c139_0a', 'high'), ('a004_0a', 'high'), ('8503_0a', 'high')]
    for name, _ in renders:
        fn = ('viewer__motion__%s.yag' % name if name == '8503_0a'
              else 'ringmotion__%s.yag' % name)
        path = os.path.join(SCR, fn)
        if not os.path.exists(path):
            continue
        pose, ecd = mid_pose(path, groups, axismap)
        rt.render_pose(pose, '%s ECD view elev=%.1f azim=%.1f' % (name, ecd[1], ecd[0]),
                       (ecd[1], ecd[0]),
                       os.path.join(OUTDIR, '%s_highpreset_view.png' % name))
        print('rendered', name)
    # absurd control: c139 at elev=-80
    pose, ecd = mid_pose(os.path.join(SCR, 'ringmotion__c139_0a.yag'), groups, axismap)
    rt.render_pose(pose, 'c139 CONTROL elev=-80 (below-ring, absurd)',
                   (-80.0, ecd[0]),
                   os.path.join(OUTDIR, 'c139_control_below.png'))
    print('rendered c139 control')

if __name__ == '__main__':
    main()
