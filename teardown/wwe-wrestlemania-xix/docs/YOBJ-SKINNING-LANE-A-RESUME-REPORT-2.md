# Lane (a) SKINNING DECODE — Watchdog Resume Report #2 (2026-10-16 ~08:41-09:00 EDT)

**Checkpoint:** `wmxix-100-retail.json` (parent coordinator, attempts 0→1, status stays `blocked`)
**Task:** WMXIX 100% Retail — lane (a) batch→bone mapping still the only open sublane
(lanes b/c/d + dolre all done/merged).

Continues from YOBJ-SKINNING-LANE-A-RESUME-REPORT.md §3 open items:
1. limbs not in 000_0.ymg → check `//edit_data/MODEL/Man/` parts
2. batch→bone mapping still unresolved

## 1. edit_data limb parts extracted and decoded — NOT limbs

Pulled 6 YMG parts from the split ISO parts in `~/workspace/wmxix-iso/`
(concat order part_00,aa,ab,ac verified byte-exact against the already-pulled
000_1.ymg) via offsets from docs/WMXIX-FILE-LISTING.txt:

| file | ISO off | size | batches | b0 range | verts/batch |
|---|---|---|---|---|---|
| Lower_Body/mc0_000/c7.ymg | 0x05D9C9C8 | 12052 | 5 | 0–4 | 11–22 |
| Lower_Body/mc0_000/l3.ymg | 0x05D9F8DC | 6680 | 1 | 0 | 15 |
| Lower_Body/mc0_000/r3.ymg | 0x05DA12F4 | 6648 | 1 | 0 | 13 |
| Upper_Body/mu0_000/c6.ymg | 0x05E92C44 | 17300 | 3 | 0–2 | 18–69 |
| Upper_Body/mu0_000/l0.ymg | 0x05E96FD8 | 6936 | 1 | 0 | 18 |
| Upper_Body/mu0_000/r0.ymg | 0x05E9A428 | 6904 | 1 | 0 | 15 |

Decoded with the a2-proven `get_batches` (s16x3 positions). All decode cleanly
with local coordinates (~0–30 units). These are small CAW clothing layers
(elbow pads, etc.), each a single rigid-ish piece — **not** the missing arms/legs.
Every one of them uses only b0 ∈ {0..4}, consistent with b0 indexing a
per-file batch/material list, not a global bone palette.

Files: `teardown/wwe-wrestlemania-xix/work/edparts/*.ymg`

## 2. `//model/wrestler/*_2.ymg` (and 001_1/005_2) are DUMY placeholders

Pulled 003_2.ymg (0x0C9851F4, 54848B), 001_1.ymg (0x0C7BC5B8, 73304B),
005_2.ymg (0x0CB88DE4, 36392B) — all start with `DUMY`. The disc contains
no hidden limb files in the wrestler slots; each slot's real mesh is only
`_0` (+ `_1` duplicate). So limbs, if present, must be inside `_0`'s
batch gap data.

## 3. Gap data as u16x3 limb geometry — REJECTED (own-eyes)

Hypothesis: the 0.5–5KB `s16x3`-like data after each batch's `c1*6` positions
is additional geometry (limbs). Test: parse each batch's
[pos_end, next_batch_doff) region as u16x3, split strips at jumps >1000 raw
units, triangulate, render.

Result: scattered junk in every batch (see render in this report's commit).
Batch0 gap: 3498B → 583 verts, median step 192 but bimodal junk;
batch3: 72 strips of noise; batch12 gap hits 65535 (s16 negatives mixed in).
NOT limbs, NOT smooth geometry. Gap data is some other stream
(weights? material runs?) — semantics still OPEN.

## 4. Status / next

- batch→bone mapping: still unresolved. b0→bone disproven (resume report #1).
  New constraint: CAW parts use only b0 ∈ 0–4, so b0 is per-file, not global.
- Limbs: not in edit_data parts, not in placeholder `_N` files, not the
  batch gap regions as plain geometry. Candidates left: (a) gap data in a
  different encoding; (b) Table1 16-byte records' `(u16,0)` payloads
  (YOBJ-BATCH-SEMANTICS.md); (c) limbs live in a different file family
  entirely (`//model/` outside `wrestler/` — check FILE-LISTING for
  other YMG families, e.g. `//model/` common dirs).
- (c) is the cheapest next test: census all `*.ymg` paths in
  docs/WMXIX-FILE-LISTING.txt outside `model/wrestler/` and `edit_data/MODEL`,
  look for arm/leg-sized files (>40KB, non-DUMY).

**Artifacts this run:** `teardown/wwe-wrestlemania-xix/work/edparts/`
(6 decoded CAW YMGs), this report. Render: /tmp/wmxix_gap_test.png
(gap-as-geometry rejected — kept in /tmp, not committed).
