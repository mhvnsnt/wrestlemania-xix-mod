#!/usr/bin/env python3
"""YOBJ batch-block diagnostic: are targets s16 positions or u16 index triplets?
Also scans for candidate position arrays."""
import struct, sys
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32

def u16(b, i): return struct.unpack('>H', b[i:i+2])[0]
def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]
def s8(b, i): return struct.unpack('b', b[i:i+1])[0]

def main():
    data, size = stream_file('model/wrestler/000_0.ymg')
    print(f'file size: {size}')

    # Batch table @0x7CA0, 14 recs x 8B
    print('\n=== batch records ===')
    for r in range(14):
        o = 0x7CA0 + r * 8
        bone, c1, z, c2, off = data[o], data[o+1], data[o+2], data[o+3], u32(data, o+4)
        if c1 == 0:
            continue
        base = 0x80 + off
        print(f'rec{r}: bone={bone} count={c1} base=0x{base:05X}')
        # first 3 triplets as s16x3 and u16x3
        for t in range(min(3, c1)):
            to = base + t * 6
            s = (s16(data, to), s16(data, to+2), s16(data, to+4))
            u = (u16(data, to), u16(data, to+2), u16(data, to+4))
            print(f'   t{t}: s16={s}  u16={u}')

    # Check: do u16 values look like sequential indices?
    print('\n=== u16 triplet stats across all batches ===')
    allu = []
    for r in range(14):
        o = 0x7CA0 + r * 8
        c1 = data[o+1]
        if c1 == 0:
            continue
        base = 0x80 + u32(data, o+4)
        for t in range(c1):
            to = base + t * 6
            allu.extend([u16(data, to), u16(data, to+2), u16(data, to+4)])
    print(f'  n={len(allu)} min={min(allu)} max={max(allu)}')
    # histogram of small values
    import collections
    c = collections.Counter(allu)
    print(f'  unique={len(c)} top10={c.most_common(10)}')

    # Scan bulk region 0x80-0x7CA0 for s8 runs that could be positions
    print('\n=== bulk region scan (0x80 to 0x7CA0) ===')
    # Find the batch data extents
    lo, hi = size, 0
    for r in range(14):
        o = 0x7CA0 + r * 8
        c1 = data[o+1]
        if c1 == 0:
            continue
        base = 0x80 + u32(data, o+4)
        lo = min(lo, base); hi = max(hi, base + c1*6)
    print(f'  batch data covers 0x{lo:05X}-0x{hi:05X}')
    # what's between 0x80 and lo?
    print(f'  gap 0x80-0x{lo:05X} ({lo-0x80} bytes): first 32 bytes hex:')
    print(f'    {data[0x80:0x80+32].hex()}')
    # what's after hi up to 0x7CA0?
    print(f'  gap 0x{hi:05X}-0x7CA0 ({0x7CA0-hi} bytes): nonzero fraction:')
    nz = sum(1 for i in range(hi, 0x7CA0) if data[i])
    print(f'    nonzero={nz}/{0x7CA0-hi} = {100*nz/(0x7CA0-hi):.1f}%')

if __name__ == '__main__':
    main()
