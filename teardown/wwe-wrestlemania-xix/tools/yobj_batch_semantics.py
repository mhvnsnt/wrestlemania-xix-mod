#!/usr/bin/env python3
"""Item (a): YOBJ 16-byte batch table per-field semantics.
Measures on 000_0.ymg from ISO:
  - full dump of 58 records (u0,u1,b8,marker,variant,count)
  - count vs heuristic strip vertex/triangle counts (1:1 map hypothesis)
  - u0/u1 as offsets: read data there, check coordinate-range sanity
  - b8/marker/variant distribution vs strip properties
  - material-table linkage: 15 materials (20B recs) vs batch records
"""
import struct, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from yukes_fmt import stream_file, u32
from yobj_strips import load_000_0, split_strips
from yobj_strips import s16 as _s16

def u16(b, i): return struct.unpack('>H', b[i:i+2])[0]
def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]
def f32(b, i): return struct.unpack('>f', b[i:i+4])[0]

def batch_table(data):
    t = u32(data, 0x5C)
    recs, o = [], t
    while o + 16 <= len(data):
        r = data[o:o+16]
        b11 = r[11]; cnt = struct.unpack('>I', r[12:16])[0]
        if r[0] == 0 and b11 in (1, 2) and cnt < 20000:
            recs.append(dict(off=o, u0=u32(r,0), u1=u32(r,4), b8=r[8],
                             marker=r[9:11].hex(), variant=b11, count=cnt))
            o += 16
        else:
            break
    return t, recs

def main():
    data, size = stream_file('model/wrestler/000_0.ymg')
    t, recs = batch_table(data)
    print(f'batch table @{t:#x}, {len(recs)} records')
    print(' idx  off    u0        u1        b8  marker v  count')
    for i, r in enumerate(recs):
        print(f'{i:4d} {r["off"]:05X} {r["u0"]:08X} {r["u1"]:08X} '
              f'{r["b8"]:02X}  {r["marker"]}  {r["variant"]} {r["count"]:5d}')

    # u0 distinct values
    u0s = sorted(set(r['u0'] for r in recs))
    print('\ndistinct u0:', [f'{v:08X}' for v in u0s])
    u1s = sorted(set(r['u1'] for r in recs))
    print('distinct u1:', [f'{v:08X}' for v in u1s])
    b8s = sorted(set((r['b8'], r['marker'], r['variant']) for r in recs))
    print('distinct (b8,marker,variant):', [(f'{a:02X}',b,c) for a,b,c in b8s])

    # heuristic strips for comparison
    batches = load_000_0(data)
    allstrips = []
    for bi,(raw, strips) in enumerate(batches):
        for s in strips:
            allstrips.append((bi, len(s)))
    print(f'\nheuristic: {len(batches)} batches -> {len(allstrips)} strips; '
          f'vert sum={sum(c for _,c in allstrips)}, tri sum={sum(c-2 for _,c in allstrips)}')
    print('strip vert counts:', [c for _,c in allstrips])
    print('record counts:    ', [r['count'] for r in recs])

    # H: does record count == strip vertex count, in order?
    rc = [r['count'] for r in recs]
    sc = [c for _, c in allstrips]
    if len(rc) == len(sc):
        match = sum(1 for a,b in zip(rc,sc) if a==b)
        print(f'\nrecord-vs-strip count 1:1 positional match: {match}/{len(rc)}')
        # also try count == verts-2 (triangles), count == 2*verts etc.
        m2 = sum(1 for a,b in zip(rc,sc) if a==b-2)
        print(f'record count == strip tris (verts-2): {m2}/{len(rc)}')
    print('sum record counts:', sum(rc), ' sum strip verts:', sum(sc))

    # H: u0 as offset -> read count*6 bytes, check s16 coordinate sanity
    print('\n--- u0 as data-offset test ---')
    for base_name, base in [('file',0),('bulk(0x80)',0x80)]:
        ok = 0
        for r in recs[:10]:
            o = base + r['u0']
            if o + 6 > size: continue
            vals = [s16(data, o+i*2) for i in range(3)]
            inrange = all(-4000 <= v <= 4000 for v in vals)
            ok += inrange
        print(f'  base {base_name}: {ok}/10 records read as sane s16 coords at u0')

    # look at raw bytes at a couple of u0 locations
    print('\n--- raw bytes at u0=0x61C0 (+0x80 base) ---')
    o = 0x80 + 0x61C0
    print(' ', data[o:o+48].hex())
    print('--- raw bytes at file offset 0x61C0 ---')
    print(' ', data[0x61C0:0x61C0+48].hex())

    # material table @0x10704: 20B records, 15 materials
    print('\n--- material table @0x10704 ---')
    mo = 0x10704
    print(' header:', data[mo:mo+16].hex())
    nmat = 0
    for i in range(20):
        r = data[mo+4+i*20:mo+4+(i+1)*20]
        if not any(r): break
        nmat += 1
    print(' nonzero 20B records:', nmat)
    for i in range(min(nmat, 6)):
        r = data[mo+4+i*20:mo+4+(i+1)*20]
        print(f'  mat{i}:', r.hex())
    # idx chunks: u16 triplets referenced from mat records
    print('\n--- u16 idx chunks referenced by material recs (offsets rel 0x7CA0) ---')
    for i in range(min(nmat, 4)):
        r = data[mo+4+i*20:mo+4+(i+1)*20]
        idx_off = u16(r, 2)
        o = 0x7CA0 + idx_off
        chunk = [u16(data, o+j*2) for j in range(12)]
        print(f'  mat{i} idx_off={idx_off:#x} first12: {chunk}')

if __name__ == '__main__':
    main()
