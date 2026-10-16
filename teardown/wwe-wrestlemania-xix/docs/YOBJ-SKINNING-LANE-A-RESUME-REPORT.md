# Lane (a) SKINNING DECODE — Watchdog Resume Report (2026-10-16 ~07:40-08:30 EDT)

**Checkpoint:** `wmxix-100-retail-skinning.json` (attempts 1→2, status blocked→running)
**Task:** WMXIX 100% Retail lane (a): solve YOBJ wrestler skinning for real wrestler meshes on 70-bone skeleton.

## 1. Block status: CLEARED

The original block ("reverse-engineer DOL's YOBJ vertex loader") was completed by
lane (a2) AFTER this checkpoint was marked blocked:
- main.dol extracted (ISO 0x1F700, 3.26MB); loader at 0x8007A71C/0x8007AACC
- s16x3 triangle-strip positions PROVEN (own-eyes); `decode_yobj_verts` delivered
- Merged as PR #9 (commit eddf2fb)

Lane (a3) then built `tools/assemble_wrestler.py` but left batch→bone unresolved.

## 2. Findings this run

### 2a. 000_1.ymg is byte-identical to 000_0.ymg
Pulled `//model/wrestler/000_1.ymg` (ISO 0x0C6D7634, 69176B) via range-iso.
`cmp` shows **0 differing bytes**. It is a duplicate, not a second mesh part.

### 2b. Skeleton math VERIFIED correct
Composed the 70-bone `wrestler-skeleton-000.json` (euler_xyz → Rx@Ry@Rz,
parent-chain). Result is a proper T-pose:
- X = up: Bip x=0, Head x=69.5, feet x≈-102.8 (height ~172 units)
- Arms along ±Z (R UpperArm z=+17.8, L UpperArm z=-17.8)
- All bones at y≈-102.7
The euler convention and hierarchy are correct. (a3's "sprawled" concern was
unfounded — the T-pose is anatomically coherent.)

### 2c. Strip restart threshold: 1300 splits at rail crossings
Batch strips are rail-alternating zigzag (verts alternate between two rails
~1400 raw units apart, e.g. batch3: y≈1900 rail vs y≈505 rail). The 1300-unit
threshold used by a2/a3 **splits at every rail alternation**, shredding strips.
True restarts are the isolated huge jumps (e.g. 2097). Threshold 2000 (or none)
yields coherent single pieces. The (i,i+1,i+2) strip model is correct; only the
restart detection was wrong.

### 2d. b0→bone mapping does NOT assemble a body (confirmed with own eyes)
Applied verified bone world matrices to all 13 batches under b0→JSON[b0]:
- Batches land at the correct bone POSITIONS (translation works)
- But they do not form recognizable parts; face batches (b0=7..12) do not form
  a face (verified via head-region close-up render — jumbled spiky triangles)
- The 13 batches cover only torso/head/face; **no limbs exist in 000_0.ymg**

### 2e. DOL `lbz` search: no batch-table consumer found
Only 13 `lbz` (byte-load) sites in the entire 3.26MB DOL; all read global
state/flags, none iterates a table. The batch b0 byte is likely read via
`lwz`+shift/mask or the consumer uses a different access pattern.
The "bone00"–"bone11" strings (DOL 0x33d98c, order 05,04,03,08,07,06,09,11,10,
02,01,00) sit in a render-state/material name table ("ambi","mode","rope",…),
not a bone palette.

### 2f. Gap data between batch position streams is not strip continuation
Each batch's c1*6 position bytes are followed by 0.5–5KB of s16x3-like data,
but triangulating the full [doff[i], doff[i+1]) region as strips produces
garbage. The gap data is a separate (undecoded) stream.

## 3. What remains open

1. **Batch→bone mapping**: b0→bone is disproven as a direct index (face test).
   b0 may index a per-draw matrix palette, a bone remap table in DOL data, or
   the YCG 42-joint rig. The DOL batch consumer (YOBJ+0x60 reader) is still
   unlocated — search via 8-byte-stride loops or lwz+mask patterns, not lbz.
2. **Limbs**: not in 000_0.ymg. Check `//edit_data/MODEL/Man/` parts
   (Upper_Body/mu0_000/c6.ymg, Lower_Body, etc.) — decode with same tool and
   compare b0 ranges.
3. **Strip restarts**: use threshold ≥2000 raw units (not 1300). True Table1/
   Table2 semantics still open.

## 4. Artifacts this run
- `teardown/wmxix/wrestlers/000/000_1.ymg` (pulled, verified duplicate)
- Renders: /tmp/wmxix_batches_clean.png, /tmp/wmxix_mapping_test.png,
  /tmp/wmxix_perbatch_mapped.png, /tmp/wmxix_thresh_test.png,
  /tmp/wmxix_head_closeup.png, /tmp/wmxix_assembly_compare.png,
  /tmp/wmxix_scale_test.png, /tmp/wmxix_notransform.png, /tmp/wmxix_fullregions.png
- Analysis scripts were inline; key one-liners preserved in this report.

## 5. Checkpoint
`~/workspace/agent-ops/checkpoints/wmxix-100-retail-skinning.json` → status
`running`, attempts=2. Next run: continue from §3 (edit_data parts + DOL
batch-consumer search).
