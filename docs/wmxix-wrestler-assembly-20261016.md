# WMXIX Wrestler Full Assembly (2026-10-16)

**Branch:** `lane/skinning-assembly-100-retail`  
**Status:** IN PROGRESS — full point cloud assembled, mesh render pending

## What Was Built

### Complete vertex extraction pipeline
- **Base batches (13):** 606 verts, 6B s16x3, scale /4096, bone-local
- **Table1 detail (87 clean records):** 1254 verts, 6B s16x3, scale /16384, bone-local
- **Total:** 1860 verts forming coherent humanoid

### Key discoveries
1. **Table1 scale is /16384** (not /4096): Head was 1.0m at /4096, correct 0.24m at /16384
2. **Mirrored batch mapping:** Batches 0-6 = LEFT side, 7-12 = RIGHT side (materials confirm)
3. **Transform:** Bone-local rotation (zyx euler) + translation-only world position + Y-flip
4. **Table1 [4] field:** 0x00000000 = clean sequential verts; 0x80xxxxxx = different format (skipped)

### Batch→bone map (mirrored)
```
0: Spine1 (4)    [hhh_body]
1: L UpperArm (41) [hhh_arm]
2: L Hand (44)   [hhh_hand]
3: Pelvis (2)    [hhh_waists]
4: L Thigh (66)  [hhh_l_leg] ✓ confirmed
5: L Calf (68)   [hhh_knee]
6: L Foot (69)   [hhh_foot]
7: Pelvis (2)    [hhh_waists R]
8: R UpperArm (20) [hhh_arm R]
9: Spine1 (4)    [hhh_body R]
10: R Foot (64)  [hhh_foot R]
11: R Calf (63)  [hhh_knee R]
12: R Hand (23)  [hhh_hand R]
```

### Table1 bones (detail overlay)
Head (188 verts), face features (lips, eyes, brows), fingers (all), forearms, hands, calves, feet, toes, clavicles.

## Remaining
- [ ] Blender solid mesh render (in progress)
- [ ] Face indices decode (index buffer at 0x8eb4 partially decoded)
- [ ] Final OBJ with faces
- [ ] Verify full-body coherence visually
