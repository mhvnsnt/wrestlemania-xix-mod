# YOBJ Skinning Decoder — Investigation Report (2026-10-15)

**Sample:** `model/wrestler/000_0.ymg` (69,176 B, Triple H) + `edit_data/MODEL/Man/Elbow/me0_000/l0.ymg` (rigid reference)
**Tool:** `tools/yobj_decode.py` (parses container, skeleton, batches, tables; exports OBJ)
**Status:** Container FULLY decoded. Vertex position encoding + skinning assembly UNSOLVED.

---

## 1. What was decoded (all measured)

### YOBJ header (0x80 bytes, big-endian)
| Offset | Value (000_0) | Meaning |
|---|---|---|
| 0x00 | `YOBJ` | magic |
| 0x08 | `0x00040001` | [u16 a=4][u16 b=1] (elbow/face: 3/1; 001_0: 4/4) |
| 0x10 | `0x47` (71) | bone slot count (incl. null sentinel) |
| 0x14 | `0xF3B4` | skeleton section (bone slots start +8 = 0xF3BC) |
| 0x18 | `0x0F` (15) | material count |
| 0x1C | `0x10704` | material table |
| 0x24 | `0x10574` | texture name table (ASCII) |
| 0x38 | `0xF360` | GCTC section |
| 0x54 | `0x80` | data base (payload offsets are relative to this) |
| 0x5C | `0x5AE0` | Table1 (draw descriptors) |
| 0x60 | `0x7CA0` | skin-batch descriptors |

### Skeleton (71 slots × 64 B @0xF3BC)
Slot: `name[16] | u32 parent (1-based, 0xFFFFFFFF=none) | f32 pos[3] | f32 euler[3] | f32 length | pad[16]`.
Full hierarchy in `WRESTLER-SKELETON.md`. World matrices computable (euler XYZ: R=Rx@Ry@Rz).
Bone 0 = "null" sentinel; bone 1 = "Bip" root.

### Skin batches (13 + header @0x7CA0, 8 B records)
Record: `[u8 idx][u8 count][u16 count][u32 offset]` (offset from base 0x80).
000_0: 606 verts total as **s16x3** runs. Counts: 72,65,49,120,17,50,15,23,72,102,4,13,4.
All batches span ~0–1900 raw units in every axis, all-positive, smooth (median consecutive dist 49–374).

### Table1 — draw descriptors (58 × 16 B @0x5AE0)
Record: `[u32 u0][u32 u1][u8 b8][u16 marker][u8 variant][u32 count]`.
- `u0`: payload offset (from 0x80). `count`: number of 4-byte payload units.
- Payload: **(u16, 0) pairs** — second u16 is 0 for 99.7% (892 units total, values 0–4096).
- Records 1–7 share `u0=0x61C0`; counts sum to 128 = record 0's count (group header).
- `b8`: 0x03–0x46 (NOT bone index — rejected; likely part/material id).
- `u1`: 0, 1, or `0x80000000|X`.

### Table2 — SECOND table (DISCOVERED 2026-10-15, 52 × 16 B @0x5AE0+58*16=0x5E80)
Record: `[u32 u0][u32 u1][u16 a][u16 b][u16 c=0][u16 count]`.
- Payload: **(u16, u16) pairs** (1026 units total, values 0–17667, both nonzero).
- `c` is always 0. Counts (d) range 0–54.

### Materials (15 × 20 B @0x10704)
Record: `[u16 a][u16 b][u16 one=1][u16 idx_off][RGBA×3]`.
`idx_off` values are 0x5C apart (0x830, 0x88C, …) — 92-byte stride, but the
target data overlaps skin-batch vertex runs (not separate blocks).

### Texture names (@0x10574)
13 body parts: `hhh_body, hhh_arm, hhh_hand, hhh_waists, hhh_l_leg, hhh_knee,
hhh_foot, face, head_back, eye, head_top, mouth, tooth` (+ `m_`/`pm_` variants).

---

## 2. Hypotheses tested and REJECTED

