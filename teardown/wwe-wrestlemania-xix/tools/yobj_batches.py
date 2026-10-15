#!/usr/bin/env python3
"""YOBJ TODO (3): draw-batch table decode.
The 0x10D80 'GX display list' hypothesis is WITHDRAWN (that region is saturated
vertex payload). YOBJ has no GX DL (byte scan finds only scattered false
positives). The real draw structure is the 16-byte batch table at header
[0x5C]: (u32, u32, u8 type, u16 marker, u8 variant, u32 count).
Usage: python3 tools/yobj_batches.py [disc/path/file ...] (default: model/wrestler/000_0.ymg)"""
import struct, sys
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32

def batch_table(data):
    t = u32(data, 0x5C)
    recs = []
    o = t
    while o + 16 <= len(data):
        r = data[o:o + 16]
        b11 = r[11]; cnt = struct.unpack('>I', r[12:16])[0]
        if r[0] == 0 and b11 in (1, 2) and cnt < 20000:
            recs.append(dict(off=o,
                              u0=struct.unpack('>I', r[0:4])[0],
                              u1=struct.unpack('>I', r[4:8])[0],
                              b8=r[8], marker=r[9:11].hex(), variant=b11,
                              count=cnt))
            o += 16
        else:
            break
    return t, recs

def gx_scan(data):
    """Count GX draw-command-like bytes; report clustering (or lack thereof)."""
    hits = []
    for i in range(len(data) - 3):
        c = data[i]
        if c in (0x90, 0x98, 0xA0):
            cnt = struct.unpack('>H', data[i + 1:i + 3])[0]
            if 3 <= cnt <= 6000:
                hits.append(i)
    return hits

if __name__ == '__main__':
    for yp in sys.argv[1:] or ['model/wrestler/000_0.ymg']:
        data, size = stream_file(yp)
        assert data[:4] == b'YOBJ', yp
        t, recs = batch_table(data)
        hits = gx_scan(data)
        print(f'== {yp} (size {size:#x}): batch table @{t:#x}, {len(recs)} records; '
              f'{len(hits)} GX-cmd-like bytes (scattered, no DL)')
        for r in recs[:8]:
            print(f"  @{r['off']:05X} u0={r['u0']:08X} u1={r['u1']:08X} b8=0x{r['b8']:02X} "
                  f"marker={r['marker']} v={r['variant']} count={r['count']}")
        if len(recs) > 8:
            print(f'  ... +{len(recs) - 8} more, count sum = {sum(r["count"] for r in recs)}')
