#!/usr/bin/env python3
"""Item-10(2): do .atr event ticks align with motion peaks in the .yag?

For each clip: FK pose every 4 ticks (000_0 rig), motion energy E(t) =
sum of joint displacements. For each event tick of types
0x33/0x34/0x88/0x89/0x8B/0x32: percentile of E(tick) in clip E
distribution + local-max test (+-12 ticks). Baseline: 300 random ticks.
Also verifies yag-duration vs atr-0x01 timebase agreement.
"""
import os, sys, struct, json, math, random
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from yanm_ecd_render_test import (load_yag, load_ycg, pose_at,
                                  clip_duration_ticks)
from yanm_atr_semantics2 import parse_atr

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCRATCH = os.path.join(REPO, '.scratch', 'files')
random.seed(7)

def motion_energy(data, tracks, groups, axismap, dur, step=4):
    ts = np.arange(0, dur + 1, step)
    prev = None
    E = []
    for t in ts:
        pose = pose_at(data, 0.0, tracks, groups, axismap, float(t))
        vec = np.concatenate([np.asarray(p, float).ravel()
                              for p in pose.values()]) if pose else np.zeros(3)
        if prev is not None:
            n = min(len(vec), len(prev))
            E.append(float(np.abs(vec[:n] - prev[:n]).sum()))
        prev = vec
    return ts[1:], np.array(E)

def main():
    axismap = json.load(open(os.path.join(REPO, 'docs', 'yanm-task2-finish.json')))['axis_map']
    groups = load_ycg(os.path.join(SCRATCH, 'model__wrestler__000_0.ycg'))
    clips = ['c001_0a', 'c101_0a', 'c102_0a', 'c016_0a', 'c135_0a', 'c200_0a']
    per_type_pct = {t: [] for t in (0x33, 0x34, 0x88, 0x89, 0x8B, 0x32)}
    per_type_lm = {t: [0, 0] for t in (0x33, 0x34, 0x88, 0x89, 0x8B, 0x32)}
    base_pct, base_lm = [], [0, 0]
    for name in clips:
        data, spt, tracks = load_yag(os.path.join(SCRATCH, f'ringmotion__{name}.yag'))
        atr = parse_atr(os.path.join(SCRATCH, f'ringmotion__{name}.atr'))
        dur = clip_duration_ticks(data, tracks)
        e1 = [e['tick'] for e in atr['evs'] if e['type'] == 0x01]
        print(f'{name}: yag_dur={dur} atr_0x01={e1[0] if e1 else None} '
              f'ratio={(e1[0]/dur) if e1 and dur else None}')
        ts, E = motion_energy(data, tracks, groups, axismap, dur)
        if len(E) == 0:
            continue
        # percentile lookup via sorted E
        Es = np.sort(E)
        def pct(v):
            return float(np.searchsorted(Es, v)) / len(Es) * 100
        def localmax(tick, half=12):
            i = int(np.argmin(np.abs(ts - tick)))
            lo = max(0, i - half // 4); hi = min(len(E), i + half // 4 + 1)
            return E[i] >= E[lo:hi].max() - 1e-9
        for e in atr['evs']:
            t = e['type']
            if t not in per_type_pct:
                continue
            v = E[int(np.argmin(np.abs(ts - e['tick'])))]
            per_type_pct[t].append(pct(v))
            h, n = per_type_lm[t]
            per_type_lm[t] = (h + (1 if localmax(e['tick']) else 0), n + 1)
        for _ in range(300):
            rt = random.uniform(0, dur)
            v = E[int(np.argmin(np.abs(ts - rt)))]
            base_pct.append(pct(v))
            base_lm[1] += 1
            base_lm[0] += 1 if localmax(rt) else 0
    print('\nTYPE | n | mean E-percentile | local-max hit rate')
    for t in (0x33, 0x34, 0x88, 0x89, 0x8B, 0x32):
        n = len(per_type_pct[t])
        mp = sum(per_type_pct[t]) / n if n else 0
        h, nn = per_type_lm[t]
        print(f'  0x{t:02X} | {n} | {mp:5.1f} | {h}/{nn}={h/nn if nn else 0:.2f}')
    print(f'  BASE(random) | {len(base_pct)} | {sum(base_pct)/len(base_pct):5.1f} | '
          f'{base_lm[0]}/{base_lm[1]}={base_lm[0]/base_lm[1]:.2f}')

if __name__ == '__main__':
    main()
