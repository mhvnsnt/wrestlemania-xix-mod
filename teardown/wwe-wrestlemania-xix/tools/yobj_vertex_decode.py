#!/usr/bin/env python3
"""YOBJ vertex decoder — DOL RE lane (a2).

Decodes YOBJ skin-batch s16x3 vertex positions into float32 triangle strips.

Findings (see docs/YOBJ-DOL-DECODER-REPORT.md):
- main.dol (ISO 0x1F700, 3.26MB) contains file-type table at DOL file offset
  0x30B2B0 (vaddr 0x8030E2B0): POF0->1, YOBJ->2, YANM->3, POFE->-2, DUMY->-1.
- Loader at 0x8007A71C / 0x8007AACC: magic->id via table memcmp loop;
  POF0 (id 1) sections apply pointer relocations (add base to u32s at
  encoded offsets). YOBJ (id 2) section data is memmove'd then relocated.
- Skin batches: s16x3 big-endian positions. Each batch is a TRIANGLE STRIP
  in vertex order (verified by own-eyes render: coherent ribbon meshes).
- Scale: s16 / 64 (matches GX s16 vertex with 6 frac bits; skeleton units).

Gaps (not yet solved):
- Strip restart boundaries within a batch (Table1/Table2 semantics).
- Batch->bone mapping for skinning assembly (b0 field purpose unconfirmed).
"""

import struct
import numpy as np


def parse_yobj_header(ymg: bytes) -> dict:
    """Parse YOBJ 0x80-byte header. Returns field dict."""
    h = {}
    h['magic'] = ymg[0:4]
    assert h['magic'] == b'YOBJ', f"bad magic {h['magic']!r}"
    h['bone_count'] = struct.unpack('>I', ymg[0x10:0x14])[0]
    h['skeleton_off'] = struct.unpack('>I', ymg[0x14:0x18])[0]
    h['material_count'] = struct.unpack('>I', ymg[0x18:0x1C])[0]
    h['material_table'] = struct.unpack('>I', ymg[0x1C:0x20])[0]
    h['texname_table'] = struct.unpack('>I', ymg[0x24:0x28])[0]
    h['gctc_off'] = struct.unpack('>I', ymg[0x38:0x3C])[0]
    h['data_base'] = struct.unpack('>I', ymg[0x54:0x58])[0]
    h['table1_off'] = struct.unpack('>I', ymg[0x5C:0x60])[0]
    h['batch_table_off'] = struct.unpack('>I', ymg[0x60:0x64])[0]
    return h


def get_batches(ymg: bytes, base: int = 0x80):
    """Yield (b0, count, verts_float32) for each skin batch.

    Record: [u8 b0][u8 count][u16 count][u32 offset_from_base].
    Record 0 is a header; records 1..N are batches.
    """
    h = parse_yobj_header(ymg)
    off = h['batch_table_off']
    batches = []
    for r in range(1, 64):
        rec = ymg[off + r * 8: off + (r + 1) * 8]
        if len(rec) < 8 or rec == b'\x00' * 8:
            break
        b0, c1 = rec[0], rec[1]
        w2 = struct.unpack('>H', rec[2:4])[0]
        doff = struct.unpack('>I', rec[4:8])[0]
        if c1 == 0:
            continue
        vbase = doff + base
        raw = ymg[vbase: vbase + c1 * 6]
        if len(raw) < c1 * 6:
            break
        verts = np.frombuffer(raw, dtype='>i2').reshape(-1, 3).astype(np.float32)
        batches.append({'b0': b0, 'count': c1, 'verts': verts / 64.0,
                        'raw': verts})
    return batches


def strip_triangles(verts: np.ndarray, restart_dist: float = 15.625):
    """Triangulate an (N,3) strip-order vertex array.

    Splits the strip at jumps > restart_dist (in /64-scaled units; 15.625 =
    1000 raw s16 units). Rungs within a strip are ~750-950 raw; true strip
    boundaries are 1050+. Returns (M,3) int32 triangle index array into verts,
    with alternating winding for strips.

    NOTE: This is a heuristic. True strip boundaries come from Table1/Table2
    (not yet decoded). See docs/YOBJ-DOL-DECODER-REPORT.md.
    """
    n = len(verts)
    if n < 3:
        return np.zeros((0, 3), dtype=np.int32)
    # find split points
    dists = np.linalg.norm(verts[1:] - verts[:-1], axis=1)
    splits = [0] + [i + 1 for i, d in enumerate(dists) if d > restart_dist] + [n]
    tris = []
    for a, b in zip(splits[:-1], splits[1:]):
        m = b - a
        if m < 3:
            continue
        for i in range(m - 2):
            i0, i1, i2 = a + i, a + i + 1, a + i + 2
            if i % 2 == 0:
                tris.append((i0, i1, i2))
            else:
                tris.append((i1, i0, i2))
    return np.array(tris, dtype=np.int32)


def decode_yobj_verts(ymg_bytes: bytes):
    """Decode YOBJ skin batches to float32 positions + triangle indices.

    Returns dict with:
      'batches': list of {'b0', 'count', 'verts' (Nx3 float32, /64 scale),
                          'tris' (Mx3 int32 strip triangulation)}
      'verts_all': (606,3) concatenated positions (for 000_0.ymg)
      'tris_all': (T,3) concatenated triangles (batch-local indices rebased)

    NOTE: positions are in batch-local (bind-pose, pre-skinning) space.
    Batch->bone skinning assembly is NOT applied (mapping unconfirmed;
    see docs/YOBJ-DOL-DECODER-REPORT.md §5).
    """
    batches = get_batches(ymg_bytes)
    all_v = []
    all_t = []
    voff = 0
    for b in batches:
        v = b['verts']
        t = strip_triangles(v)  # uses 15.625 threshold (1000 raw units)
        b['tris'] = t
        all_v.append(v)
        if len(t):
            all_t.append(t + voff)
        voff += len(v)
    verts_all = np.vstack(all_v) if all_v else np.zeros((0, 3), np.float32)
    tris_all = np.vstack(all_t) if all_t else np.zeros((0, 3), np.int32)
    return {'batches': batches, 'verts_all': verts_all.astype(np.float32),
            'tris_all': tris_all.astype(np.int32)}


if __name__ == '__main__':
    import sys
    ymg = open(sys.argv[1], 'rb').read()
    out = decode_yobj_verts(ymg)
    print(f"batches: {len(out['batches'])}")
    for i, b in enumerate(out['batches']):
        print(f"  batch{i+1}: b0={b['b0']} verts={b['count']} tris={len(b['tris'])}")
    print(f"total verts: {len(out['verts_all'])}, total tris: {len(out['tris_all'])}")
    # write OBJ
    with open('/tmp/yobj_decoded.obj', 'w') as f:
        for v in out['verts_all']:
            f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
        for t in out['tris_all']:
            f.write(f"f {t[0]+1} {t[1]+1} {t[2]+1}\n")
    print("wrote /tmp/yobj_decoded.obj")
