#!/usr/bin/env python3
"""WMXIX arena YOBJ face index extractor — CRACKED 2026-10-13.

Format: 20-byte index records:
  [u16 a][u16 b][u16 c][u32 0xFFFFFFFF][u16 base][u16 d][u16 e][u32 0xFFFFFFFF]
  Triangle = (b+base, c+base, e+base) — global vertex indices.
  Field 'a' is constant per block (material/group ID). d==b in most records.

Validation: geometrically verified (median edge 1.0-1.3 units in ~5000-unit arena).
Status: format CRACKED, block discovery ongoing (249/10000+ tris found in bg/00).
"""
import struct, sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from yukes_fmt import stream_file
from yobj_arena_extract import find_vert_arrays

def u16(d, o): return struct.unpack('>H', d[o:o+2])[0]
def f32(d, o): return struct.unpack('>f', d[o:o+4])[0]

def extract_faces(iso_path, arena_path):
    data, size = stream_file(arena_path)
    verts = find_vert_arrays(data, size)
    all_verts = []
    for start, n in verts:
        for i in range(n):
            all_verts.append((f32(data, start+i*12), f32(data, start+i*12+4), f32(data, start+i*12+8)))
    NV = len(all_verts)
    
    def el(p, q):
        if p >= NV or q >= NV: return 999999
        return math.sqrt(sum((x-y)**2 for x, y in zip(all_verts[p], all_verts[q])))
    
    varray_ranges = [(s, s+n*12) for s, n in verts]
    def in_varray(o):
        for s, e in varray_ranges:
            if s-20 <= o < e: return True
        return False
    
    tris = []
    o = 0x80
    while o < size - 20:
        if in_varray(o):
            o += 2; continue
        b, c = u16(data, o+2), u16(data, o+4)
        sep1 = struct.unpack('>I', data[o+6:o+10])[0]
        base, e = u16(data, o+10), u16(data, o+14)
        sep2 = struct.unpack('>I', data[o+16:o+20])[0]
        if sep1 == 0xFFFFFFFF and sep2 == 0xFFFFFFFF:
            B, C, E = b+base, c+base, e+base
            if B < NV and C < NV and E < NV and len({B,C,E}) == 3:
                l = sorted([el(B,C), el(C,E), el(E,B)])
                if l[0] < 100 and l[1] < 100:
                    tris.append((B,C,E))
                    o += 20
                    continue
        o += 2
    return all_verts, tris

if __name__ == '__main__':
    arena = sys.argv[1] if len(sys.argv) > 1 else 'bg/00.ymg'
    out = sys.argv[2] if len(sys.argv) > 2 else '/tmp/wmxix_arenas/faces.obj'
    verts, tris = extract_faces(None, arena)
    with open(out, 'w') as f:
        f.write(f"# {arena} — faces CRACKED\n")
        for x, y, z in verts:
            f.write(f"v {x:.2f} {y:.2f} {z:.2f}\n")
        for a, b, c in tris:
            f.write(f"f {a+1} {b+1} {c+1}\n")
    print(f"{arena}: {len(verts)} verts, {len(tris)} faces -> {out}")
