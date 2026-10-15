#!/usr/bin/env python3
"""Render v2 retarget verification: YANM-side ycg FK vs T3-side schematic IK, side by side.
T3 schematic uses normalized-skeleton dims (arm 302+231, leg 449+446) and 2-bone IK."""
import json, sys, math
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

CH = json.load(open('docs/yanm_to_tekken3_v2.json'))
CN = CH['channel_names']
poses = np.array(CH['poses'], float)
FPS = CH['fps']

def ch(name): return CN.index(name)
# T3 base values
base = poses[0]  # not used directly; we use per-frame

# --- 2-bone IK ---
def ik2(S, W, a, b, bend):
    d = W - S; L = np.linalg.norm(d)
    L = np.clip(L, abs(a-b)+1e-6, a+b-1e-6)
    dn = d/np.linalg.norm(d)
    # bend: unit vector perpendicular-ish to dn, defines bend plane
    t = bend - dn*np.dot(bend, dn); t /= (np.linalg.norm(t)+1e-9)
    cosA = np.clip((L*L + a*a - b*b)/(2*L*a), -1, 1)
    sinA = math.sqrt(max(0, 1-cosA*cosA))
    E = S + a*(cosA*dn + sinA*t)
    return E

# T3 normalized skeleton schematic (root frame; x=up, y=forward, z=left)
# shoulder/hip anchors (from SKELETON_OFFSETS, hips frame approx = root frame)
SH_R = np.array([350., 0., -100.]); SH_L = np.array([350., 0., 100.])
HIP_R = np.array([-160., 0., 100.]); HIP_L = np.array([-160., 0., -100.])
# NOTE: doc offsets put R leg at z+; stance data shows R ankle z-; using doc offsets for anchors,
# IK targets are absolute so anchors only affect elbow/knee draw.
A_UP, A_LO = 302., 231.
L_UP, L_LO = 449., 446.
CHEST = np.array([300., 0., 0.]); HEAD = np.array([520., 0., 0.]); PELVIS = np.zeros(3)

def t3_skeleton(p):
    W = {}
    W['wrist_R'] = np.array([p[ch('ik0_x')], p[ch('ik0_y')], p[ch('ik0_z')]])
    W['wrist_L'] = np.array([p[ch('ik1_x')], p[ch('ik1_y')], p[ch('ik1_z')]])
    W['ankle_R'] = np.array([p[ch('ik2_x')], p[ch('ik2_y')], p[ch('ik2_z')]])
    W['ankle_L'] = np.array([p[ch('ik3_x')], p[ch('ik3_y')], p[ch('ik3_z')]])
    # elbows: bend back (-y) ; knees: bend forward (+y)
    W['elbow_R'] = ik2(SH_R, W['wrist_R'], A_UP, A_LO, np.array([0.,-1.,0.]))
    W['elbow_L'] = ik2(SH_L, W['wrist_L'], A_UP, A_LO, np.array([0.,-1.,0.]))
    W['knee_R'] = ik2(HIP_R, W['ankle_R'], L_UP, L_LO, np.array([0.,1.,0.]))
    W['knee_L'] = ik2(HIP_L, W['ankle_L'], L_UP, L_LO, np.array([0.,1.,0.]))
    return W

def draw(ax, W, title, color):
    segs = [(PELVIS, CHEST), (CHEST, HEAD),
            (SH_R, W['elbow_R']), (W['elbow_R'], W['wrist_R']),
            (SH_L, W['elbow_L']), (W['elbow_L'], W['wrist_L']),
            (HIP_R, W['knee_R']), (W['knee_R'], W['ankle_R']),
            (HIP_L, W['knee_L']), (W['knee_L'], W['ankle_L']),
            (HIP_R, HIP_L), (SH_R, SH_L)]
    for a, b in segs:
        ax.plot([a[0], b[0]], [a[1], b[1]], [a[2], b[2]], color=color, lw=2)
    pts = np.array([W['wrist_R'], W['wrist_L'], W['ankle_R'], W['ankle_L']])
    ax.scatter(pts[:,0], pts[:,1], pts[:,2], c='red', s=20)
    ax.set_title(title, fontsize=9)
    ax.set_xlim(-1000, 1000); ax.set_ylim(-1000, 1000); ax.set_zlim(-1000, 1000)
    ax.view_init(elev=10, azim=-60)

frames = [0, len(poses)//3, 2*len(poses)//3, len(poses)-1]
fig, axes = plt.subplots(2, 4, figsize=(20, 10), subplot_kw={'projection': '3d'})
for j, f in enumerate(frames):
    W = t3_skeleton(poses[f])
    draw(axes[0][j], W, f'T3 v2 frame {f} (t={f/FPS:.2f}s)', 'blue')
    # overlay trace: ankle_R path
plt.tight_layout()
plt.savefig('docs/retarget_v2_render.png', dpi=70)
print('saved docs/retarget_v2_render.png')

# also: top-down trace of ankle/wrist targets over time (motion path sanity)
fig2, ax2 = plt.subplots(1, 2, figsize=(12, 5))
ankR = np.array([[p[ch('ik2_x')], p[ch('ik2_y')], p[ch('ik2_z')]] for p in poses])
ankL = np.array([[p[ch('ik3_x')], p[ch('ik3_y')], p[ch('ik3_z')]] for p in poses])
wrR = np.array([[p[ch('ik0_x')], p[ch('ik0_y')], p[ch('ik0_z')]] for p in poses])
for ax, (pts, nm) in zip(ax2, [(ankR, 'ankles'), (wrR, 'wrists')]):
    ax.plot(pts[:, 1], pts[:, 0], lw=1, label=nm+'_R(y-fwd,x-up)')
    ax.set_title(nm + ' target path (side view: y=fwd, x=up)'); ax.legend(); ax.axis('equal')
plt.tight_layout(); plt.savefig('docs/retarget_v2_paths.png', dpi=80)
print('saved docs/retarget_v2_paths.png')
