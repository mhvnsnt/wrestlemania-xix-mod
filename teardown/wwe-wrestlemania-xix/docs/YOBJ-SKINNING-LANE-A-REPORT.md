# YOBJ Skinning Decode — Lane (a) Technical Report (2026-10-15)

**Worker:** lane (a) SKINNING DECODE, branch `lane/skinning-decode-100-retail`
**Goal:** Solve YOBJ wrestler skinning for real WMXIX wrestler meshes on the 70-bone skeleton.
**Result:** No working skinning solution. The prior "YOBJ-SKINNING-SOLUTION.md" (2026-10-15)
claiming solved skinning is **FALSE** — disproven by own-eyes verification (see §1).
This report documents all tested hypotheses with measured numbers and the single
most promising next step (§5).

---

## 1. CRITICAL FINDING: Prior "Solution" is false

`teardown/wwe-wrestlemania-xix/docs/YOBJ-SKINNING-SOLUTION.md` (committed in e83771f)
claims: "Skin batch descriptor `idx` field IS the bone index... All parts assemble
into correct anatomical positions... Verified on 000_0.ymg."

**Disproven:** The commit's own output file `testbed/head_000.obj` ("000_0.ymg assembled
with bone transforms", 606 verts, 580 tris) renders as **scattered garbage** — verified
with my own eyes from 5 angles (see `/tmp/asm_head.png` in lane notes). It is not a
coherent head, torso, or any body part. The "verification" table in the doc
(batch→bone→"Coherent torso") does not match the actual file content.

Independent re-test: I reimplemented the claimed transform (`world = bone_world @ (v/64)`,
batches→bones 1–5, batch counts [72,65,49,120,17] from the YMG) using the skeleton from
`docs/wrestler-skeleton-000.json`. Result: fragmented blobs near joints, not coherent
parts (see `/tmp/solution_test2.png`). **The bone-transform hypothesis is REJECTED.**

**Implication:** Do not build on YOBJ-SKINNING-SOLUTION.md. It is a false claim.

---

## 2. Ground truth established (via range-read YMG from GitHub release)

Using the repo's `tools/wmxix_range_iso.py` (HTTP Range reads from
`mhvnsnt/western-heart` release `wmxix-iso-v1`; only ~69KB fetched, disk-safe),
I loaded the actual `model/wrestler/000_0.ymg` (69,176 bytes) and verified:

**Skin batch descriptors** (@0x7CA0, 14 records × 8B; rec0 = header):
```
rec: b0  c1   w2(=c1)  offset  -> file offset : verts
 1:   0   72    72     0x07d08 -> 0x07d88 : 72
 2:   1   65    65     0x08c62 -> 0x08ce2 : 65
 3:   2   49    49     0x099de -> 0x09a5e : 49
 4:   3  120   120     0x0a402 -> 0x0a482 : 120
 5:   4   17    17     0x0b5ba -> 0x0b63a : 17
 6:   5   50    50     0x0ba0c -> 0x0ba8c : 50
 7:   6   15    15     0x0c3d4 -> 0x0c454 : 15
 8:   7   23    23     0x0c668 -> 0x0c6e8 : 23
 9:   8   72    72     0x0caa8 -> 0x0cb28 : 72
10:   9  102   102     0x0d7d4 -> 0x0d854 : 102
11:  10    4     4     0x0ef56 -> 0x0efd6 : 4
12:  12   13    13     0x0eff6 -> 0x0f076 : 13   (b0=12, NOT 11)
13:  11    4     4     0x0f2a0 -> 0x0f320 : 4    (b0=11, NOT 12)
```
Record layout: `[u8 b0][u8 c1][u16 w2=c1][u32 offset]` (offset from base 0x80).
Total: 606 verts. b0 values are NOT sequential (12/13 swapped).

**Batch data:** s16x3 big-endian, values ~0–1900 raw, all-positive (one z=-21).
Per-batch bboxes (in /64 units) all span ~0–30 in every axis, all in +octant.
Median consecutive distance 49–374 raw (smooth strips; ladder/zigzag verified).

**Gaps:** 12 gaps between batch data blocks contain **4,412 s16x3 triplets**
(smooth, median dist 3.0/64). As point clouds they show structured (grid-like)
shapes but do not triangulate into coherent meshes via strip heuristic.

**Table1:** 58 records, 892 (u16,0) payload units, values 0–4096, repeating
(e.g. 80, 195, 372, 2048, 3150, 3723).
**Table2:** 52 records, 1026 (u16,u16) payload units, values 0–17667.

---

## 3. Hypotheses tested and REJECTED (all with own-eyes renders)

