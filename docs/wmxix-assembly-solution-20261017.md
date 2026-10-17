# WMXIX Wrestler Assembly - SOLUTION (2026-10-17)

## Status: WORKING — Recognizable humanoid assembled!

## The Solution

### 1. Axis Permutation (Y-Z-X file order)
The YMG file stores bone transform coordinates in **Y-Z-X order**, not X-Y-Z.
- File: [Y, Z, X] → World: [Z, Y, X] via permutation (1,0,2)
- worldX = JSON[1], worldY = JSON[0], worldZ = JSON[2]
- This produces a VERTICAL skeleton (all other perms give horizontal)

### 2. Bone Scale: /100 (centimeters to meters)
Bone positions in JSON are in centimeters (or 1/100 units).
- Bones /100 → skeleton height 1.59m (close to expected 1.8m)
- Bones /64 → skeleton height 2.49m (too tall)

### 3. Vertex Scale: /2500
Vertex s16 values divided by 2500 give correct body proportions.
- /64 → 57m bbox (wrong)
- /1000 → 4.5m bbox (close but big)
- /2500 → 2.2m bbox with correct proportions!

### 4. Translation-Only Transform (NO rotation)
Vertices are positioned by bone TRANSLATION ONLY, not full matrix.
- `world_vert = vert_local + bone_world_pos`
- Full rotation matrices scatter the parts (57m bbox)
- Translation-only gives anatomically correct stacking!

### 5. Batch→Bone Mapping (material names)
- batch 0 (hhh_body) → Bip Spine1 (3)
- batch 1 (hhh_arm) → Bip L UpperArm (40)
- batch 2 (hhh_hand) → Bip L Hand (43)
- batch 3 (hhh_waists) → Bip Pelvis (1)
- batch 4 (hhh_l_leg) → Bip L Thigh (65)
- batch 5 (hhh_knee) → Bip L Calf (67)
- batch 6 (hhh_foot) → Bip L Foot (68)
- batches 7-12 (head/face) → Bip Head (5)

## Results
- **606 verts** (13 base batches), **580 tris** (strip triangulation)
- Bbox: [0.77, 2.22, 1.27]m — anatomically correct proportions!
- Y-positions: head ~1.0, torso ~0.7, pelvis ~0.38, thigh ~0.27, calf ~-0.13, foot ~-0.63
- Render: `teardown/wwe-wrestlemania-xix/work/wrestler-output/wrestler_000_trans_views.png`
  shows recognizable humanoid in front/side/top views!

## Files
- OBJ (points): `teardown/wwe-wrestlemania-xix/work/wrestler-output/wrestler_000_trans.obj`
- OBJ (faced): `teardown/wwe-wrestlemania-xix/work/wrestler-output/wrestler_000_trans_faced.obj`
- Render: `teardown/wwe-wrestlemania-xix/work/wrestler-output/wrestler_000_trans_views.png`

## Remaining Work
1. Table1 detail verts (1254 verts: head details, fingers, etc.) — same transform should apply
2. Refine batch→bone mapping for head batches (currently all → Head bone)
3. Verify strip triangulation produces clean mesh (not just point cloud)
4. Test on other wrestler slots (001, 002, etc.)
5. The /2500 vert scale and /100 bone scale need DOL verification for ground truth

## Key Insight
The game uses translation-only positioning for these batches — the verts are
pre-oriented in bone-local space and just need to be placed at the bone's
world position. This is common for rigid body parts in wrestling games.
