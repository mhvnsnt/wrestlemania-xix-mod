#!/usr/bin/env python3
"""Extract all WMXIX arena vertex data as point-cloud OBJs.
Streams from ISO. Vertex format: f32 triplets (CRACKED 2026-10-13).
Face/index mapping: OPEN (documented in ARENA-FORMAT.md)."""
import struct, sys, os
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32, f32
from gcn_fst import read_header, read_entries, flat_listing

def find_vert_arrays(data, size):
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

def extract_one(arena_path, outdir):
    try:
        data, size = stream_file(arena_path)
    except SystemExit:
        print(f'  SKIP (not found): {arena_path}')
        return 0
    arrays = find_vert_arrays(data, size)
    total = sum(n for _, n in arrays)
    if total == 0:
        print(f'  {arena_path}: no verts found')
        return 0
    name = os.path.basename(arena_path).replace('.ymg', '')
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, f'{name}.obj'), 'w') as f:
        f.write(f'# {arena_path} - WMXIX arena vertices (f32, point cloud)\n')
        f.write(f'# {len(arrays)} arrays, {total} verts. Faces: see ARENA-FORMAT.md\n')
        for start, n in arrays:
            for i in range(n):
                x = f32(data, start+i*12)
                y = f32(data, start+i*12+4)
                z = f32(data, start+i*12+8)
                f.write(f'v {x:.2f} {y:.2f} {z:.2f}\n')
    print(f'  {arena_path}: {total} verts -> {name}.obj')
    return total

def main():
    iso = 'WWE Wrestlemania XIX (USA).iso'
    outdir = sys.argv[1] if len(sys.argv) > 1 else '/tmp/wmxix_arenas'
    # Get arena file list from ISO
    with open(iso, 'rb') as f:
        h = read_header(f)
        entries, names = read_entries(f, h['fst_off'], h['fst_size'])
        listing = flat_listing(entries, names)
    arenas = sorted(set(
        p for p, isdir, o, l in listing
        if '/bg/' in p and p.endswith('.ymg') and not isdir
        and '_light' not in p and '_scr' not in p and '_ent' not in p
        and '_gt' not in p and '_add' not in p and 'sc2' not in p
        and 'ight' not in p
    ))
    print(f'found {len(arenas)} main arena files')
    grand = 0
    for a in arenas:
        # strip leading //
        path = a.lstrip('/')
        grand += extract_one(path, outdir)
    print(f'\nTOTAL: {grand} verts across {len(arenas)} arenas -> {outdir}')

if __name__ == '__main__':
    main()
