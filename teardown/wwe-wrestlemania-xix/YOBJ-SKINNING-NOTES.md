# YOBJ per-strip skinning — investigation notes (2026-10-13)

## Hypothesis tested
Batch s16x3 runs are bone-local positions; applying per-batch bone bind-world
matrices assembles the posed mesh.

## Result: REJECTED by measurement
Tested transforms on 000_0.ymg (13 batches, 606 verts):
- A: batch verts as bone-local → hierarchical bone world matrix — SCATTERED
- B: inverse bind (unpose) — SCATTERED
- C: translation-only — SCATTERED
- D: bone LOCAL matrix only — SCATTERED
- 6 axis permutations of raw batches — all SCATTERED (no head-like shape)
- Material-table (pos,nrm,uv) triplets → position pool @0x7D88 — SCATTERED

## Measurements
- Batch bboxes ALL span ~0–1900 raw units in every axis (not bone-local clusters).
- Material table: 20-byte records (CORRECTION to v2 doc's "28 bytes"):
  [u16 one][u16 idx_off][RGBA×4]; 15 valid materials, idx_off 0x830–0xD10.
- Material index chunks: 46 u16s = 15×(pos_idx,nrm_idx,uv_idx) + terminator;
  pos_idx range 0–1842 (global pool).
- 000_0.ymg == 000_1.ymg BYTE-IDENTICAL (69,176 B, 0 differing bytes).
  The _1 "alt attire" is texture-only (000_1.tex differs); geometry assembly
  needs only 000_0.
- Full bulk region (0x80–0xF338) as s16x3: 10,356 triplets, median consecutive
  dist 1667 (vs 160 for batch runs) — mixed data, not a single vertex array.

## Open
The batch s16x3 data does not resolve to coherent head geometry under any
tested interpretation. Either the dequantization is wrong (not s16/64), the
batches need per-VERTEX (not per-batch) skinning weights from an unlocated
table, or the "positions" are delta-encoded. The elbow CAW part (148 verts)
did render as a coherent shell, so the s16/64 reading is valid for RIGID parts.
Deeper RE needed: locate weight table, or find the true position pool that
material indices 0–1842 reference.
