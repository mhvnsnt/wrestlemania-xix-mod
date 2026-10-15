#!/usr/bin/env python3
"""Item-7(a): ECD camera-framing render test.

Builds FK skeletons from the ycg anim rig + yag mid-frame poses, renders each
clip from the ECD-derived viewpoint (view_init(elev=ch2, azim=ch1)) and from
control viewpoints, and measures framing quality to test the camera-framing
hypothesis for ECD28978 vs alternatives (eye gaze, opponent setup, metadata).

Reads local extracted files from $WMXIX_SCRATCH (see wmxix_extract.py).
Writes renders + metrics JSON to docs/ecd-render-test/ (git-tracked).
"""
import struct, math, json, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (projection='3d')

SCRATCH = os.environ.get('WMXIX_SCRATCH',
    '/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/.scratch/files')
REPO = '/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix'
OUTDIR = os.path.join(REPO, 'docs', 'ecd-render-test')
os.makedirs(OUTDIR, exist_ok=True)

def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]
def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]
def f32(b, i): return struct.unpack('>f', b[i:i+4])[0]
def adeg(v): return math.degrees(math.asin(max(-1.0, min(1.0, v / 32767.0))))

# ---------------- ycg ----------------
def load_ycg(path):
    data = open(path, 'rb').read()
    n = u32(data, 0)
    groups = {}
    for r in range(n):
        o = 4 + r * 56
        h = u32(data, o)
        pos = np.array([f32(data, o+16), f32(data, o+20), f32(data, o+24)])
        quat = tuple(f32(data, o+28+k*4) for k in range(4))
        groups.setdefault(h, []).append({'pos': pos, 'quat': quat})
    # order proximal->distal: sort along axis of max spread
    for h, recs in groups.items():
        pts = np.array([r['pos'] for r in recs])
        ax = int(np.argmax(pts.max(axis=0) - pts.min(axis=0))) if len(recs) > 1 else 0
        recs.sort(key=lambda r: r['pos'][ax])
    return groups

def quat_to_mat(q):
    x, y, z, w = q
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w),   2*(x*z+y*w)],
        [2*(x*y+z*w),   1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w),   2*(y*z+x*w),   1-2*(x*x+y*y)]])

def Raxis(k, a):
    c, s = math.cos(a), math.sin(a)
    if k == 0: return np.array([[1,0,0],[0,c,-s],[0,s,c]])
    if k == 1: return np.array([[c,0,s],[0,1,0],[-s,0,c]])
    return np.array([[c,-s,0],[s,c,0],[0,0,1]])

def fk_chain(recs, angles, axis):
    """angles: radians, one per record except last (tip). Returns joint positions."""
    pts = [recs[0]['pos'].copy()]
    R = quat_to_mat(recs[0]['quat'])
    for i, ang in enumerate(angles):
        R = R @ Raxis(axis, ang)
        Rb = quat_to_mat(recs[i]['quat'])
        seg_local = Rb.T @ (recs[i+1]['pos'] - recs[i]['pos'])
        pts.append(pts[-1] + R @ seg_local)
    return pts

# ---------------- yag ----------------
def load_yag(path):
    data = open(path, 'rb').read()
    assert data[:4] == b'YANM', path
    spt = struct.unpack('>f', data[0x3C:0x40])[0]
    tracks = []
    for r in range(29):
        o = 0x50 + r * 32
        h = u32(data, o)
        if h == 0: continue
        a, b, w28 = u32(data, o+4), u32(data, o+8), u32(data, o+28)
        tracks.append({'hash': h, 'a': a, 'b': b, 'w28': w28})
    return data, spt, tracks

def key_times(raw, ks, stride):
    """cumulative tick times for stride-byte keys (dt at byte 2)."""
    dts = [raw[i+2] for i in range(ks, len(raw), stride)]
    t = [0.0]
    for d in dts[:-1]: t.append(t[-1] + d)
    return np.array(t, float)

def sample_single(data, tr, t_mid):
    n = tr['w28']; ks = tr['b']
    raw = data[ks:ks + n * 5]
    if n == 1:
        return adeg(s16(raw, 0)), adeg(s16(raw, 3))
    t = key_times(raw, 0, 5)
    c1 = np.array([s16(raw, i) for i in range(0, len(raw), 5)], float)
    c2 = np.array([s16(raw, i+3) for i in range(0, len(raw), 5)], float)
    v1 = np.interp(t_mid, t, c1); v2 = np.interp(t_mid, t, c2)
    return adeg(v1), adeg(v2)

