# YOBJ (u16,0) payload — item 1 hypothesis tests (MEASURED 2026-10-13)

Sample: `model/wrestler/000_0.ymg` (+ 001_0/002_0/003_0.ymg for cross-file).
Tool: `tools/yobj_payload_item1.py` (reproduces all numbers below).

## H1: (pos_idx, nrm_idx) pairs indexing position/normal pools — REJECTED

- The 58-record batch table's v2 payloads are `(u16 a, u16 0)`; `a` ranges
  0–4096 (48 distinct values in 000_0.ymg).
- A position pool for `a` would need ≥4097 entries. The only vertex pools
  located are the 13 skin-batch runs (`@0x7CA0` descriptors): **606 verts**.
  4096 >> 605 — indices do not fit.
- Exhaustive s16x3 scan of 000_0/001_0/002_0/003_0.ymg found no ≥4097-entry
  pool (largest clean runs are the skin batches; inter-run gaps are smooth
  s16x3 but fragmented and overlap material/attribute structures).
- `b` (2nd u16) = 0 for 99.7% of v2 units — degenerate as a normal index
  (would mean every vertex uses normal 0).
- Cross-file: 001_0.ymg uses a different table layout (DUMY wrapper); none
  of the sampled files contain a 4097+ position pool.
- **Verdict: REJECTED.** The `(u16,0)` values are not indices into any
  located position/normal pool.

## H2: 16.16 fixed-point interpretation of u32 (a<<16|b) — NOT DISTINGUISHING

- With `b=0`, the BE u32 `(a<<16)` as 16.16 fixed = `float(a)` — identical
  to the integer reading. No separate float attribute structure was found
  that consumes these as 16.16.
- **Verdict:** not a separate interpretation; reveals no new semantics.

## H3: 12-bit fraction (value/4096) — OPEN (leading hypothesis)

- Values span 0–4096 uniformly-ish (48 distinct for 000_0.ymg); `value/4096`
  ∈ 0.0–1.0 (e.g. 80→0.0195, 2048→0.5, 3723→0.909).
- Per-model: 000_0 and 002_0 share a near-identical value set (48/46);
  003_0 has a different set (59). So the values derive from per-model data,
  not format constants.
- Same 5-value sequences repeat across records with different `b8`
  (e.g. `[2048,3723,2048,3150,1820]` in recs 45/49/51/52) — not per-vertex
  unique data; behaves like a per-model **palette** or quantized parameter.
- 4096 (=0x1000, just above 12-bit max) occurs in runs at record starts
  (recs 31–34), not as a clean end sentinel.
- **Candidates:** 12-bit UV.u coordinate (V unknown — possibly a 1D LUT
  texture, or V stored elsewhere); or normalized per-vertex weights/morph
  params. **Needs texture decode (`.tex`) to confirm/reject.**
- **Verdict: OPEN.** Next step: decode 000_0.tex, check dimensions; if 1D
  or if UV.u ∈ 0–4096 maps cleanly, confirm; else reject.

## What the payload is NOT (all measured)
- Not indices into the 606-vert skin pool (this cycle).
- Not indices into s16x3 pools at [0x80,0x6240)/[0x240,0x6240) (prior cycle).
- Not (x,y) 2D verts (prior cycle, LE; BE re-test: consecutive-pair
  distances median 11462 — not strip-like).
- Not (x, (y,z)) assembly with rec0's 128 pairs (this cycle: partitioned
  per-record consec median ~11000 — REJECTED).
