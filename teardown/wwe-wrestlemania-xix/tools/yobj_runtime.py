#!/usr/bin/env python3
"""YOBJ runtime vertex format decoder (WWE WrestleMania XIX, GameCube).

Reverse-engineered from main.dol (see docs/YOBJ-DOL-DECODER-REPORT.md).

PROVEN from the DOL's vertex buffer builder @0x80078C6C:
- The game builds 28-byte runtime vertices by copying 12-byte source verts
  (6x s16) VERBATIM. There is NO arithmetic decode on positions.
- POSITION FORMULA: P = (s16_x, s16_y, s16_z) -- raw signed 16-bit values.
  Render-time scale (1/64, matching the elbow finding) is applied by GX,
  not the loader. No s16->float conversion exists in the DOL text.

Runtime vertex (28 bytes), built by the loop at 0x80079348/0x80079400:
  +0x00: s16 x3  position (verbatim)
  +0x06: s16 x3  normal   (verbatim)
  +0x0C: u32     packed bone indices: ((b2+1)<<16 | (b1+1)<<8 | (b0+1))
                 bN = bonemap[file_boneN]; path1 (rec[3]==1): single bone, w=0
  +0x10: u32     weights (per-vertex stream) or 0
  +0x14,+0x18: s16  material/batch index
  +0x16,+0x1A: s16  vertex index

Draw record (16 bytes) consumed per batch by the builder:
  [0],[1],[2]: bone bytes (via 256-byte bonemap)
  [3]: type (1 = single bone; 3 = two bones; else three bones)
  [4]: u32 vertex count (copy-loop trip count)
  [8]: u32 aux (weight-stream pointer for multi-bone path)
  [12]: u8  source-advance count (src += count*12)
  [13]: u8  flag (0 = skip source advance)

STATUS: the 12-byte source verts' location in the YOBJ file is not yet
mapped (see report section 7). This module decodes the runtime format once
the source is identified.
"""
import struct

VERTEX_SIZE = 28
SOURCE_SIZE = 12

def decode_runtime_vertex(buf, off=0):
    """Decode one 28-byte runtime vertex. Returns dict."""
    x, y, z = struct.unpack('>3h', buf[off:off+6])
    nx, ny, nz = struct.unpack('>3h', buf[off+6:off+12])
    bones_packed, weights = struct.unpack('>2I', buf[off+12:off+20])
    mat0, vidx0, mat1, vidx1 = struct.unpack('>4h', buf[off+20:off+28])
    b0 = bones_packed & 0xFF
    b1 = (bones_packed >> 8) & 0xFF
    b2 = (bones_packed >> 16) & 0xFF
    return {
        # POSITION FORMULA: raw s16, render scale applied by GX (1/64)
        'pos': (x, y, z),
        'pos_scaled': (x / 64.0, y / 64.0, z / 64.0),
        'nrm': (nx, ny, nz),
        'bones': (b0 - 1, b1 - 1, b2 - 1),  # stored as index+1
        'bones_packed': bones_packed,
        'weights': weights,
        'material': mat0,
        'vert_index': vidx0,
    }

def decode_source_vertex(buf, off=0):
    """Decode one 12-byte source vertex (6x s16, verbatim-copied)."""
    x, y, z, nx, ny, nz = struct.unpack('>6h', buf[off:off+12])
    return {
        'pos': (x, y, z),
        'pos_scaled': (x / 64.0, y / 64.0, z / 64.0),
        'nrm': (nx, ny, nz),
    }

def build_runtime_vertex(src12, bone_u32, weights_u32, material, vert_index):
    """Emulate the DOL builder: 12-byte source -> 28-byte runtime vertex."""
    out = bytearray(28)
    out[0:12] = src12[0:12]  # verbatim s16x6 copy (lha/sth x6)
    struct.pack_into('>I', out, 12, bone_u32)
    struct.pack_into('>I', out, 16, weights_u32)
    struct.pack_into('>h', out, 20, material)
    struct.pack_into('>h', out, 22, vert_index)
    struct.pack_into('>h', out, 24, material)
    struct.pack_into('>h', out, 26, vert_index)
    return bytes(out)

def write_obj(path, verts, scale=1.0/64.0):
    """Write positions as OBJ (for proof renders once source is mapped)."""
    with open(path, 'w') as f:
        f.write('# YOBJ runtime verts: pos = s16 * %s (DOL-proven)\n' % scale)
        for v in verts:
            x, y, z = v['pos']
            f.write('v %.4f %.4f %.4f\n' % (x*scale, y*scale, z*scale))

if __name__ == '__main__':
    # self-test: emulate builder on synthetic data, decode back
    src = struct.pack('>6h', 700, 567, 1488, 100, 200, 300)
    rv = build_runtime_vertex(src, 0x00020101, 0x3F800000, 5, 42)
    d = decode_runtime_vertex(rv)
    assert d['pos'] == (700, 567, 1488), d
    assert d['nrm'] == (100, 200, 300), d
    assert d['bones'] == (0, 0, 1), d  # packed 0x00020101 -> (1,1,2)-1
    assert d['material'] == 5 and d['vert_index'] == 42, d
    print('self-test OK:', d['pos'], '->', d['pos_scaled'])
