#!/usr/bin/env python3
"""WMXIX arena face reconstruction — PATH 1 (algorithmic surface reconstruction).

Reads point-cloud OBJs from teardown/wmxix/arenas/ (vertices only, no faces),
segments out non-position attribute arrays (normals/UVs the f32 scanner picked
up as 'vertices'), splits each position array into spatial components, and
reconstructs a real surface mesh per component with a deterministic cascade —
every face comes from a real algorithm, never hand-patched:

  1. GRID reconstruction — for axis-aligned structured grids (box parts, slabs:
     the ring's mat platform, posts). Connects grid-adjacent vertices into
     quads; outward winding from neighbor-occupancy. This recovers the true
     faces of grid-sampled parts.
  2. LOOP-STACK reconstruction — for components whose points form closed loops
     stacked along one axis (ropes, trim bands, skirts):
       * dense smooth loops (>=16 pts/level) that are curve-like (local-PCA
         linearity) -> TUBE mesh per loop (parallel-transport frames;
         radius = 0.25x point spacing — documented estimate, true rope radius
         is unrecoverable without the YMG)
       * faceted loops -> convex HULL if the part is a solid (all hull faces
         sampled), else BRIDGE band between consecutive loops
  3. GAP-SPLIT — recursively split the array at the largest 1D gap when it
     clearly separates two compact groups; reconstruct each piece.
  4. CONVEX HULL (Qhull) — for convex solids (box plates, slabs): accepted only
     when most points are hull vertices and nearly every hull triangle has
     sample points nearby.
  5. ALPHA SHAPE (Edelsbrunner; Delaunay-based, same family as CGAL): keep
     tetrahedra with circumsphere radius < alpha, boundary faces wound outward.
     Alpha swept over 2x/4x/8x/16x the characteristic point spacing.
  6. Points fallback — component documented for THREE.Points rendering with
     the reason (too sparse / thin / noisy for any method above).

A component is accepted from step 1-3 only with >=8 triangles, zero degenerate
faces, sane edge lengths, and coverage of most input points.

NOTE on open3d/Poisson: the original plan called for Open3D Poisson, but the
open3d wheel (~500MB) cannot be fetched on this VM in reasonable time, so the
pipeline runs on the present numpy/scipy stack (alpha shapes are an equally
real, peer-reviewed reconstruction algorithm).

Usage:
    reconstruct_arena_faces.py <in.obj> <out.obj>
    reconstruct_arena_faces.py --all   # all arenas -> teardown/wmxix/arenas/faces/

Output OBJ: mesh verts + f faces; header comment records method per component.
MANIFEST.json alongside: per-arena status / method / fallback reasons.
"""
import sys, os, math, json
import numpy as np
from scipy.spatial import Delaunay, cKDTree, QhullError
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components


# ---------------------------------------------------------------- IO / segment

def load_obj(path):
    v = []
    with open(path) as f:
        for line in f:
            if line.startswith('v '):
                p = line.split()
                v.append((float(p[1]), float(p[2]), float(p[3])))
    return np.asarray(v, dtype=np.float64)


def segment_arrays(v):
    """Split the concatenated cloud back into position arrays, dropping the
    attribute runs (long runs where every component has |c| < 3.0 — normal/UV
    arrays the f32 scanner picked up as 'vertices'). Returns (arrays, n_dropped)."""
    small = (np.abs(v) < 3.0).all(axis=1)
    runs = []
    i, n = 0, len(v)
    while i < n:
        j = i
        while j < n and small[j] == small[i]:
            j += 1
        runs.append((i, j, small[i]))
        i = j
    arrays, dropped = [], 0
    for s, e, is_small in runs:
        if is_small and (e - s) >= 8:
            dropped += (e - s)
            continue
        if is_small:
            continue
        arr = np.unique(np.round(v[s:e], 2), axis=0)
        if len(arr) >= 3:
            arrays.append(arr)
    return arrays, dropped


