#!/usr/bin/env python3
"""YOBJ triangle connectivity via triangle strips.

FINDING (2026-10-13, verified by eye): WMXIX YOBJ meshes do NOT use separate
index buffers. Triangles are formed implicitly by TRIANGLE STRIPS: the vertex
runs are strip-ordered (ladder/zigzag), and each maximal run between
separator/jump verts forms one strip. Triangles = consecutive triples
(v_i, v_{i+1}, v_{i+2}) within a strip.

Evidence:
- Vertex runs show ladder structure (alternating rails, e.g. elbow verts
  0-21: x descending 956->28 on even/odd rails).
- Consecutive-vertex distance is bimodal: intra-strip steps (~100-200 raw
  units) vs inter-strip jumps (800-2100). Splitting at jumps yields strips
  that each render as a smooth surface patch (verified visually).
- Separator verts are single near-origin verts (e.g. (35,0,19), (0,0,0))
  between strips; they are not part of any triangle.
- The "dense u16 runs" found in file gaps are NOT index buffers (they
  contain coordinate-scale values and zero runs); no valid index buffer
  referencing the vertex list was found anywhere in the file.

OPEN: strips render smooth individually but scattered globally -- the vertex
positions need per-strip/per-vertex skinning transforms (bone matrices) to
assemble. That is a vertex-position issue, not connectivity.

Usage:
  python3 tools/yobj_strips.py elbow        # elbow part -> OBJ + render
  python3 tools/yobj_strips.py 000_0       # wrestler 000 part 0 -> OBJ + render
Streams from ISO (disk-safe). OBJs written to /tmp/yobj_tri/ by default.
"""
import struct, sys, math, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from yukes_fmt import stream_file, u32

def u16(b, i): return struct.unpack('>H', b[i:i+2])[0]
def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]
def dist(a, b): return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

def split_strips(raw):
    """Split a vertex run into triangle strips at jump boundaries.

    Edge lengths are bimodal: intra-strip steps vs inter-strip jumps.
    Threshold = max(400, 4x median): safely above intra-strip steps,
    safely below jumps. Over-splitting is harmless (smooth sub-strips);
    under-splitting would create stretched triangles, so we err low.
    """
    n = len(raw)
    if n < 3: return []
    ds = sorted(dist(raw[i], raw[i + 1]) for i in range(n - 1))
    TH = max(400, ds[len(ds) // 2] * 4)
    bnd = [i for i in range(n - 1) if dist(raw[i], raw[i + 1]) > TH]
    strips, start = [], 0
    for i in bnd + [n - 1]:
        run = list(range(start, i + 1))
        if len(run) >= 3:
            strips.append(run)
        start = i + 1
    return strips

def load_elbow(data):
    raw = [(u16(data, 0x4D8 + i * 6), u16(data, 0x4D8 + i * 6 + 2),
            u16(data, 0x4D8 + i * 6 + 4)) for i in range(148)]
    return [(raw, split_strips(raw))]

def load_000_0(data):
    out = []
    for r in range(1, 14):
        o = 0x7CA0 + r * 8
        c1, off = data[o + 1], u32(data, o + 4)
        if c1 == 0: continue
        base = 0x80 + off
        raw = [(s16(data, base + i * 6), s16(data, base + i * 6 + 2),
                s16(data, base + i * 6 + 4)) for i in range(c1)]
        out.append((raw, split_strips(raw)))
    return out

def write_obj(path, batches, scale=1.0 / 64):
    verts, tris = [], []
    for raw, strips in batches:
        bi = len(verts)
        verts.extend(raw)
        for s in strips:
            for i in range(len(s) - 2):
                tris.append((bi + s[i] + 1, bi + s[i + 1] + 1, bi + s[i + 2] + 1))
    with open(path, 'w') as f:
        for x, y, z in verts:
            f.write(f'v {x * scale:.4f} {y * scale:.4f} {z * scale:.4f}\n')
        for a, b, c in tris:
            f.write(f'f {a} {b} {c}\n')
    return len(verts), len(tris), sum(len(ss) for _, ss in batches)

def render(path, batches, title, scale=1.0 / 64):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import matplotlib.cm as cm
    verts = [[(x * scale, y * scale, z * scale) for x, y, z in raw] for raw, _ in batches]
    fig = plt.figure(figsize=(12, 5))
    for k, (elev, azim) in enumerate([(15, -60), (15, 120)]):
        ax = fig.add_subplot(1, 2, k + 1, projection='3d')
        si = 0
        for bi, (raw, strips) in enumerate(batches):
            v = verts[bi]
            for s in strips:
                polys = [[v[a], v[b], v[c]] for a, b, c in zip(s, s[1:], s[2:])]
                ax.add_collection3d(Poly3DCollection(
                    polys, alpha=0.9, facecolor=cm.tab20(si % 20), edgecolor='none'))
                si += 1
        allv = [p for v in verts for p in v]
        xs = [p[0] for p in allv]; ys = [p[1] for p in allv]; zs = [p[2] for p in allv]
        ax.set_xlim(min(xs), max(xs)); ax.set_ylim(min(ys), max(ys)); ax.set_zlim(min(zs), max(zs))
        ax.view_init(elev=elev, azim=azim)
    fig.suptitle(title)
    fig.savefig(path, dpi=70); plt.close(fig)

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else 'elbow'
    outdir = sys.argv[2] if len(sys.argv) > 2 else '/tmp/yobj_tri'
    os.makedirs(outdir, exist_ok=True)
    if which == 'elbow':
        data, _ = stream_file('edit_data/MODEL/Man/Elbow/me0_000/l0.ymg')
        batches = load_elbow(data)
    else:
        data, _ = stream_file('model/wrestler/000_0.ymg')
        batches = load_000_0(data)
    nv, nt, ns = write_obj(f'{outdir}/{which}_strips.obj', batches)
    print(f'{which}: {nv} verts, {ns} strips, {nt} tris -> {outdir}/{which}_strips.obj')
    render(f'{outdir}/{which}_strips.png', batches, f'{which}: {nt} tris in {ns} strips')

if __name__ == '__main__':
    main()