| # | Hypothesis | Result |
|---|---|---|
| 1 | s16x3 = bone-local (x,y,z), `world = bone_world @ (v/64)`, b0→bone b0+1 | SCATTERED (fragments, not parts). Also tested with 12/13 swap corrected. |
| 2 | Same, with parent-bone matrix instead of bone matrix | SCATTERED |
| 3 | Scales /8, /16, /64; 6 axis permutations | SCATTERED (no head-like shape) |
| 4 | Per-batch centering (subtract bbox center), then bone transform | SCATTERED |
| 5 | Global bias 1024: `(raw-1024)/64` then bone transform | SCATTERED |
| 6 | Delta encoding: per-batch cumsum (first vert absolute) | REJECTED — explodes to 908×1270×1190 random-walk streaks |
| 7 | s16x3 = (pos_idx, nrm_idx, uv_idx) into 4,412-entry gap pool | SCATTERED — mapped mesh still fragmented; all 606 indices in range but no coherence |
| 8 | Little-endian s16x3 | REJECTED — garbage (wild sign flips) |
| 9 | Prior worker's `testbed/head_000.obj` is correct | FALSE — renders as scattered garbage |

**Key diagnostic:** The verts are fragmented *within* each batch (not just misplaced
between batches). If they were positions (even with wrong offset), each batch would
be a coherent chunk. The within-batch fragmentation proves the s16x3 values are
**not (x,y,z) positions in any tested frame** — the encoding is non-trivial
(quantized/compressed, permuted, or non-positional).

**Elbow contrast:** `edit_data/MODEL/Man/Elbow/me0_000/l0.ymg` (rigid CAW part) has
148 verts at fixed offset 0x4D8 (NOT in its batch table) that render coherent via
s16x3/64 with NO transform. The wrestler's 606 "verts" are in the batch table and
do not decode the same way. Rigid vs skinned parts use different vertex storage.

---

## 4. DOL reverse-engineering lead (HIGH VALUE)

The game's executable (`//sys/main.dol`, DOL offset 0x1F700 on ISO) contains a
**file-type table** at DOL file offset **0x30B2B0** (vaddr **0x8030E2B0**):
```
magic    id
POF0     1
YOBJ     2
YANM     3
POFE    -2
DUMY    -1
```
(8-byte entries: `[u32 magic][u32 id]`.)

This table is used by the file loader to dispatch to the YOBJ parser (type 2).
The YOBJ vertex decoding logic is in the DOL near the code referencing this table.

---

## 5. Single most promising next step

**Reverse-engineer the DOL's YOBJ vertex loader.**

Concrete path:
1. Extract `//sys/main.dol` via `tools/wmxix_range_iso.py` (3.4MB, 10 sections).
2. Find code referencing the file-type table (vaddr 0x8030E2B0) — likely a
   linear search comparing file magic, dispatching on ID.
3. Follow the YOBJ (ID 2) path to the vertex buffer decoder. Look for the loop
   reading s16x3 + Table1/Table2. The decoding math (scale, bias, codebook lookup,
   or dequantization) will reveal the exact position formula.
4. Required tooling: PPC disassembler (capstone 5.0.7 already installed;
   `Cs(CS_ARCH_PPC, CS_MODE_BIG_ENDIAN)` works).

**Why this is the right next step:** All empirical hypotheses are exhausted
(§3). The vertex encoding is non-obvious (not plain s16x3 positions). The DOL
contains the ground-truth decoder — the file-type table location is confirmed.
This is a bounded RE task (find one function), not open-ended research.

**Cheaper alternative (if DOL RE stalls):** Dolphin emulator memory dump —
run the game, break at render, dump the GX vertex arrays. The GPU-ready positions
will reveal the decode. Requires Dolphin + game setup.

---

## 6. Files and artifacts

- This report: `teardown/wwe-wrestlemania-xix/docs/YOBJ-SKINNING-LANE-A-REPORT.md`
- Prior false solution (do not use): `teardown/wwe-wrestlemania-xix/docs/YOBJ-SKINNING-SOLUTION.md`
- Disproof render: `/tmp/asm_head.png` (testbed/head_000.obj, 5 angles, scattered)
- Hypothesis test renders: `/tmp/solution_test2.png`, `/tmp/bias1024.png`,
  `/tmp/centered.png`, `/tmp/cumsum.png`, `/tmp/mapped.png`, `/tmp/gap1_mesh.png`
- Batch descriptor dump: §2 table above (from live YMG via range-iso)

## 7. Checkpoint

`~/workspace/agent-ops/checkpoints/wmxix-100-retail-skinning.json` → status `blocked`
with notes pointing to this report. The blocker is the unknown vertex position
encoding; the unblock path is DOL RE (§5).
