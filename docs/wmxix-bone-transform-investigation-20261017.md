# WMXIX Bone Transform Investigation (2026-10-17)

**Branch:** `lane/skinning-assembly-100-retail`  
**Status:** BLOCKED — correct parameters found, but assembly still incoherent

## Confirmed Correct Parameters

### 1. Vertex scale: s16 / 64 (NOT /4096)
- `teardown/wwe-wrestlemania-xix/tools/yobj_vertex_decode.py` line 14: "Scale: s16 / 64 (matches GX s16 vertex with 6 frac bits; skeleton units)"
- Line 65: `verts / 64.0`
- The breakthrough's "/4096" was WRONG.

### 2. Euler order: XYZ (NOT ZYX)
- `tools/assemble_wrestler.py` line: `R = Rx(euler[0]) @ Ry(euler[1]) @ Rz(euler[2])`
- This is XYZ intrinsic order.

### 3. Bone data: precomputed in JSON
- `teardown/wwe-wrestlemania-xix/docs/wrestler-skeleton-000.json` (70 bones)
- Each bone: index, parent, pos (raw float, used directly), euler_xyz, name
- Bone indices match YMG order (idx=4 is Neck, idx=65 is L Thigh)

### 4. Transform: full 4x4 matrix
- `w = M @ [v, 1]` where M is bone world matrix from FK
- Verts are transformed by the bone's FULL world matrix (rotation + translation)

## Existing Tool

`tools/assemble_wrestler.py` — fully working pipeline:
- Parses YMG batches via `yobj_vertex_decode.get_batches()`
- Loads skeleton from JSON
- Applies batch→bone mapping (default: b0→bone, which is WRONG)
- Triangulates strips via `strip_triangles()`
- Outputs OBJ with faces + render

The tool's docstring admits: "the batch->bone mapping (b0 -> bone) places batches near spine/face bones but does NOT yield limbs; the true mapping is unresolved."

## Corrected Mapping Attempted

Based on material names:
- batch 0 (hhh_body) → Bip Spine1 (3)
- batch 1 (hhh_arm) → Bip L UpperArm (40)
- batch 2 (hhh_hand) → Bip L Hand (43)
- batch 3 (hhh_waists) → Bip Pelvis (1)
- batch 4 (hhh_l_leg) → Bip L Thigh (65)
- batch 5 (hhh_knee) → Bip L Calf (67)
- batch 6 (hhh_foot) → Bip L Foot (68)
- batches 7-12 (face/head parts) → Bip Head (5)

**Result:** Still scattered, not a coherent body. Bbox 200×57×123 (in /64 units) = 3.1×0.9×1.9m.

## What's Wrong

The batch→bone MAPPING is not the only problem. Even with correct mapping, the transform doesn't place batches anatomically. Possible issues:

1. **Bone world matrices are wrong.** The FK might be incorrect (wrong parent chain, wrong matrix composition order).
2. **Verts need inverse bind pose.** In skinning, verts are often in bind-pose model space, and the transform is `C * B^-1 * v`. If YMG verts are in bind-pose space, I need the inverse bind matrices.
3. **Batches are not rigid.** They might be skinned (multi-bone weights), not rigidly attached to one bone.
4. **The "batches" are not body parts.** They might be something else entirely (LOD pieces, shadow volumes, etc.).

## Key Realization

The previous agents (including the "breakthrough") were working with WRONG parameters (/4096 scale, ZYX order). All their "coherent" results were based on incorrect transforms. The `assemble_wrestler.py` tool has the RIGHT parameters but the WRONG mapping.

## Next Steps

1. **Verify the FK.** Recompute bone world matrices from JSON and verify the skeleton is anatomically correct (measure bone distances).
2. **Test inverse bind pose.** If verts are in bind-pose model space, try `world = vert` (no transform) at /64 scale and see if it's a body.
3. **Brute-force the mapping.** For each batch, try every bone and measure which gives the most "connected" result.
4. **Check if batches are skinned.** Look for bone weight data in the YMG file.
5. **Find the DOL loader.** Disassemble the YOBJ loader to see the exact transform.

## Files
- This doc: `docs/wmxix-bone-transform-investigation-20261017.md`
- Test OBJs: `/tmp/test_assemble.obj` (default mapping), `/tmp/test_correct.obj` (corrected mapping)
- Renders: `/tmp/correct_mapping.png`, `/tmp/batch_assembly_debug.png`, `/tmp/batches_isolated.png`
