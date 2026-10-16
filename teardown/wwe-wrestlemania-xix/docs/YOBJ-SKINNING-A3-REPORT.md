# YOBJ Skinning Assembly — Lane (a3) Report (2026-10-16)

**Worker:** lane (a3) SKINNING ASSEMBLY, branch `lane/skinning-assembly-100-retail`
**Goal:** Table1/Table2 strip boundaries + batch→bone mapping; deliver
         `tools/assemble_wrestler.py` with a verified humanoid render.
**Result:** PARTIAL. Positions decode (a2-proven). Strip triangulation
         improved (1300 threshold). **Batch→bone mapping UNRESOLVED** —
         the 13 batches do not assemble into a recognizable humanoid.
         This report documents precisely what's wrong.

---

## 1. Table1/Table2 strip boundaries — FINDINGS

### 1a. There is no "Table2" at 0x5E80
`docs/YOBJ-SKINNING-DECODER-REPORT.md` §1 claims a second table of 52×16B
at 0x5AE0+58*16=0x5E80 with (u16,u16) payloads. **This is a misparse.**
Bytes at 0x5E88 are the Table1 payload pool ((u16,0) pairs), not records.
The actual structure is **one table at 0x5AE0 with 58 records**:
- 8-byte table header (zeros), then 58×16B records.
- Correct record layout: `[u32 u0][u32 u1][u8 b8][u16 marker][u8 variant][u32 count]`
  (the a2-era parse starting at 0x5AE8 was off by 8; the BATCH-SEMANTICS
  doc's layout is correct).
- 6 records with variant=1 (marker=0xffff), 52 with variant=2
  (marker=(b8-1)<<8|0xff).
- Records 1–7 share u0=0x61C0; counts [44,14,14,8,4,38,6] sum to 128 =
  record 0's count (group header). Records 8–57 have unique u0.
- Payload: 892 (u16,0) units, values 0–4096, second u16 always 0.

### 1b. Table1 does NOT define skin-batch strip boundaries
- Table1 record `count` values vs heuristic strip lengths (1300 threshold):
  only **13/58 exact matches**. The 58-record count matching the 58
  heuristic strips (noted in BATCH-SEMANTICS) is coincidental.
- Table1 payload u16s (0–4096) do not index into batch verts (max 120),
  the 606-vert concatenated array, or the 4412 gap pool (indexed verts
  are non-smooth: median consecutive dist 430–986 vs 49–374 for batches).
- **Conclusion:** Table1 is a separate attribute layer / draw-descriptor
  list, not the strip index. Its exact semantics remain OPEN.

### 1c. Improved strip triangulation (the real fix for boundaries)
The a2 1000-raw-unit heuristic **splits at rail crossings**, breaking strips.
Measured on 000_0.ymg batch 3:
- Consecutive distances show two jump types:
  - ~1025 runs (3 in a row): **rail crossings within a zigzag strip**
    (verts alternate between z≈1900 and z≈900 layers).
  - Isolated jumps >1300 (1422, 2098, 1925, 1769, 1695, 1891, 1305, 1659):
    **true strip boundaries**.
- New threshold: **1300 raw units** (20.3 in /64 units).
- Result: 606 verts → **536 tris** (vs 469 with 1000 threshold), 27 strips.
  Strips are visibly more coherent (ribbons instead of fragments).

---

## 2. Batch→bone mapping — UNRESOLVED

### 2a. What was tried
| Mapping | Result |
|---|---|
| b0 → JSON bone b0 (`bone_world @ (v/64)`) | Batches cluster near spine/face bones (centroids within ~15u of bones). **No limbs. Not a humanoid.** |
| b0 → bone b0+1 (a2) | Same (reported by a2). |
| Size-based guess (120v→Spine1, 72v→Thigh, etc.) | Scattered. Wrong. |
| Texture-part-order guess (b0→part→bone) | Scattered. Wrong. |
| Translation-only | Scattered (confirms rotation matters). |

### 2b. Precisely what's wrong
With b0→bone b0 (the most principled mapping):
- 13 batches land at bones 0–12 = Bip, Pelvis, Spine, Spine1, Neck, Head,
  right_lip, top_tooth, low_tooth, low_lip, top_lip, left_lip, r_top_eye.
- Transformed bounds: x∈[0,84], y∈[-103,-70], z∈[-30,30].
- Skeleton bounds: x∈[-90,69] (feet to head), z∈[-10,74] (arms).
- **The batches occupy only the torso/head X-range. They do not extend
  to the arm region (z=17–74 at x=55) or the leg region (x=-90–0).**
- Render (`teardown/wmxix/wrestlers/000/assembled.png`): a jumble of
  colored patches in the torso/head area. Not a recognizable humanoid.
  (Own-eyes verified.)

### 2c. Why b0 cannot be a direct bone index
- b0 values are 0–12. The 70-bone skeleton's limb bones are at indices
  18–69 (arms), 60–68 (legs). No mapping of 0–12 reaches them.
- YMG skeleton slots 0–12 verified by direct read: null, Bip, Pelvis,
  Spine, Spine1, Neck, Head, + 6 face bones. Definitely no limbs.
- Therefore b0 must be remapped (via a table not yet located in YMG or
  DOL), OR b0 is not a bone index at all.

### 2d. DOL RE performed (inconclusive)
- Parsed main.dol (3.4MB); built robust PPC disassembler.
- Found 15 candidate skinning functions (lha + 0x4330 + fmadds); the most
  promising (0x8008cbb8, 12 halfword loads + 12 fmadds) processes **bytes**,
  not s16x3 — not the batch skinning loop.
- Found "bone00"–"bone11" strings (12 bones, order 05,04,03,08,07,06,09,
  11,10,02,01,00) but they sit in a material/render-state table, not a
  bone palette; no code xrefs found.
- The batch→bone remap table was not located. Further DOL work needed:
  find the function that reads YOBJ+0x60 (batch table) and uses the b0
  byte as an index.

---

## 3. Deliverables
- `tools/assemble_wrestler.py`: takes slot dir or .ymg path; decodes via
  a2 `decode_yobj_verts`; triangulates with 1300 threshold; applies
  b0→bone map (overridable via `--map`); writes `assembled.obj` + render.
  Tested on slot 000: 606 verts, 536 tris.
- `teardown/wmxix/wrestlers/000/000_0.ymg`: cached YMG (69,176 B).
- `teardown/wmxix/wrestlers/000/assembled.obj`: assembled mesh (b0→bone).
- `teardown/wmxix/wrestlers/000/assembled.png`: render (own-eyes verified:
  **not a humanoid** — documents the unresolved mapping).

## 4. Next steps (for follow-up)
1. **DOL:** Find the batch-table consumer (YOBJ+0x60 reader). The b0→bone
   remap is likely a small table in the DOL or a hardcoded array.
2. **Alternative:** Dolphin memory dump — run the game, break at render,
   dump the posed vertex buffer; the GPU-ready positions reveal the mapping.
3. **Table1:** Its 892 (u16,0) payload may be UVs or a second mesh; decode
   via the DOL's Table1 reader (YOBJ+0x5C).

## 5. Checkpoint
`~/workspace/agent-ops/checkpoints/wmxix-100-retail-skinning-a3.json` →
status `blocked` (batch→bone mapping unresolved; all else delivered).