def sample_dual(data, tr, t_mid):
    ca, cb = tr['w28'] >> 16, tr['w28'] & 0xFFFF
    araw = data[tr['a']:tr['a'] + ca * 4]
    if ca > 4:  # 8B header, ca-2 keys (yanm_first8b_test.py rule)
        araw = araw[8:]
        nk = ca - 2
    else:
        nk = ca
    avals, adts = [], []
    for i in range(nk):
        avals.append(s16(araw, i*4)); adts.append(araw[i*4+2])
    ta = np.array([0.0] + list(np.cumsum(adts)[:-1]), float)
    A = np.interp(t_mid, ta, np.array(avals, float))
    Aang = adeg(A)
    braw = data[tr['b']:tr['b'] + cb * 5]
    if cb == 1:
        b1, b2 = adeg(s16(braw, 0)), adeg(s16(braw, 3))
    else:
        tb = key_times(braw, 0, 5)
        c1 = np.array([s16(braw, i) for i in range(0, len(braw), 5)], float)
        c2 = np.array([s16(braw, i+3) for i in range(0, len(braw), 5)], float)
        b1 = adeg(np.interp(t_mid, tb, c1)); b2 = adeg(np.interp(t_mid, tb, c2))
    return Aang + b1, Aang + b2

def clip_duration_ticks(data, tracks):
    tot = 0
    for tr in tracks:
        if tr['a'] == 0:
            n = tr['w28']; ks = tr['b']
            raw = data[ks:ks + n * 5]
            tot = max(tot, sum(raw[i+2] for i in range(0, len(raw), 5)))
    return tot

# ---------------- pose ----------------
LEG_HASHES = {0xBD5B2A59, 0xBD5B5259}

def pose_at(data, spt, tracks, groups, axismap, t_mid, leg_mode='asin'):
    """Returns dict hash -> list of joint positions (FK)."""
    out = {}
    for tr in tracks:
        h = tr['hash']
        if h not in groups:
            continue  # finger/toe/thumb/ECD/0C5B: no ycg records
        recs = groups[h]
        n = len(recs)
        axis = axismap.get('%08X' % h, {}).get('hinge_axis', 0)
        if tr['a'] == 0:
            a1, a2 = sample_single(data, tr, t_mid)
        else:
            a1, a2 = sample_dual(data, tr, t_mid)
        angs = [math.radians(a1)]
        if n >= 2:
            angs.append(math.radians(a2))
        # leg hip: optional half-angle decode variant
        if leg_mode == 'halfang' and h in LEG_HASHES and n == 3:
            pass  # handled by caller via raw channels if needed
        out[h] = fk_chain(recs, angs[:n-1], axis)
    return out

# ---------------- render ----------------
CHAIN_CLASS = {
    0xBD5B2A59: 'leg', 0xBD5B5259: 'leg',
    0x6198F425: 'arm', 0x6198F4D5: 'arm',
    0x613B7547: 'torso', 0x613B75B7: 'torso',
    0x099CD766: 'torso', 0x347D3654: 'torso',
    0x5B214D41: 'head', 0x5B214D4E: 'head',
}
CLASS_COLOR = {'leg': 'blue', 'arm': 'green', 'torso': 'black', 'head': 'red',
               'other': 'gray'}

def to_display(P):
    """ycg (x=up, y=lateral, z=fwd) -> display (x=fwd, y=lateral, z=up)."""
    P = np.asarray(P, float)
    return np.stack([P[:, 2], P[:, 1], P[:, 0]], axis=1)

def render_pose(pose, title, view, path, lim=60):
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='3d')
    for h, pts in pose.items():
        P = to_display(pts)
        cls = CHAIN_CLASS.get(h, 'other')
        ax.plot(P[:, 0], P[:, 1], P[:, 2], color=CLASS_COLOR[cls], lw=2.5)
        ax.scatter(P[:, 0], P[:, 1], P[:, 2], color=CLASS_COLOR[cls], s=18)
    ax.set_title(title, fontsize=9)
    allp = to_display([p for pts in pose.values() for p in pts])
    c = allp.mean(axis=0)
    ax.set_xlim(c[0]-lim, c[0]+lim); ax.set_ylim(c[1]-lim, c[1]+lim); ax.set_zlim(c[2]-lim, c[2]+lim)
    ax.view_init(elev=view[0], azim=view[1])
    ax.set_box_aspect((1, 1, 1))
    fig.tight_layout()
    fig.savefig(path, dpi=80)
    plt.close(fig)

# ---------- quantitative: is the ECD view near-optimal for action visibility?
ACTION_HASHES = [0xBD5B2A59, 0xBD5B5259, 0x6198F425, 0x6198F4D5,
                 0x5B214D41, 0x5B214D4E]

