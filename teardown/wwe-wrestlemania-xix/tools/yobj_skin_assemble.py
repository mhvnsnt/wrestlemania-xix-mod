#!/usr/bin/env python3
"""YOBJ skinned-mesh assembler (WWE WrestleMania XIX, GameCube).

Reproduces/validates docs/YOBJ-SKINNING-SOLUTION.md:
  - skin batch descriptor byte [0] (u8 idx) IS the 0-based bone index
  - batch verts are s16 triplets in BONE-LOCAL space, scale 1/64
  - world_pos = bone_world_matrix[idx+1] @ (vertex / 64.0)
    (idx+1 skips the 'null' sentinel at skeleton slot 0)

Usage: yobj_skin_assemble.py <file.ymg> [out.obj]
Prints per-batch bone assignment + bbox dimensions (cm) for verification.
"""
import sys, math, struct
sys.path.insert(0, __import__('os').path.dirname(__file__))
from yobj_decode import Yobj, u32, s16
import numpy as np


def parse_batches_with_idx(y):
    """Like Yobj.parse_batches but captures the descriptor idx byte (d[o])."""
    d = y.d
    batches = []
    o = y.skin_off
    rec = 0
    while o + 8 <= len(d):
        idx_byte = d[o]
        c1 = d[o+1]
        cnt16 = struct.unpack('>H', d[o+2:o+4])[0]
        off = u32(d, o+4)
        if y.base + off >= len(d):
            # terminator/padding record (e.g. rec14: u8 count=0, u16=53,
            # offset 0x6F1035C far beyond EOF) — not a real batch
            break
        if c1 == 0 and off == 0:
            o += 8; rec += 1; continue
        base = y.base + off
        verts = [(s16(d, base+i*6), s16(d, base+i*6+2), s16(d, base+i*6+4))
                 for i in range(c1)]
        batches.append(dict(rec=rec, idx_byte=idx_byte, count=c1,
                            count16=cnt16, offset=off, verts=verts))
        o += 8; rec += 1
        if rec > 32:
            break
    return batches


def assemble(y):
    y.parse_skeleton()
    batches = parse_batches_with_idx(y)
    W = y.world_mats
    names = [b['name'] for b in y.bones]
    out = []          # (batch_rec, bone_name, world verts)
    for b in batches:
        bi = b['idx_byte'] + 1          # skip null sentinel
        assert bi < len(W), f"batch rec {b['rec']}: bone idx {bi} out of range"
        M = W[bi]
        wv = []
        for (x, y_, z) in b['verts']:
            p = np.array([x/64.0, y_/64.0, z/64.0, 1.0])
            wv.append((M @ p)[:3])
        out.append((b, names[bi], np.array(wv)))
    return out


def bbox(a):
    lo, hi = a.min(axis=0), a.max(axis=0)
    return lo, hi, hi - lo


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else None
    data = open(src, 'rb').read()
    if data[:4] == b'DUMY':
        # DUMY-wrapped YOBJ (cf. DOL magic dispatch table): YOBJ starts at
        # the first YOBJ magic within the prologue
        at = data.find(b'YOBJ', 0, 128)
        assert at > 0, 'DUMY without embedded YOBJ'
        print(f'DUMY prologue ({at} bytes), YOBJ at +{at:#x}')
        data = data[at:]
    y = Yobj(data)
    y.parse_header()
    parts = assemble(y)
    print(f"{src}: {len(parts)} batches")
    allv = []
    f = open(dst, 'w') if dst else None
    try:
        for b, bone, wv in parts:
            lo, hi, dim = bbox(wv)
            # dimensions in game units (s16/64); ~cm scale per solution doc
            print(f"  rec{b['rec']:2d} idx_byte={b['idx_byte']:2d} -> bone[{b['idx_byte']+1:2d}] "
                  f"{bone:16s} n={len(wv):3d} dim=({dim[0]:6.1f},{dim[1]:6.1f},{dim[2]:6.1f}) "
                  f"max={dim.max():6.1f} cnt16={b['count16']}")
            allv.append(wv)
            if f is not None:
                f.write(f"g batch{b['rec']}_{bone}\n")
                for p in wv:
                    f.write(f"v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}\n")
    finally:
        if f is not None:
            f.close()
    allv = np.vstack(allv)
    lo, hi, dim = bbox(allv)
    print(f"OVERALL bbox min=({lo[0]:.1f},{lo[1]:.1f},{lo[2]:.1f}) "
          f"max=({hi[0]:.1f},{hi[1]:.1f},{hi[2]:.1f}) dim=({dim[0]:.1f},{dim[1]:.1f},{dim[2]:.1f})")
    if dst:
        print(f"wrote {dst}")


if __name__ == '__main__':
    main()
