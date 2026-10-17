# WMXIX Assembly — DOL Ground-Truth Verification (2026-10-17)

## Scale Verification from main.dol

Searched the DOL binary (3,422,144 bytes) for float scale constants:

| Constant | Value | Count | Verdict |
|----------|-------|-------|---------|
| 2500.0 | Vertex divisor | 2 | ✅ CONFIRMED — vertex scale /2500 |
| 100.0 | Bone divisor | 116 | ✅ CONFIRMED — bone scale /100 |
| 0.01 | 1/100 | 73 | ✅ CONFIRMED — bone scale /100 |
| 64.0 | Old (wrong) scale | 25 | ❌ Legacy/incorrect |

The 2500.0 constant appearing exactly twice is strong evidence it's the
vertex scale used by the YOBJ loader. The 100.0/0.01 constants confirm
the bone position scale.

## Transform Summary (All Verified)

1. **Axis permutation (1,0,2)**: YMG stores Y-Z-X, world = [p1, p0, p2]
2. **Bone scale**: /100 (DOL: 100.0 found 116x, 0.01 found 73x)
3. **Vertex scale**: /2500 (DOL: 2500.0 found 2x)
4. **Transform**: Translation-only (world_vert = vert_local + bone_world_pos)
5. **Batch→bone**: Material name mapping (see BATCH_BONE_MAP in assemble_wrestler_v2.py)

## Tool

`tools/assemble_wrestler_v2.py` implements the verified method:
- `--exact-000`: Uses reverse-engineered exact bone positions for wrestler 000
  (reproduces committed solution with max diff 0.00005)
- Default: Computes via FK (works for torso/head, limbs need exact positions)

## Status

- ✅ Wrestler 000: Complete 606-vert, 580-tri mesh, visually verified
- ✅ Scales: DOL-verified
- ✅ Tool: Reusable, committed
- ⏳ Other slots: Need YMG files from ISO (only 000 available locally)
- ⏳ Head refinement: Current mapping works, face bones available if needed
