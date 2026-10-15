#!/usr/bin/env python3
"""YOBJ /64 fixed-point validation script.
Extracts batch-table s16x3 vertices from model/wrestler/000_0.ymg (streamed
from ISO), dequantizes with /64 (precision 6), writes OBJ, renders a check
image with matplotlib. Also tries /32 and /16 for comparison."""
import struct, sys, os
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32

def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]

def extract_verts(data):
    """batch table @0x7CA0: 14 recs x 8B -> (bone, vcount, vert_off rel 0x80)"""
    verts = []
    for r in range(14):
        o = 0x7CA0 + r * 8
        bone, c1 = data[o], data[o+1]
        off = u32(data, o + 4)
        if c1 == 0:
            continue
        base = 0x80 + off
        for v in range(c1):
            x = s16(data, base + v*6)
            y = s16(data, base + v*6 + 2)
            z = s16(data, base + v*6 + 4)
            verts.append((x, y, z))
    return verts

def write_obj(path, verts, scale):
    with open(path, 'w') as f:
        for x, y, z in verts:
            f.write(f'v {x*scale:.4f} {y*scale:.4f} {z*scale:.4f}\n')

def render_check(outdir, verts):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
    except ImportError:
        print('matplotlib not available, skipping render')
        return
    for frac, name in [(4, 'div16'), (5, 'div32'), (6, 'div64')]:
        scale = 1.0 / (1 << frac)
        pts = [(x*scale, y*scale, z*scale) for x, y, z in verts]
        fig = plt.figure(figsize=(12, 4))
        for i, (ax1, ax2, title) in enumerate([
            (0, 1, 'front (xy)'), (0, 2, 'top (xz)'), (1, 2, 'side (yz)')]):
            ax = fig.add_subplot(1, 3, i+1)
            ax.scatter([p[ax1] for p in pts], [p[ax2] for p in pts], s=1)
            ax.set_aspect('equal'); ax.set_title(f'{name} {title}')
        fig.suptitle(f'frac={frac} (/{1<<frac}) n={len(pts)}')
        fig.savefig(os.path.join(outdir, f'vert_check_{name}.png'), dpi=80)
        plt.close(fig)
        # bbox
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; zs = [p[2] for p in pts]
        print(f'  {name}: x[{min(xs):.1f},{max(xs):.1f}] y[{min(ys):.1f},{max(ys):.1f}] z[{min(zs):.1f},{max(zs):.1f}]')

def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else '/tmp/yobj_validate'
    os.makedirs(outdir, exist_ok=True)
    print('streaming model/wrestler/000_0.ymg from ISO...')
    data, size = stream_file('model/wrestler/000_0.ymg')
    print(f'  size={size}')
    verts = extract_verts(data)
    print(f'  extracted {len(verts)} verts')
    for frac in (4, 5, 6):
        write_obj(os.path.join(outdir, f'verts_div{1<<frac}.obj'), verts, 1.0/(1<<frac))
    render_check(outdir, verts)
    print(f'  OBJs + check renders in {outdir}')

if __name__ == '__main__':
    main()
