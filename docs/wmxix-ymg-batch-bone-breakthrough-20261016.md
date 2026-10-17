# WMXIX YMG Batch→Bone Breakthrough (2026-10-16)

**Branch:** `lane/skinning-assembly-100-retail`  
**Status:** MAJOR PROGRESS — coherent body-part clusters achieved!

## Breakthrough Findings

### 1. File verts are 6B (s16x3), NOT 12B
The DOL consumer reads 12B/vert (6× s16) from the RUNTIME buffer, but the YMG FILE stores 6B/vert (3× s16 positions only). The loader expands 6B → 12B at load time (adding normals/padding).

**Proof:** Reading as 12B, the "normal" of vert N equals the "position" of vert N+1 in 6B view. The data is a continuous s16x3 stream.

### 2. Scale: verts /4096, bones /64
- **Bones:** float32 positions / 64 = meters (proven: UArm→Forearm 0.47m, Neck→Head 0.21m)
- **Verts:** s16 positions / 4096 = meters (bone-local offsets)
  - Example: vert (700, 567, 1488) / 4096 = (0.171, 0.138, 0.363)m from bone origin — plausible!

The 64× ratio (4096/64) reflects different fixed-point representations, not an error.

### 3. Translation-only works (rotation TBD)
Applying bone world-position (translation only, no rotation) to verts/4096 yields coherent body-part clusters:
- Batch 4 (hhh_l_leg) → Bip L Thigh (66): **clear vertical leg shape!**
- Batch 0 (hhh_body) → Bip Spine1 (4): central torso mass
- Other batches cluster in plausible anatomical positions

Full rotation matrices (zyx) scatter the parts — the YMG euler angles may be for a different purpose, or the rotation order/space is wrong. Translation-only is the working baseline.

### 4. Table1 is a separate mesh system
Table1 at 0x5ae0 (110 records, 61 bones including facial/finger detail) does NOT match the 13 batch verts. It's likely a high-detail overlay (face, hands) or a different LOD. The 13-batch table at 0x7ca0 is the main body mesh.

### 5. Batch table layout confirmed
8-byte records at 0x7ca0: `[idx:u8][cnt:u8][0x00:u8][cnt_dup:u8][doff:u32be]`
- doff is from base 0x80
- 13 batches, 606 verts total, 6B/vert

## Current Best Render
`teardown/wwe-wrestlemania-xix/work/dol-analysis/final_simple.png`
- 6B/vert, /4096 scale, bone/64 translation-only
- Hypothesized batch→bone map (texture-name based)
- Body parts cluster correctly; leg is clearly recognizable!

## Remaining Work
1. **Refine batch→bone mapping:** Current map is hypothesized from texture names. Some batches may need different bones.
2. **Rotation:** Determine correct rotation application (or prove translation-only is sufficient for the base mesh).
3. **Assemble full body:** Once mapping is refined, generate OBJ and verify.
4. **Table1:** Determine if it's needed for the full render or a separate system.

## Files
- Render scripts: `teardown/wwe-wrestlemania-xix/work/dol-analysis/final_simple.py` (to be created from inline)
- Renders: `final_simple.png` (best so far), `table1_*.png`, `batch6b_*.png`, `scale_*.png`
