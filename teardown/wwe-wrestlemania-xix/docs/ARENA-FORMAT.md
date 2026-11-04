# WMXIX Arena YOBJ Format — CRACKED (2026-10-13)

## Status: VERTEX POSITIONS CRACKED ✅ | FACE INDICES OPEN ⚠️

### What works
Arena `.ymg` files in `bg/` contain **f32 (float32) vertex triplets** — NOT
quantized like wrestler models. 43 arena files extracted, 324,425 verts total.

### Vertex format
- **Type:** 3× f32 (12 bytes/vertex), big-endian
- **Layout:** Contiguous arrays, 20 arrays in bg/00.ymg (16,831 verts)
- **Coordinate space:** Model space, units are game units (~5000 = arena width)
- **Detection:** Scan for runs of 5+ consecutive sane f32 triplets
  (|v| < 20000, not ASCII text)

### File structure (bg/00.ymg, 304,480 bytes)
| Offset | Content |
|--------|---------|
| 0x00 | `YOBJ` magic, version 0x00030013 (different from wrestler 0x00040001) |
| 0x14 | → 0x46BB4: object/bone names ("kaijo_rw") |
| 0x1C | → 0x47404: material table (25 records × 20 bytes) |
| 0x24 | → 0x470B4: texture name table ("rw19.bmp", etc.) |
| 0x60 | → 0x0830: mesh metadata |
| 0x68-0x77 | f32 bounding values |

### Material records (20 bytes each, at 0x47404+)
```
[u32 color1][u32 color2][u32 color3][u32 0][u16 0x0004][u16 idx_offset]
```
Index offsets are ABSOLUTE file offsets (e.g., 0x80C0, 0x80F4...).
Each points to a ~52-byte chunk of u16 data.

### Face indices: OPEN
The u16 chunks at material index offsets contain MIXED data — not clean
triangle indices. Values like [0, 5, 134, 44718, 44799, ...] suggest
interleaved attributes or a different stride. The vertex→face mapping
needs the mesh-header structure parsed.

**Next step:** Parse mesh descriptors at 0x0830+ to link vertex arrays
to index arrays. Or: use Blender Poisson reconstruction on point clouds.

### Extracted data
- **Tool:** `tools/extract_all_arenas.py`
- **Output:** 43 OBJ files (point clouds, no faces yet)
- **Location:** Pushed to `western-heart/teardown/wmxix/arenas/`
- **Renders:** `/tmp/yobj_validate/arena_*.png` show correct geometry
  (bg/00 = full arena, ring.ymg = wrestling ring, kaijo_x8 = arena)

### Wrestler YOBJ: STILL OPEN
Wrestler `.ymg` files (model/wrestler/) use a DIFFERENT format:
- Quantized s16 vertices (not f32)
- Per-bone skinning batch tables
- The /64 fixed-point hypothesis did NOT validate cleanly
- See `tools/yobj_validate.py` and `tools/yobj_diag.py` for attempts

The arena crack does NOT directly transfer to wrestlers — different
YOBJ version (0x00030013 vs 0x00040001), different vertex encoding.