def project_pts(pts_d, elev, azim):
    """Orthographic projection of display-frame points from view (elev, azim).
    Returns (n,2) screen coords."""
    el, az = math.radians(elev), math.radians(azim)
    # camera looks from direction d toward origin
    d = np.array([math.cos(el)*math.cos(az), math.cos(el)*math.sin(az), math.sin(el)])
    # screen basis: right = normalize(cross(up0, d)) with up0=+z unless parallel
    up0 = np.array([0., 0., 1.])
    right = np.cross(up0, d)
    if np.linalg.norm(right) < 1e-9:
        right = np.array([1., 0., 0.])
    right /= np.linalg.norm(right)
    up = np.cross(d, right)
    P = np.asarray(pts_d, float)
    c = P.mean(axis=0)
    Pc = P - c
    return np.stack([Pc @ right, Pc @ up], axis=1)

def action_spread(pose, elev, azim):
    """Projected 2D variance of action-joint positions (display frame)."""
    pts = []
    for h in ACTION_HASHES:
        if h in pose:
            pts.extend(pose[h])
    if not pts:
        return 0.0
    S = project_pts(to_display(pts), elev, azim)
    return float(S.var(axis=0).sum())

def optimality(pose, ecd):
    """Grid-search views; report ECD view's spread vs best and percentile."""
    spreads = {}
    best = (-1, None)
    for el in range(0, 91, 10):
        for az in range(0, 360, 15):
            s = action_spread(pose, el, az)
            spreads[(el, az)] = s
            if s > best[0]:
                best = (s, (el, az))
    s_ecd = action_spread(pose, ecd[1], ecd[0])
    vals = sorted(spreads.values())
    pct = sum(1 for v in vals if v <= s_ecd) / len(vals)
    return {'ecd_spread': s_ecd, 'best_spread': best[0], 'best_view': best[1],
            'ecd_percentile': pct, 'ratio_to_best': s_ecd / best[0] if best[0] else 0.0}

def main():
    axismap = json.load(open(os.path.join(REPO, 'docs', 'yanm-task2-finish.json')))['axis_map']
    groups = load_ycg(os.path.join(SCRATCH, 'model__wrestler__000_0.ycg'))
    clips = {
        'c200_0a': 'ringmotion__c200_0a.yag',
        'c200_1a': 'ringmotion__c200_1a.yag',
        'c200_2a': 'ringmotion__c200_2a.yag',
        'FACE': 'viewer__motion__FACE.yag',
        'FIGHTING': 'viewer__motion__FIGHTING.yag',
        'showcase8503': 'viewer__motion__8503_0a.yag',
    }
    results = {}
    for name, fn in clips.items():
        data, spt, tracks = load_yag(os.path.join(SCRATCH, fn))
        ecd = next(t for t in tracks if t['hash'] == 0xECD28978)
        eraw = data[ecd['b']:ecd['b']+5]
        ech1, ech2 = adeg(s16(eraw, 0)), adeg(s16(eraw, 3))
        ticks = clip_duration_ticks(data, tracks)
        t_mid = ticks / 2.0
        pose = pose_at(data, spt, tracks, groups, axismap, t_mid)
        results[name] = {'ecd': [round(ech1, 1), round(ech2, 1)],
                         'ticks_total': ticks, 'sec_per_tick': spt,
                         't_mid_s': round(t_mid * spt, 3) if spt else None,
                         'n_groups_posed': len(pose)}
        views = {'ecd_view': (ech2, ech1), 'standard': (10, -60),
                 'front': (5, 0), 'top': (85, -60)}
        for vn, vv in views.items():
            p = os.path.join(OUTDIR, f'{name}_{vn}.png')
            render_pose(pose, f'{name} mid-frame t={t_mid:.0f}tk | {vn} elev={vv[0]:.1f} azim={vv[1]:.1f} | ECD=({ech1:.1f},{ech2:.1f})',
                        vv, p)
        opt = optimality(pose, (ech1, ech2))
        results[name]['optimality'] = {k: (round(v, 3) if isinstance(v, float) else v)
                                       for k, v in opt.items()}
        print(f'{name}: ECD=({ech1:.1f},{ech2:.1f}) ticks={ticks} groups={len(pose)} '
              f'pct={opt["ecd_percentile"]:.2f} ratio={opt["ratio_to_best"]:.2f} best={opt["best_view"]}')
        # per-track mid angles for the record
        ang = {}
        for tr in tracks:
            h = tr['hash']
            if h in groups:
                a1, a2 = sample_single(data, tr, t_mid) if tr['a'] == 0 else sample_dual(data, tr, t_mid)
                ang['%08X' % h] = [round(a1, 1), round(a2, 1)]
        results[name]['mid_angles_deg'] = ang
    json.dump(results, open(os.path.join(OUTDIR, 'metrics.json'), 'w'), indent=1)
    print('wrote', OUTDIR)

if __name__ == '__main__':
    main()