| # | Hypothesis | Result |
|---|---|---|
| 1 | s16x3 = (x,y,z) positions, per-batch bone world matrix | SCATTERED (all 13 batches × 70 bones) |
| 2 | s16x3 with /8, /16, /64 scales, 6 axis permutations | SCATTERED |
| 3 | s16x3 centered per-batch, then bone transform | SCATTERED (batches are scribbles, not parts) |
| 4 | Table1 (u16,0) = vertex indices into 606-vert pool | DEGENERATE (35/49 tris degenerate; values 0–4096 ≫ 606) |
| 5 | Table1 = (bone:u8, weight:u8) pairs | REJECTED (77/892 "bones" > 70) |
| 6 | Table1 = UV.u (12-bit), Table2 = (Y,Z) → 892 3D verts | STRUCTURE but not human (vertical walls/columns) |
| 7 | rec0 (x,y) + group (z) = 128 head verts | BLOB (not head-like) |
| 8 | Per-subset bone transform (recs 1–7 → b8 bones) | SCATTERED |
| 9 | s16x3 = (pos,nrm) interleaved | REJECTED (normals not unit-like) |
| 10 | Delta encoding (cumsum) | REJECTED (values all-positive, explodes) |
| 11 | Table1+Table2 as (X,Y,Z) in 3 permutations | STRUCTURE but not human |

---

## 3. Key external findings (2026-10-15)

1. **YOBJ format doc** (`xmcacutt/yukes-yobj-format-documentation`, PS2-era):
   - Meshes have vertex buffers (positions + normals); submeshes have face strips.
   - Strip data: `UVW (float3) | Vertex Index (int32) | Unk` per 0x20-byte entry.
   - Skinning: per-vertex `(bone, weight)` lists.
   - Confirms the CONCEPTS but 2003 GameCube encoding differs (s16 vs float).

2. **2K19 YOBJ Blender plugin** (`pokeytroll195/...`): vertices are `>3f` positions +
   `>3f` normals (28-byte stride); skin is `(u16 bone, f32 weight)` per influence;
   triangles from face-index strips. Again, concepts confirmed, encoding differs.

3. **Elbow (rigid) vs 000_0 (skinned)**: SAME container structure (Table1 with
   (u16,0) payloads, skin batches, skeleton). The 148-vert elbow shell renders
   coherently from s16x3/64 with NO transform, but 000_0's 606 verts do not.
   The difference is not structural — it's in how the vertex data encodes positions.

---

## 4. PRECISE BLOCKER

**The vertex position encoding is unknown.** Specifically:

1. The 606 s16x3 values do not behave as (x,y,z) positions under any tested
   rigid transform (bone matrices, scales /8–/64, axis permutations, centering).
   They form smooth strips but the strips are scribbles, not body parts.

2. Table1's 892 (u16,0) and Table2's 1026 (u16,u16) payloads do not decode as
   vertex indices (range 0–4096/0–17667 exceeds any located pool), UVs, or
   (bone,weight) pairs. Their exact semantics are unknown.

3. No batch→bone mapping exists in the parsed structures. The 8B descriptors
   carry only (count, offset). Table1's `b8` (3–70) does not map cleanly to
   13 batches or 71 bones.

**What this means:** The GameCube YOBJ uses a vertex encoding that is not
plain s16x3 positions. It may be:
- Quantized/compressed positions requiring Table1/Table2 as codebooks,
- Positions in a non-obvious space (e.g., bone-relative with per-vertex bone
  selection from an unlocated table),
- Or the s16x3 runs are not positions at all (normals? deltas? parameters?).

---

## 5. Next concrete experiment

**Reverse-engineer the DOL's YOBJ vertex loader.** The game's main executable
(on the ISO) contains the parsing code. Steps:
1. Extract the DOL (`//sys/main.dol`) via `tools/wmxix_range_iso.py`.
2. Search for YOBJ magic (`0x594F424A`) or header field accesses.
3. Identify the vertex buffer decoding (likely a loop reading s16x3 + Table1/Table2).
4. The decoding math will reveal the exact position formula.

**Alternative (cheaper):** Find a GameCube-era YOBJ tool or doc. The PS2 "YOBJ Specs
+ Hex Workshop Bookmark File (eri619 & Greg Thordenta)" may cover the s16
encoding if the PS2 and GameCube versions share it.

**Alternative (empirical):** Locate the in-game posed vertex buffer via Dolphin
emulator memory dump (run the game, break at render, dump GX vertex arrays).
The GPU-ready data will show the true positions, revealing the decode.

---

## 6. Deliverables

- `tools/yobj_decode.py`: full container parser (header/skeleton/batches/
  table1/table2/materials), exports `_skeleton.obj` + `_batches.obj` (raw).
- `work/ymg-decode/`: sample files (000_0, 001_0, elbow, face), renders,
  cloned YOBJ docs (`yobj-doc/`, `yobj-plugin/`).
- This report.

**Not delivered:** a working mesh decoder (blocked as above).
