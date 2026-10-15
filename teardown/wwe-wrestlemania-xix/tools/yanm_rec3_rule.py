#!/usr/bin/env python3
"""YANM task-2 open: rec3 (ankle/wrist) procedural handling.
rec3 has no YANM channel. Compares candidate procedural rules by FK'ing the
leg chain (BD5B5259, hinge about local X) over ringmotion/a000_0a.yag and
measuring the foot segment's world-orientation stability (mean angular
deviation from bind). The rule that keeps the foot flattest wins.
Rules: hold0 (rec3=0), comp1 (rec3=-(r1+r2)), comp05 (rec3=-0.5*(r1+r2)).
Writes docs/yanm-rec3-rule.json."""
import struct, sys, json, math
import numpy as np
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32, f32
from fk_ycg import YcgRig, quat_to_mat, Rx

def s16(b): return struct.unpack('>h', b)[0]

rig = YcgRig()
data, _ = stream_file('ringmotion/a000_0a.yag')

def get_track(h):
    for r in range(29):
        o = 0x50 + r * 32
        if u32(data, o) == h:
            ks = u32(data, o + 8); n = u32(data, o + 28)
            raw = data[ks:ks + n * 5]
            c1 = np.array([s16(raw[i:i+2]) for i in range(0, n * 5, 5)], float)
            dts = np.array([raw[i + 2] for i in range(0, n * 5, 5)], float)
            c2 = np.array([s16(raw[i + 3:i + 5]) for i in range(0, n * 5, 5)], float)
            T = int(dts.sum())
            s1 = np.zeros(T); s2 = np.zeros(T); t = 0
            for v, d in zip(c1, dts):
                d = int(d)
                if t + d > T: d = T - t
                s1[t:t + d] = v; t += d
                if t >= T: break
            t = 0
            for v, d in zip(c2, dts):
                d = int(d)
                if t + d > T: d = T - t
                s2[t:t + d] = v; t += d
                if t >= T: break
            return s1, s2
    raise KeyError(h)

H = 0xBD5B5259
c1, c2 = get_track(H)
r1 = np.arcsin(np.clip(c1 / 32767.0, -1, 1))
r2 = np.arcsin(np.clip(c2 / 32767.0, -1, 1))
ch = rig.chain(H)  # 3 records proximal->distal
Rb = [quat_to_mat(r['quat']) for r in ch]

def foot_orientation(r3_series):
    """World orientation matrix of the foot segment (after rec3 hinge) per tick.
    Q_i = bind orientation of joint i relative to joint i-1's frame;
    world R = Q_0 @ Rx(a0) @ Q_1 @ Rx(a1) @ Q_2 @ Rx(a2)."""
    Q = [Rb[0]] + [np.linalg.inv(Rb[i - 1]) @ Rb[i] for i in (1, 2)]
    Rs = []
    for f in range(len(r1)):
        R = Q[0] @ Rx(r1[f]) @ Q[1] @ Rx(r2[f]) @ Q[2] @ Rx(r3_series[f])
        Rs.append(R)
    return np.array(Rs)

def ang_dev(Rs):
    R0 = Rs[0]
    devs = []
    for R in Rs:
        dR = R0.T @ R
        cosang = (np.trace(dR) - 1) / 2
        devs.append(math.degrees(math.acos(np.clip(cosang, -1, 1))))
    return np.mean(devs), np.max(devs)

rules = {
    'hold0': np.zeros_like(r1),
    'comp1': -(r1 + r2),
    'comp05': -0.5 * (r1 + r2),
}
print(f'leg chain {H:08X}, {len(r1)} ticks, r1 range [{np.degrees(r1).min():.1f},{np.degrees(r1).max():.1f}] r2 range [{np.degrees(r2).min():.1f},{np.degrees(r2).max():.1f}]')
out = {}
for name, r3 in rules.items():
    Rs = foot_orientation(r3)
    mean_d, max_d = ang_dev(Rs)
    out[name] = dict(mean_dev_deg=round(float(mean_d), 2), max_dev_deg=round(float(max_d), 2))
    print(f'  {name:6s}: mean foot-orientation deviation {mean_d:6.2f} deg, max {max_d:6.2f} deg')
best = min(out, key=lambda k: out[k]['mean_dev_deg'])
print('best:', best)
json.dump(dict(track='%08X' % H, ticks=len(r1),
               r1_deg=[round(float(np.degrees(r1).min()), 1), round(float(np.degrees(r1).max()), 1)],
               r2_deg=[round(float(np.degrees(r2).min()), 1), round(float(np.degrees(r2).max()), 1)],
               rules=out, best=best),
          open('docs/yanm-rec3-rule.json', 'w'), indent=1)
print('wrote docs/yanm-rec3-rule.json')