def knn_spacing(v, k=6):
    tree = cKDTree(v)
    idx = np.arange(len(v))
    if len(v) > 2000:
        idx = np.linspace(0, len(v) - 1, 2000).astype(int)
    dists, _ = tree.query(v[idx], k=k + 1)
    return float(np.median(dists[:, 1:]))


def subcluster(v, eps):
    tree = cKDTree(v)
    pairs = tree.sparse_distance_matrix(tree, max_distance=eps, output_type='coo_matrix')
    _, labels = connected_components(csgraph=csr_matrix(pairs), directed=False)
    return labels


# ---------------------------------------------------------------- validation

def mesh_stats(vv, faces, spacing, pts=None):
    if vv is None or len(faces) == 0:
        return None
    e = np.linalg.norm(vv[faces[:, 0]] - vv[faces[:, 1]], axis=1)
    e = np.concatenate([e, np.linalg.norm(vv[faces[:, 1]] - vv[faces[:, 2]], axis=1)])
    area2 = np.linalg.norm(np.cross(vv[faces[:, 1]] - vv[faces[:, 0]],
                                    vv[faces[:, 2]] - vv[faces[:, 0]]), axis=1)
    degen = int((area2 < 1e-9).sum())
    st = dict(tris=len(faces), verts=len(vv), degen=degen,
              med_edge=float(np.median(e)),
              edge_ratio=float(np.median(e) / spacing) if spacing > 0 else 0.0)
    if pts is not None:
        # bridge guard: triangles whose centroid floats far from any sample
        # point are spanning empty space (e.g. bridging two separate parts)
        cent = (vv[faces[:, 0]] + vv[faces[:, 1]] + vv[faces[:, 2]]) / 3.0
        tree = cKDTree(pts)
        d, _ = tree.query(cent, k=1)
        st['bridge_frac'] = float((d > 3.0 * spacing).mean())
    return st


def accept(vv, faces, spacing, n_in, pts=None):
    st = mesh_stats(vv, faces, spacing, pts)
    if st is None:
        return None
    if (st['tris'] >= 8 and st['degen'] == 0 and st['edge_ratio'] < 25.0
            and st['verts'] >= 0.3 * n_in
            and st.get('bridge_frac', 0.0) < 0.15):
        return st
    return None


# ---------------------------------------------------------------- 1. grid

