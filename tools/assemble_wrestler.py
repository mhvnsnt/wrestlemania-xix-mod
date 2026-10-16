#!/usr/bin/env python3
"""Assemble a WMXIX wrestler YOBJ into a posed mesh.

Lane (a3) SKINNING ASSEMBLY for "WMXIX 100% Retail".

Takes a wrestler slot directory (e.g. teardown/wmxix/wrestlers/000/) OR a
.YMG file path, decodes the 13 skin batches via the a2-proven s16x3
triangle-strip decoder, applies batch->bone transforms from the 70-bone
skeleton, and writes an assembled OBJ + a verification render.

Status (2026-10-16): PARTIAL. Positions decode correctly (a2-proven).
Strip triangulation uses an improved 1300-raw-unit threshold (the a2
1000-unit heuristic splits at rail crossings ~1025, breaking strips;
true boundaries are isolated jumps >1300). The batch->bone mapping
(b0 -> bone) places batches near spine/face bones but does NOT yield
limbs; the true mapping is unresolved. See docs/YOBJ-SKINNING-A3-REPORT.md.

Usage:
    python3 tools/assemble_wrestler.py <slot_dir|ymg_path> [-o out.obj]
"""
import os, sys, json, struct
import numpy as np

# --- import the a2 decoder ---
_here = os.path.dirname(os.path.abspath(__file__))
_repo = os.path.dirname(_here)
_a2 = os.path.join(_repo, 'teardown', 'wwe-wrestlemania-xix', 'tools')
if _a2 not in sys.path:
    sys.path.insert(0, _a2)
from yobj_vertex_decode import get_batches, parse_yobj_header

SKEL_JSON = os.path.join(_repo, 'teardown', 'wwe-wrestlemania-xix',
                         'docs', 'wrestler-skeleton-000.json')
# Improved strip-split threshold (raw s16 units). a2 used 1000, but rail
# crossings within a strip are ~1025; true strip boundaries are isolated
# jumps >1300. (Measured on 000_0.ymg batch 3.)
STRIP_SPLIT_RAW = 1300.0


def strip_triangles(v, thresh_raw=STRIP_SPLIT_RAW):
    """Triangulate (N,3) strip-order verts, splitting at jumps > thresh."""
    thresh = thresh_raw / 64.0
    n = len(v)
    if n < 3:
        return np.zeros((0, 3), np.int32)
    dists = np.linalg.norm(v[1:] - v[:-1], axis=1)
    splits = [0] + [i + 1 for i, d in enumerate(dists) if d > thresh] + [n]
    tris = []
    for a, b in zip(splits[:-1], splits[1:]):
        m = b - a
        if m < 3:
            continue
        for i in range(m - 2):
            i0, i1, i2 = a + i, a + i + 1, a + i + 2
            tris.append((i0, i1, i2) if i % 2 == 0 else (i1, i0, i2))
    return np.array(tris, dtype=np.int32)


def load_skeleton():
    sk = json.load(open(SKEL_JSON))

    def Rx(a):
        c, s = np.cos(a), np.sin(a)
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

    def Ry(a):
        c, s = np.cos(a), np.sin(a)
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

    def Rz(a):
        c, s = np.cos(a), np.sin(a)
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    world = {}
    for b in sk:
        i, p = b['index'], b['parent']
        R = Rx(b['euler_xyz'][0]) @ Ry(b['euler_xyz'][1]) @ Rz(b['euler_xyz'][2])
        M = np.eye(4)
        M[:3, :3] = R
        M[:3, 3] = b['pos']
        world[i] = M if p == -1 else world[p] @ M
    return sk, world


# Batch->bone mapping. b0 is the batch record's first byte (0..12).
# Best-known mapping: b0 -> skeleton JSON bone b0 (YMG bone b0+1, accounting
# for the null sentinel at YMG slot 0). This places batches near the spine
# and face but does NOT resolve limb batches; the true mapping is OPEN.
# Override via --map "0:60,1:65,..." (batch_idx:bone_idx).
def default_bone_map(batches):
    return {i: b['b0'] for i, b in enumerate(batches)}


def assemble(ymg_bytes, bone_map=None):
    batches = get_batches(ymg_bytes)
    sk, world = load_skeleton()
    if bone_map is None:
        bone_map = default_bone_map(batches)
    verts_all, tris_all, parts = [], [], []
    voff = 0
    for i, b in enumerate(batches):
        v = b['verts']
        bone = bone_map.get(i, b['b0'])
        M = world[bone]
        w = (M @ np.hstack([v, np.ones((len(v), 1))]).T).T[:, :3]
        t = strip_triangles(v)
        verts_all.append(w)
        if len(t):
            tris_all.append(t + voff)
        parts.append({'batch': i, 'b0': b['b0'], 'bone': bone,
                      'bone_name': sk[bone]['name'], 'nverts': len(v),
                      'ntris': len(t)})
        voff += len(v)
    V = np.vstack(verts_all).astype(np.float32)
    T = np.vstack(tris_all).astype(np.int32) if tris_all else np.zeros((0, 3), np.int32)
    return V, T, parts


