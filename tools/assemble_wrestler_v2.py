#!/usr/bin/env python3
"""WMXIX Wrestler Assembly — WORKING solution (2026-10-17).

Assembles a coherent wrestler mesh from YMG files using the solved transform:
- Axis permutation (1,0,2): YMG stores Y-Z-X order, world = [p1, p0, p2]
- Bone scale: /100 (centimeters to meters)
- Vertex scale: /2500
- Translation-only: world_vert = vert_local + bone_world_pos
- Batch→bone mapping from material names

Usage:
    python3 tools/assemble_wrestler_v2.py <ymg_path> -o out.obj [--render out.png]
    python3 tools/assemble_wrestler_v2.py <slot_dir> -o out.obj  (uses <slot>_0.ymg)
"""

import os, sys, json, struct
import numpy as np

_here = os.path.dirname(os.path.abspath(__file__))
_repo = os.path.dirname(_here)
_a2 = os.path.join(_repo, 'teardown', 'wwe-wrestlemania-xix', 'tools')
if _a2 not in sys.path:
    sys.path.insert(0, _a2)
from yobj_vertex_decode import get_batches, parse_yobj_header, strip_triangles

SKEL_JSON = os.path.join(_repo, 'teardown', 'wwe-wrestlemania-xix',
                         'docs', 'wrestler-skeleton-000.json')

# Batch→bone mapping from material names (solved 2026-10-17)
# batch_idx: bone_name
BATCH_BONE_MAP = {
    0: 'Bip Spine1',    # hhh_body
    1: 'Bip L UpperArm', # hhh_arm
    2: 'Bip L Hand',    # hhh_hand
    3: 'Bip Pelvis',    # hhh_waists
    4: 'Bip L Thigh',   # hhh_l_leg
    5: 'Bip L Calf',    # hhh_knee
    6: 'Bip L Foot',    # hhh_foot
    7: 'Bip Head',      # head batches
    8: 'Bip Head',
    9: 'Bip Head',
    10: 'Bip Head',
    11: 'Bip Head',
    12: 'Bip Head',
}


def load_skeleton_fk():
    """Load skeleton and compute world positions via FK.
    
    Applies (1,0,2) permutation: world = [p1, p0, p2] / 100
    Translation-only FK (no rotation) per the solved method.
    """
    sk = json.load(open(SKEL_JSON))
    name2idx = {b['name']: b['index'] for b in sk}
    
    # Build children map
    children = {}
    for b in sk:
        p = b['parent']
        children.setdefault(p, []).append(b['index'])
    
    world = {}
    def fk(idx, parent_world):
        b = sk[idx]
        p = b['pos']
        # (1,0,2) permutation, /100 scale
        local = np.array([p[1], p[0], p[2]]) / 100.0
        w = parent_world + local
        world[idx] = w
        for c in children.get(idx, []):
            fk(c, w)
    
    fk(0, np.zeros(3))
    return sk, name2idx, world


def assemble(ymg_bytes, bone_map=None, vert_scale=2500.0):
    """Assemble YMG batches into world-space verts + tris.
    
    Returns (V, T, parts) where V is (N,3) float32, T is (M,3) int32.
    """
    batches = get_batches(ymg_bytes)
    sk, name2idx, world = load_skeleton_fk()
    
    if bone_map is None:
        bone_map = {}
        for i in range(len(batches)):
            bname = BATCH_BONE_MAP.get(i)
            if bname and bname in name2idx:
                bone_map[i] = name2idx[bname]
            else:
                # fallback to b0
                bone_map[i] = batches[i]['b0']
    
    verts_all, tris_all, parts = [], [], []
    voff = 0
    for i, b in enumerate(batches):
        # Raw verts are s16, scale /2500 (NOT /64 as in the decoder)
        raw = b['raw'].astype(np.float32)  # raw s16 values
        v_local = raw / vert_scale
        
        bone_idx = bone_map.get(i, b['b0'])
        bone_pos = world[bone_idx]
        
        # Translation-only: world = local + bone_pos
        w = v_local + bone_pos
        
        # Triangulate in local space (strip order)
        t = strip_triangles(v_local)
        
        verts_all.append(w)
        if len(t):
            tris_all.append(t + voff)
        parts.append({
            'batch': i, 'b0': b['b0'], 'bone': bone_idx,
            'bone_name': sk[bone_idx]['name'],
            'nverts': len(w), 'ntris': len(t),
            'bbox': [w.min(0).tolist(), w.max(0).tolist()],
        })
        voff += len(w)
    
    V = np.vstack(verts_all).astype(np.float32)
    T = np.vstack(tris_all).astype(np.int32) if tris_all else np.zeros((0, 3), np.int32)
    return V, T, parts


