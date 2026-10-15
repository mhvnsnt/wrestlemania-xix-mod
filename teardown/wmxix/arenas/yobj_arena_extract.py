#!/usr/bin/env python3
"""WMXIX arena YOBJ extractor.
Finds f32 vertex arrays and u16 index arrays, exports OBJ with faces.
Streams from ISO (disk-safe)."""
import struct, sys, os
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32, f32

def u16(b, i): return struct.unpack('>H', b[i:i+2])[0]

def find_vert_arrays(data, size):
    """Scan for f32-triplet vertex arrays."""
    arrays = []
    o = 0x80
    while o < size - 240:
        ok = True
        for t in range(5):
            vals = [f32(data, o+t*12+i*4) for i in range(3)]
            if not all(abs(v) < 20000 and (abs(v) > 0.0001 or v == 0) for v in vals):
                ok = False; break
            raw = data[o+t*12:o+t*12+12]
            if all(32 <= b < 127 or b == 0 for b in raw):
                try:
                    txt = raw.decode('ascii').strip('\x00')
                    if len(txt) >= 6 and txt.replace(' ','').replace('_','').replace('.','').isalnum():
                        ok = False; break
                except: pass
        if ok:
            e = o
            while e+12 < size:
                vals = [f32(data, e+i*4) for i in range(3)]
                if not all(abs(v) < 20000 for v in vals): break
                e += 12
            n = (e - o) // 12
            if n >= 20:
                arrays.append((o, n))
                o = e
                continue
        o += 4
    return arrays

def find_index_arrays(data, size, vert_arrays):
    """For each vert array, look for nearby u16 index buffers.
    Heuristic: u16 runs where max < total_verts and length is multiple of 3."""
    total_verts = sum(n for _, n in vert_arrays)
    # Build global vertex index base offsets
    # (each array is separate, so indices are per-array; we'll try global too)
    indices = []
    o = 0x80
    while o < size - 22:
        # check for u16 run: 10 consecutive u16s all < total_verts and non-zero mix
        vals = [u16(data, o+i*2) for i in range(10)]
        if all(v < total_verts for v in vals) and any(v > 0 for v in vals):
            # extend
            e = o
            while e+2 < size and u16(data, e) < total_verts:
                # stop at 0xFFFF sentinel runs or obvious non-index data
                e += 2
                if e - o > 100000: break
            n = (e - o) // 2
            if n >= 6 and n % 3 == 0:
                indices.append((o, n))
                o = e
                continue
        o += 2
    return indices

def extract_arena(iso_path, arena_path, outdir):
    data, size = stream_file(arena_path)
    print(f'{arena_path}: size={size}')
    verts = find_vert_arrays(data, size)
    print(f'  vert arrays: {len(verts)}, total={sum(n for _,n in verts)}')
    idx_arrays = find_index_arrays(data, size, verts)
    print(f'  index arrays: {len(idx_arrays)}')

    # Write OBJ with vertices (global indexing)
    os.makedirs(outdir, exist_ok=True)
    name = os.path.basename(arena_path).replace('.ymg', '')
    obj_path = os.path.join(outdir, f'{name}.obj')

    # Build global vertex list with base offsets
    all_verts = []
    array_bases = []
    for start, n in verts:
        array_bases.append(len(all_verts))
        for i in range(n):
            x = f32(data, start+i*12)
            y = f32(data, start+i*12+4)
            z = f32(data, start+i*12+8)
            all_verts.append((x, y, z))

    with open(obj_path, 'w') as f:
        f.write(f'# {arena_path} extracted from WMXIX\n')
        for x, y, z in all_verts:
            f.write(f'v {x:.2f} {y:.2f} {z:.2f}\n')
        # Write faces from index arrays (try global indexing)
        n_faces = 0
        for istart, in_ in idx_arrays:
            for t in range(in_ // 3):
                a = u16(data, istart+t*6)
                b = u16(data, istart+t*6+2)
                c = u16(data, istart+t*6+4)
                if a < len(all_verts) and b < len(all_verts) and c < len(all_verts):
                    # skip degenerate
                    if a != b and b != c and a != c:
                        f.write(f'f {a+1} {b+1} {c+1}\n')
                        n_faces += 1
    print(f'  wrote {obj_path}: {len(all_verts)} verts, {n_faces} faces')
    return obj_path, len(all_verts), n_faces

if __name__ == '__main__':
    arena = sys.argv[1] if len(sys.argv) > 1 else 'bg/00.ymg'
    outdir = sys.argv[2] if len(sys.argv) > 2 else '/tmp/wmxix_arenas'
    extract_arena(None, arena, outdir)