def grid_reconstruct(v):
    r = np.round(v, 2)
    U = [np.unique(r[:, a]) for a in range(3)]
    if max(len(u) for u in U) > 64:
        return None, None
    gidx = [{x: i for i, x in enumerate(u)} for u in U]
    gi = np.array([tuple(gidx[a][x] for a, x in enumerate(p)) for p in r])
    occ = np.zeros([len(u) for u in U], dtype=bool)
    vert_at = {}
    for vi, key in enumerate(map(tuple, gi)):
        occ[key] = True
        vert_at[key] = vi
    # grid score: fraction of verts with >= 2 axis-neighbors
    nbr = np.zeros(len(r), dtype=int)
    for vi, (i, j, k) in enumerate(map(tuple, gi)):
        c = 0
        if i > 0 and occ[i - 1, j, k]: c += 1
        if i + 1 < occ.shape[0] and occ[i + 1, j, k]: c += 1
        if j > 0 and occ[i, j - 1, k]: c += 1
        if j + 1 < occ.shape[1] and occ[i, j + 1, k]: c += 1
        if k > 0 and occ[i, j, k - 1]: c += 1
        if k + 1 < occ.shape[2] and occ[i, j, k + 1]: c += 1
        nbr[vi] = c
    if (nbr >= 2).mean() < 0.55:
        return None, None
    tris = []
    nu, nv, nw = occ.shape
    for i in range(nu):
        for j in range(nv):
            for k in range(nw):
                if not occ[i, j, k]:
                    continue
                # xy quad (normal +-z)
                if i + 1 < nu and j + 1 < nv and occ[i + 1, j, k] and occ[i, j + 1, k] and occ[i + 1, j + 1, k]:
                    below = any(occ[i + di, j + dj, k - 1] for di in (0, 1) for dj in (0, 1)) if k > 0 else False
                    above = any(occ[i + di, j + dj, k + 1] for di in (0, 1) for dj in (0, 1)) if k + 1 < nw else False
                    if below and above:
                        continue
                    p00 = vert_at[(i, j, k)]; p10 = vert_at[(i + 1, j, k)]
                    p11 = vert_at[(i + 1, j + 1, k)]; p01 = vert_at[(i, j + 1, k)]
                    if below or not above:
                        tris += [(p00, p10, p11), (p00, p11, p01)]
                    else:
                        tris += [(p00, p11, p10), (p00, p01, p11)]
                # xz quad (normal +-y)
                if i + 1 < nu and k + 1 < nw and occ[i + 1, j, k] and occ[i, j, k + 1] and occ[i + 1, j, k + 1]:
                    below = any(occ[i + di, j - 1, k + dk] for di in (0, 1) for dk in (0, 1)) if j > 0 else False
                    above = any(occ[i + di, j + 1, k + dk] for di in (0, 1) for dk in (0, 1)) if j + 1 < nv else False
                    if below and above:
                        continue
                    p00 = vert_at[(i, j, k)]; p10 = vert_at[(i + 1, j, k)]
                    p11 = vert_at[(i + 1, j, k + 1)]; p01 = vert_at[(i, j, k + 1)]
                    if below or not above:  # outward -y : (p00,p01,p11),(p00,p11,p10)
                        tris += [(p00, p01, p11), (p00, p11, p10)]
                    else:
                        tris += [(p00, p10, p11), (p00, p11, p01)]
                # yz quad (normal +-x)
                if j + 1 < nv and k + 1 < nw and occ[i, j + 1, k] and occ[i, j, k + 1] and occ[i, j + 1, k + 1]:
                    below = any(occ[i - 1, j + dj, k + dk] for dj in (0, 1) for dk in (0, 1)) if i > 0 else False
                    above = any(occ[i + 1, j + dj, k + dk] for dj in (0, 1) for dk in (0, 1)) if i + 1 < nu else False
                    if below and above:
                        continue
                    p00 = vert_at[(i, j, k)]; p10 = vert_at[(i, j + 1, k)]
                    p11 = vert_at[(i, j + 1, k + 1)]; p01 = vert_at[(i, j, k + 1)]
                    if below or not above:  # outward -x
                        tris += [(p00, p11, p10), (p00, p01, p11)]
                    else:  # outward +x
                        tris += [(p00, p10, p11), (p00, p11, p01)]
    if not tris:
        return None, None
    faces = np.asarray(tris, dtype=np.int64)
    used, faces_re = np.unique(faces, return_inverse=True)
    return v[used], faces_re.reshape(-1, 3)


# ---------------------------------------------------------------- 2. loop stacks

def loopstack_levels(v):
    """Detect stacked closed loops along one axis. Returns (ax, levels, dropped)
    or None. levels = [(value, ordered_pts, median_step)]. A level passes when
    its angular ordering has no huge gap (star-shaped) and no step larger than
    60% of the loop diameter — tolerant of non-uniform sampling (dense corners,
    sparse straights). Scatter (non-loop) levels are rejected downstream by the
    curve-dimensionality gate in reconstruct_component."""
    r = np.round(v, 2)
    for ax in range(3):
        u = np.unique(r[:, ax])
        if len(u) > 8 or len(u) == 0:
            continue
        others = [a for a in range(3) if a != ax]
        levels, dropped, ok = [], 0, True
        for val in u:
            p = r[r[:, ax] == val]
            if len(p) < 6:
                dropped += len(p)
                continue
            q2 = p[:, others]
            c = q2.mean(0)
            ang = np.arctan2(q2[:, 1] - c[1], q2[:, 0] - c[0])
            srt = np.sort(ang)
            dang = np.diff(np.concatenate([srt, [srt[0] + 2 * np.pi]]))
            q = p[np.argsort(ang)]
            d = np.linalg.norm(np.diff(np.vstack([q, q[:1]]), axis=0), axis=1)
            diam = float(np.linalg.norm(np.ptp(q2, axis=0)))
            if dang.max() > np.radians(150) or d.max() > 0.6 * diam + 1e-9:
                ok = False
                break
            levels.append((val, q, float(np.median(d))))
        if ok and levels:
            return ax, sorted(levels, key=lambda t: t[0]), dropped
    return None


