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

### Wrestler YOBJ: POSITIONS + CONNECTIVITY CRACKED (2026-10-13)
Wrestler `.ymg` files (model/wrestler/) use a DIFFERENT variant:
version 0x00040001, **s16x3 vertices dequantized /64** (tool:
`../../wwe-wrestlemania-xix/tools/yobj_strips.py`).
- **Connectivity = triangle strips, no index buffers**: vertex runs are
  strip-ordered (ladder/zigzag); split at jump boundaries (threshold
  max(400, 4×median step)); near-origin separator verts start new strips.
  Eye-verified: `000_0.ymg` → 383 tris, elbow CAW part → 113 tris
  (see `../../wwe-wrestlemania-xix/objs/`).
- **Batch table**: 58 × 16-byte records at header [0x5C] — payload offset
  (base file 0x80), material/part id, unit count; semantics measured in
  `../../wwe-wrestlemania-xix/docs/YOBJ-BATCH-SEMANTICS.md`.
- **Open**: per-vertex (not per-batch) skinning transforms — per-batch bone
  bind matrices were REJECTED by measurement (all transforms scattered).
  The elbow (rigid CAW part) renders coherent, so s16/64 is valid; either a
  weight table is unlocated or positions are delta-encoded.
  See `../../wwe-wrestlemania-xix/YOBJ-SKINNING-NOTES.md`.

The arena crack (f32) does NOT transfer to wrestlers — different YOBJ
version (0x00030013 vs 0x00040001), different vertex encoding.

## FACE INDICES: CRACKED (2026-10-13 update)

### Index record format (20 bytes)
```
[u16 a][u16 b][u16 c][u32 0xFFFFFFFF][u16 base][u16 d][u16 e][u32 0xFFFFFFFF]
```
- **Triangle** = `(b+base, c+base, e+base)` — global vertex indices into the concatenated vertex arrays
- **Field `a`**: constant per block (material/group ID, e.g. 159)
- **Field `d`**: equals `b` in most records (redundant)
- **Separators**: 0xFFFFFFFF (32-bit) delimit fields
- **Base**: vertex array base offset (e.g. 864 = 0x0360)

### Validation
Geometrically verified: median edge 1.0–1.3 units in a ~5000-unit arena.
Non-degenerate triangles with correct winding.

### Tool
`tools/yobj_arena_faces.py` — extracts faces with geometric validation.

### Status
Format CRACKED. Block discovery ongoing: 249 validated triangles found in bg/00.ymg
via the 20-byte record pattern. Full-coverage extraction (10k+ tris expected) needs
additional block-format variants identified. The 20-byte pattern covers one material
group; other groups may use different record layouts.

### Material table (corrected)
- Records are **20 bytes** (not 28). Offset field at +16 within each record.
- Each points to a descriptor in the 0x480c0+ region, 52 bytes apart (32-byte header + 20-byte sub-record).
- Sub-record: `[u32 self][u32 0][u32 3][u32 50][u32 0x0f0a080f]`