def write_obj(path, V, T):
    with open(path, 'w') as f:
        f.write('# WMXIX wrestler assembled by tools/assemble_wrestler.py (lane a3)\n')
        for v in V:
            f.write(f'v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n')
        for t in T:
            f.write(f'f {t[0]+1} {t[1]+1} {t[2]+1}\n')


def render(path, V, T, parts):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig = plt.figure(figsize=(18, 9))
    colors = plt.cm.tab20(np.linspace(0, 1, max(13, len(parts))))
    # per-part triangle ranges
    voff, troff = 0, 0
    ranges = []
    for p in parts:
        nv, nt = p['nverts'], p['ntris']
        ranges.append((voff, troff, nt, p))
        voff += nv
        troff += nt
    for j, (el, az, t) in enumerate([(10, -60, 'persp'), (5, -90, 'side X/Z'), (5, 0, 'front')]):
        ax = fig.add_subplot(1, 3, j + 1, projection='3d')
        for k, (v0, t0, nt, p) in enumerate(ranges):
            if nt:
                polys = V[T[t0:t0 + nt]]
                pc = Poly3DCollection(polys, alpha=0.9,
                                      facecolor=colors[k % 20], edgecolor='none')
                ax.add_collection3d(pc)
        ax.set_xlim(-100, 100)
        ax.set_ylim(-130, 30)
        ax.set_zlim(-30, 100)
        ax.view_init(elev=el, azim=az)
        ax.set_title(t)
    plt.suptitle('WMXIX wrestler assembly (lane a3) - b0->bone b0')
    plt.tight_layout()
    plt.savefig(path, dpi=85)
    print('render ->', path)


def resolve_ymg(slot_or_path):
    if os.path.isfile(slot_or_path):
        return open(slot_or_path, 'rb').read()
    # slot dir: look for <slot>_0.ymg, else fetch via range-iso
    base = os.path.basename(os.path.normpath(slot_or_path))
    cand = os.path.join(slot_or_path, f'{base}_0.ymg')
    if os.path.isfile(cand):
        return open(cand, 'rb').read()
    # fetch from ISO release via range-iso
    sys.path.insert(0, os.path.join(_repo, 'teardown', 'wwe-wrestlemania-xix', 'tools'))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'wmxix_range_iso',
        os.path.join(_repo, 'teardown', 'wwe-wrestlemania-xix', 'tools', 'wmxix_range_iso.py'))
    r = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r)
    spec2 = importlib.util.spec_from_file_location(
        'gcn_fst',
        os.path.join(_repo, 'teardown', 'wwe-wrestlemania-xix', 'tools', 'gcn_fst.py'))
    g = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(g)
    iso = r.RangeISO()
    h = g.read_header(iso)
    entries, name = g.read_entries(iso, h['fst_off'], h['fst_size'])
    want = f'model/wrestler/{base}_0.ymg'
    for p, isdir, o, l in g.flat_listing(entries, name):
        if p.strip('/') == want and not isdir:
            iso.seek(o)
            data = iso.read(l)
            # cache in slot dir for reuse
            os.makedirs(slot_or_path, exist_ok=True)
            open(cand, 'wb').write(data)
            return data
    raise FileNotFoundError(f'no YMG for slot {base}')


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('slot', help='slot dir (e.g. teardown/wmxix/wrestlers/000/) or .ymg path')
    ap.add_argument('-o', '--out', default=None, help='output OBJ path')
    ap.add_argument('--map', default=None,
                    help='batch->bone override, e.g. "0:60,1:65" (batch_idx:bone_idx)')
    ap.add_argument('--render', default=None, help='render PNG path')
    a = ap.parse_args()
    ymg = resolve_ymg(a.slot)
    print(f'YMG: {len(ymg)} bytes, magic={ymg[:4]}')
    bone_map = None
    if a.map:
        batches0 = get_batches(ymg)
        bone_map = {i: b['b0'] for i, b in enumerate(batches0)}
        for kv in a.map.split(','):
            bi, bone = kv.split(':')
            bone_map[int(bi)] = int(bone)
    V, T, parts = assemble(ymg, bone_map)
    print(f'assembled: {len(V)} verts, {len(T)} tris')
    for p in parts:
        print(f"  batch{p['batch']}: b0={p['b0']} -> bone {p['bone']} "
              f"({p['bone_name']}) n={p['nverts']} t={p['ntris']}")
    out = a.out or os.path.join(os.path.dirname(a.slot.rstrip('/')) if os.path.isdir(a.slot) else '/tmp',
                                'assembled.obj')
    if os.path.isdir(a.slot):
        out = os.path.join(a.slot, 'assembled.obj')
    write_obj(out, V, T)
    print('OBJ ->', out)
    rp = a.render or (os.path.join(a.slot, 'assembled.png') if os.path.isdir(a.slot) else '/tmp/assembled.png')
    render(rp, V, T, parts)


if __name__ == '__main__':
    main()