def curve_score(v):
    """Median local linearity (PCA): ~1 for curve-sampled points, lower for
    surface/volume sampling. Used to tell ropes (tubes) from scattered sheets."""
    n = len(v)
    k = min(12, n - 1)
    if k < 4:
        return 0.0
    tree = cKDTree(v)
    _, idx = tree.query(v, k=k + 1)
    nbrs = v[idx[:, 1:]] - v[:, None, :]
    cov = np.einsum('nij,nik->njk', nbrs, nbrs) / k
    w = np.linalg.eigvalsh(cov)  # ascending
    l1 = w[:, 2]
    lin = np.where(l1 > 1e-12, (w[:, 2] - w[:, 1]) / l1, 0.0)
    return float(np.median(lin))


def convex_solid_mesh(v, spacing):
    """Convex hull faces, accepted only when the part is truly a convex solid:
    most points are hull vertices AND nearly every hull triangle has sample
    points nearby (rejects hollow bands whose cap faces are unsampled)."""
    from scipy.spatial import ConvexHull
    n = len(v)
    if n < 8:
        return None, None
    try:
        hull = ConvexHull(v)
    except QhullError:
        return None, None
    hv = np.unique(hull.simplices)
    if len(hv) < 0.6 * n:
        return None, None  # too many interior points: concave or detail
    tris = hull.simplices  # (T,3)
    a, b, c = v[tris[:, 0]], v[tris[:, 1]], v[tris[:, 2]]
    pts = v[hv]
    covered = 0
    for t in range(len(tris)):
        ab, ac = b[t] - a[t], c[t] - a[t]
        nrm = np.cross(ab, ac)
        nl = np.linalg.norm(nrm)
        if nl < 1e-12:
            continue
        nrm /= nl
        dist = np.abs(np.dot(pts - a[t], nrm))
        near = pts[dist < 2.0 * spacing]
        if len(near) == 0:
            continue
        d00 = np.dot(ac, ac); d01 = np.dot(ac, ab); d11 = np.dot(ab, ab)
        denom = d00 * d11 - d01 * d01
        if abs(denom) < 1e-12:
            covered += 1
            continue
        ap = near - a[t]
        d20 = np.einsum('ij,j->i', ap, ac); d21 = np.einsum('ij,j->i', ap, ab)
        vv_ = (d11 * d20 - d01 * d21) / denom
        ww_ = (d00 * d21 - d01 * d20) / denom
        if ((vv_ >= -1e-9) & (ww_ >= -1e-9) & (vv_ + ww_ <= 1 + 1e-9)).any():
            covered += 1
    if covered < 0.9 * len(tris):
        return None, None  # hull faces unsampled: not a solid (e.g. hollow band)
    tris_re = np.searchsorted(hv, tris)  # remap to compacted hull-vertex array
    faces = orient_outward(v[hv], tris_re, v[hv].mean(0))
    used, faces_re = np.unique(faces, return_inverse=True)
    return v[hv][used], faces_re.reshape(-1, 3)


def resample_loop(q, N):
    n = len(q)
    out = np.empty((N, 3))
    for s in range(N):
        t = s / N * n
        i0 = int(t) % n
        i1 = (i0 + 1) % n
        f = t - int(t)
        out[s] = q[i0] * (1 - f) + q[i1] * f
    return out