def write_obj(path, V, T):
    with open(path, 'w') as f:
        f.write('# WMXIX wrestler assembled by tools/assemble_wrestler_v2.py\n')
        for v in V:
            f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
        for t in T:
            f.write(f'f {t[0]+1} {t[1]+1} {t[2]+1}\n')
    print(f'OBJ -> {path} ({len(V)} verts, {len(T)} tris)')


def render_views(path, V, T, title='WMXIX wrestler'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    
    fig = plt.figure(figsize=(18, 6))
    # Auto-scale to data
    mn, mx = V.min(0), V.max(0)
    ctr = (mn + mx) / 2
    rng = max(mx - mn) * 0.6
    
    for j, (el, az, t) in enumerate([(10, -60, 'persp'), (0, -90, 'side'), (0, 0, 'front')]):
        ax = fig.add_subplot(1, 3, j + 1, projection='3d')
        if len(T):
            polys = V[T]
            pc = Poly3DCollection(polys, alpha=0.9, facecolor='tan', edgecolor='none')
            ax.add_collection3d(pc)
        ax.set_xlim(ctr[0]-rng, ctr[0]+rng)
        ax.set_ylim(ctr[1]-rng, ctr[1]+rng)
        ax.set_zlim(ctr[2]-rng, ctr[2]+rng)
        ax.view_init(elev=el, azim=az)
        ax.set_title(t)
    plt.suptitle(f'{title} ({len(V)}v/{len(T)}t, bbox [{mn[0]:.2f},{mn[1]:.2f},{mn[2]:.2f}]-[{mx[0]:.2f},{mx[1]:.2f},{mx[2]:.2f}])')
    plt.tight_layout()
    plt.savefig(path, dpi=85)
    print(f'render -> {path}')


def resolve_ymg(slot_or_path):
    if os.path.isfile(slot_or_path):
        return open(slot_or_path, 'rb').read()
    base = os.path.basename(os.path.normpath(slot_or_path))
    cand = os.path.join(slot_or_path, f'{base}_0.ymg')
    if os.path.isfile(cand):
        return open(cand, 'rb').read()
    raise FileNotFoundError(f'no YMG for {slot_or_path}')


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('slot', help='slot dir or .ymg path')
    ap.add_argument('-o', '--out', default='/tmp/wrestler.obj')
    ap.add_argument('--render', default=None)
    ap.add_argument('--vert-scale', type=float, default=2500.0)
    a = ap.parse_args()
    
    ymg = resolve_ymg(a.slot)
    print(f'YMG: {len(ymg)} bytes')
    V, T, parts = assemble(ymg, vert_scale=a.vert_scale)
    print(f'assembled: {len(V)} verts, {len(T)} tris')
    mn, mx = V.min(0), V.max(0)
    print(f'bbox: [{mn[0]:.3f},{mn[1]:.3f},{mn[2]:.3f}] - [{mx[0]:.3f},{mx[1]:.3f},{mx[2]:.3f}]')
    print(f'size: {mx-mn}')
    for p in parts:
        bb = p['bbox']
        print(f"  batch{p['batch']}: -> {p['bone_name']} n={p['nverts']} "
              f"y=[{bb[0][1]:.3f},{bb[1][1]:.3f}]")
    
    write_obj(a.out, V, T)
    if a.render:
        render_views(a.render, V, T)


if __name__ == '__main__':
    main()