def orient_outward(vv, faces, center):
    tris = np.asarray(faces, dtype=np.int64)
    a, b, c = vv[tris[:, 0]], vv[tris[:, 1]], vv[tris[:, 2]]
    n = np.cross(b - a, c - a)
    radial = (a + b + c) / 3.0 - center
    flip = np.einsum('ij,ij->i', n, radial) < 0
    tris[flip] = tris[flip][:, [0, 2, 1]]
    return tris


def bridge_mesh(q1, q2):
    N = max(len(q1), len(q2))
    A = resample_loop(q1, N)
    B = resample_loop(q2, N)
    vv = np.vstack([A, B])
    tris = []
    for s in range(N):
        s2 = (s + 1) % N
        tris += [(s, s2, N + s2), (s, N + s2, N + s)]
    center = vv.mean(0)
    return vv, orient_outward(vv, tris, center)


def tube_mesh(q, radius, sides=8):
    n = len(q)
    qp = np.vstack([q, q[:1]])
    tang = qp[2:-1] - qp[:-3]  # central differences for interior stations 1..n-2
    tang = np.vstack([q[1] - q[-1], tang, q[0] - q[-2]])
    tang /= np.linalg.norm(tang, axis=1, keepdims=True) + 1e-12
    # parallel-transport frame
    normals = np.empty_like(q)
    t0 = tang[0]
    ref = np.array([0.0, 1.0, 0.0]) if abs(t0[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    n0 = ref - t0 * np.dot(ref, t0)
    n0 /= np.linalg.norm(n0) + 1e-12
    normals[0] = n0
    for i in range(1, n):
        ni = normals[i - 1] - tang[i] * np.dot(normals[i - 1], tang[i])
        l = np.linalg.norm(ni)
        normals[i] = ni / (l + 1e-12) if l > 1e-9 else normals[i - 1]
    binorm = np.cross(tang, normals)
    theta = np.linspace(0, 2 * np.pi, sides, endpoint=False)
    ring = np.cos(theta)[None, :, None] * normals[:, None, :] + \
        np.sin(theta)[None, :, None] * binorm[:, None, :]
    vv = (q[:, None, :] + radius * ring).reshape(-1, 3)
    tris = []
    for s in range(n):
        s2 = (s + 1) % n
        for m in range(sides):
            m2 = (m + 1) % sides
            a, b, c, d = s * sides + m, s2 * sides + m, s2 * sides + m2, s * sides + m2
            tris += [(a, b, c), (a, c, d)]
    return vv, np.asarray(tris, dtype=np.int64)


def loopstack_mesh(v, ax, levels):
    """Dense smooth loops -> tubes (ropes/cables); faceted loops -> bridge bands."""
    avg_pts = np.mean([len(q) for _, q, _ in levels])
    parts = []
    if len(levels) == 1 or avg_pts >= 16:
        for _, q, med in levels:
            radius = max(8.0, 0.25 * med)
            parts.append(tube_mesh(q, radius) + (f"tube(r={radius:.0f})",))
    else:
        for i in range(len(levels) - 1):
            parts.append(bridge_mesh(levels[i][1], levels[i + 1][1]) + ("bridge",))
    # merge parts
    vv_all, faces_all, base, notes = [], [], 0, []
    for vv, faces, note in parts:
        vv_all.append(vv)
        faces_all.append(faces + base)
        base += len(vv)
        notes.append(note)
    return np.vstack(vv_all), np.vstack(faces_all), notes


# ---------------------------------------------------------------- 3. alpha shape

def circumradii(pts, tets):
    a = pts[tets[:, 0]]
    b = pts[tets[:, 1]] - a
    c = pts[tets[:, 2]] - a
    d = pts[tets[:, 3]] - a
    A = np.stack([b, c, d], axis=1) * 2.0
    rhs = np.stack([np.einsum('ij,ij->i', b + a, b),
                    np.einsum('ij,ij->i', c + a, c),
                    np.einsum('ij,ij->i', d + a, d)], axis=1)
    vol6 = np.abs(np.einsum('ti,ti->t', b, np.cross(c, d)))
    ok = vol6 > 1e-9
    R = np.full(len(tets), np.inf)
    if ok.any():
        try:
            centers = np.linalg.solve(A[ok], rhs[ok]) + a[ok]
        except np.linalg.LinAlgError:
            return R
        R[ok] = np.linalg.norm(centers - a[ok], axis=1)
    return R


def alpha_shape_mesh(v, alpha):
    try:
        tri = Delaunay(v)
    except QhullError:
        try:
            tri = Delaunay(v, qhull_options='QJ')
        except QhullError:
            return None, None
    tets = tri.simplices
    if len(tets) == 0:
        return None, None
    R = circumradii(v, tets)
    keep = R < alpha
    if not keep.any():
        return None, None
    tets = tets[keep].copy()
    a, b, c, d = v[tets[:, 0]], v[tets[:, 1]], v[tets[:, 2]], v[tets[:, 3]]
    vol6 = np.einsum('ti,ti->t', b - a, np.cross(c - a, d - a))
    neg = vol6 < 0
    tets[neg][:, [1, 2]] = tets[neg][:, [2, 1]]
    faces = np.concatenate([
        tets[:, [1, 2, 3]], tets[:, [0, 3, 2]],
        tets[:, [0, 1, 3]], tets[:, [0, 2, 1]]], axis=0)
    key = np.sort(faces, axis=1)
    _, inv, counts = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    bnd = faces[counts[inv] == 1]
    if len(bnd) == 0:
        return None, None
    used, faces_re = np.unique(bnd, return_inverse=True)
    return v[used], faces_re.reshape(-1, 3)


# ---------------------------------------------------------------- cascade

def gap_split(arr, min_size=12):
    """Split an array at the largest 1D gap, when the gap clearly separates two
    compact groups (gap > 1.5x the larger piece's extent along that axis).
    Returns a list of pieces (recursively split). Guards against splitting a
    single loop whose straight sections are unsampled: such splits are only
    valid when the pieces themselves are compact relative to the gap."""
    if len(arr) < 2 * min_size:
        return [arr]
    best = None
    for ax in range(3):
        u = np.sort(np.unique(np.round(arr[:, ax], 1)))
        gaps = np.diff(u)
        if len(gaps) == 0:
            continue
        i = int(np.argmax(gaps))
        left = arr[:, ax] <= u[i]
        right = arr[:, ax] > u[i]
        if left.sum() < min_size or right.sum() < min_size:
            continue
        dla = float(arr[left][:, ax].max() - arr[left][:, ax].min())
        dra = float(arr[right][:, ax].max() - arr[right][:, ax].min())
        if gaps[i] > 1.5 * max(dla, dra) and gaps[i] > 8 * np.median(gaps):
            if best is None or gaps[i] > best[0]:
                best = (float(gaps[i]), ax, float(u[i]))
    if best is None:
        return [arr]
    _, ax, val = best
    return gap_split(arr[arr[:, ax] <= val], min_size) + \
        gap_split(arr[arr[:, ax] > val], min_size)


def reconstruct_component(v, allow_alpha=True, depth=0):
    """Cascade: grid -> loopstack (tube/bridge/hull) -> gap-split & recurse ->
    convex hull -> alpha_shape -> points fallback. Grid/loopstack/hull work
    from ~8 points; alpha_shape needs >= 12."""
    n = len(v)
    if n < 8:
        return None, None, "points", None, f"too sparse ({n} verts)"
    spacing = knn_spacing(v)
    if spacing <= 0:
        return None, None, "points", None, "degenerate spacing"
    vv, faces = grid_reconstruct(v)
    st = accept(vv, faces, spacing, n, v)
    if st is not None:
        return vv, faces, "grid", st, None
    ls = loopstack_levels(v)
    if ls is not None:
        ax, levels, dropped = ls
        avg_pts = np.mean([len(q) for _, q, _ in levels])
        if avg_pts >= 16:
            if curve_score(v) > 0.6:
                vv, faces, notes = loopstack_mesh(v, ax, levels)
                st = accept(vv, faces, spacing, n - dropped, v)
                if st is not None:
                    return vv, faces, f"loopstack({';'.join(notes)})", st, None
            # dense but not curve-like: scattered sheets, not ropes — fall through
        else:
            vv, faces = convex_solid_mesh(v, spacing)
            st = accept(vv, faces, spacing, n, v)
            if st is not None:
                return vv, faces, "convex_hull", st, None
            vv, faces, notes = loopstack_mesh(v, ax, levels)
            st = accept(vv, faces, spacing, n - dropped, v)
            if st is not None:
                extra = f" dropped_pts={dropped}" if dropped else ""
                return vv, faces, f"loopstack({';'.join(notes)}){extra}", st, None
    if depth < 3:
        pieces = gap_split(v)
        if len(pieces) > 1:
            out_vv, out_faces, base, notes = [], [], 0, []
            ok = True
            for pc in pieces:
                pvv, pfaces, pmethod, pst, _ = reconstruct_component(
                    pc, allow_alpha=True, depth=depth + 1)
                if pvv is None:
                    ok = False
                    break
                out_vv.append(pvv)
                out_faces.append(np.asarray(pfaces) + base)
                base += len(pvv)
                notes.append(f"{len(pc)}pts:{pmethod}")
            if ok:
                vv = np.vstack(out_vv)
                faces = np.vstack(out_faces)
                st = accept(vv, faces, spacing, n, v)
                if st is not None:
                    return vv, faces, f"gap_split({';'.join(notes)})", st, None
    vv, faces = convex_solid_mesh(v, spacing)
    st = accept(vv, faces, spacing, n, v)
    if st is not None:
        return vv, faces, "convex_hull", st, None
    if allow_alpha and n >= 12:
        for mult in (2.0, 4.0, 8.0, 16.0):
            alpha = mult * spacing
            vv, faces = alpha_shape_mesh(v, alpha)
            st = accept(vv, faces, spacing, n, v)
            if st is not None:
                return vv, faces, f"alpha_shape(alpha={alpha:.1f})", st, None
    return None, None, "points", None, \
        "grid/loopstack/gapsplit/hull/alpha_shape all rejected — thin/noisy/sparse"


def process(in_path, out_path):
    v = load_obj(in_path)
    arrays, dropped = segment_arrays(v)
    report = dict(input=os.path.basename(in_path), total_verts=len(v),
                  dropped_attr=int(dropped), arrays=len(arrays), components=[])
    if not arrays:
        report['status'] = 'points'
        report['reason'] = 'no position data (all attribute arrays)'
        return report
    meshes = []
    for ai, arr in enumerate(arrays):
        # 1) try the whole array first — arrays are the file's natural units
        vv, faces, method, st, reason = reconstruct_component(arr)
        if vv is not None:
            entry = dict(array=ai, method=method, n=int(len(arr)))
            entry.update(tris=st['tris'], mesh_verts=st['verts'],
                         med_edge=round(st['med_edge'], 2))
            meshes.append((vv, faces, entry))
            report['components'].append(entry)
            continue
        # 2) whole array failed: sub-cluster large arrays and retry per piece
        if len(arr) >= 48:
            spacing = knn_spacing(arr)
            diag = float(np.linalg.norm(arr.max(0) - arr.min(0)))
            eps = max(4.0 * spacing, 0.005 * diag)
            labels = subcluster(arr, eps)
            for lab in sorted(set(labels.tolist())):
                comp = arr[labels == lab]
                if len(comp) < 8:
                    report['components'].append(dict(array=ai, method='points',
                                                     n=int(len(comp)),
                                                     reason='tiny fragment'))
                    continue
                vv, faces, method, st, reason = reconstruct_component(comp)
                entry = dict(array=ai, sub=int(lab), method=method, n=int(len(comp)))
                if vv is not None:
                    entry.update(tris=st['tris'], mesh_verts=st['verts'],
                                 med_edge=round(st['med_edge'], 2))
                    meshes.append((vv, faces, entry))
                else:
                    entry['reason'] = reason
                report['components'].append(entry)
        else:
            report['components'].append(dict(array=ai, method='points',
                                             n=int(len(arr)), reason=reason))
    n_mesh = sum(1 for c in report['components'] if c['method'] != 'points')
    report['status'] = 'mesh' if meshes else 'points'
    report['mesh_components'] = n_mesh
    if not meshes:
        return report
    out_verts, out_faces = [], []
    base = 0
    # per-part OBJs (parts live in different local frames; the integrator
    # positions them) + one merged OBJ
    partdir = os.path.join(os.path.dirname(out_path), 'parts')
    os.makedirs(partdir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(in_path))[0]
    for pi, (vv, faces, entry) in enumerate(meshes):
        vv = np.asarray(vv); faces = np.asarray(faces)
        with open(os.path.join(partdir, f"{stem}_p{pi}.obj"), 'w') as f:
            f.write(f"# {stem} part {pi} — {entry.get('method')}\n")
            for x, y, z in vv:
                f.write(f"v {x:.2f} {y:.2f} {z:.2f}\n")
            for a, b, c in faces + 1:
                f.write(f"f {int(a)} {int(b)} {int(c)}\n")
        out_verts.extend(vv.tolist())
        out_faces.extend((faces + base + 1).tolist())
        base += len(vv)
    with open(out_path, 'w') as f:
        f.write(f"# {os.path.basename(in_path)} — WMXIX arena mesh, faces reconstructed\n")
        f.write(f"# pipeline: teardown/wmxix/tools/reconstruct_arena_faces.py "
                f"(grid / loopstack / alpha-shape cascade per component)\n")
        f.write(f"# components: {json.dumps(report['components'])}\n")
        for x, y, z in out_verts:
            f.write(f"v {x:.2f} {y:.2f} {z:.2f}\n")
        for a, b, c in out_faces:
            f.write(f"f {int(a)} {int(b)} {int(c)}\n")
    report['out_verts'] = len(out_verts)
    report['out_faces'] = len(out_faces)
    report['out_path'] = out_path
    return report


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('inp', nargs='?')
    ap.add_argument('outp', nargs='?')
    ap.add_argument('--all', action='store_true')
    args = ap.parse_args()
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    arenadir = os.path.join(repo, 'teardown', 'wmxix', 'arenas')
    facesdir = os.path.join(arenadir, 'faces')
    os.makedirs(facesdir, exist_ok=True)
    manifest = {}
    if args.all:
        jobs = [(os.path.join(arenadir, f), os.path.join(facesdir, f))
                for f in sorted(os.listdir(arenadir)) if f.endswith('.obj')]
    else:
        jobs = [(args.inp, args.outp)]
    for inp, outp in jobs:
        print(f"--- {os.path.basename(inp)}", flush=True)
        try:
            report = process(inp, outp)
        except Exception:
            import traceback
            traceback.print_exc()
            report = dict(input=os.path.basename(inp), status='error',
                          reason='exception, see log')
        manifest[os.path.basename(inp)] = report
        print(f"  status={report.get('status')} faces={report.get('out_faces', '-')} "
              f"comps={len(report.get('components', []))}", flush=True)
    with open(os.path.join(facesdir, 'MANIFEST.json'), 'w') as f:
        json.dump(manifest, f, indent=1)
    n_mesh = sum(1 for r in manifest.values() if r.get('status') == 'mesh')
    n_pts = sum(1 for r in manifest.values() if r.get('status') == 'points')
    print(f"\nDONE: {n_mesh} mesh, {n_pts} points-fallback, "
          f"{len(manifest) - n_mesh - n_pts} error")


if __name__ == '__main__':
    main()
