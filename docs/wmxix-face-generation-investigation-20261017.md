# WMXIX Face Generation Investigation (2026-10-17)

**Branch:** `lane/skinning-assembly-100-retail`  
**Status:** BLOCKED — point cloud incoherent, transform must be fixed first

## Summary

Investigated face generation for the 1860-vert wrestler point cloud. Tested all primitive types and geometric reconstruction methods. **Critical finding: the point cloud is not a coherent humanoid — dimensions are wrong, indicating the bone transform from commit ef77d9f is incorrect.**

## Point Cloud Analysis

**Measured dimensions (wrestler_full.obj):**
- Base batches (606 verts): 2.6m wide × 0.9m tall × 0.9m deep
- Table1 (1254 verts): 3.5m wide × 3.3m tall × 2.4m deep
- **Expected for humanoid:** ~0.5m wide × 1.8m tall × 0.3m deep

The point cloud is scattered, not a recognizable humanoid. 3D visualization confirms incoherence.

## Face Generation Attempts (all failed)

| Method | Result |
|--------|--------|
| Sequential triangles (every 3 verts) | Jumbled mess |
| Triangle strips (file order) | Jumbled mess |
| Triangle strips (jump detection, thresh 0.2/0.3/0.5) | Jumbled mess, fragile |
| Triangle strips (per-batch, transformed space) | Jumbled mess |
| Quads (every 4 verts) | Jumbled mess |
| Delaunay per-batch (2D projection) | Convex hull artifacts |

## Key Discoveries

### 1. Draw Records Found (103 records)
Located in YMG Table1 region (0x5ae0-0x7ca0). Format:
- 16 bytes: [bone0:u8][bone1:u8][bone2:u8][variant:u8][vcount:u32][wptr:u32][skip:u8][resync:u8]
- Bone pairs like (68,66), (34,23), (22,20) — adjacent bones for skinning
- Variant 2 = multi-bone, Variant 3 = 2-bone
- Total verts in records: 1706 (close to 1860, some false positives in pattern match)

These are REAL draw records from the game's data, but they don't contain face indices — only bone assignments and vertex counts.

### 2. No Index Buffer Exists
Systematic search of YMG file found no valid u16 index buffer. The "index-like" patterns were false positives (vertex coordinate data misinterpreted).

### 3. File Has No Normals
Confirmed: 6B verts (s16x3 positions only). The 12B runtime format (pos+normal) is built by the loader, which must compute normals — implying faces exist somewhere, but not found in YMG.

### 4. DOL Has File Format Registry
At 0x30b2b0: POF0(1), YOBJ(2), YANM(3), POFE(-2), DUMY(-1) with loader function pointers. Confirms YOBJ is a registered format, but doesn't help with faces.

## Root Cause

The bone transform applied in ef77d9f ("bone-local zyx rotation + translation-only FK + Y-flip") produces an incoherent point cloud. Possible issues:
- Wrong bone mapping (batches assigned to wrong bones)
- Wrong rotation order or Euler angles
- Wrong coordinate system (Y-up vs Z-up)
- Table1 verts use different transform than base batches
- Scale factors incorrect (/4096 for base, /16384 for Table1 may be wrong)

## Recommended Next Steps

1. **Fix the transform first.** The point cloud must be a coherent humanoid before faces can be generated.
   - Verify bone mapping against skeleton
   - Check a single batch (e.g., batch 4 leg) in isolation with different transforms
   - Compare against the working "final_simple.png" from the breakthrough

2. **Once point cloud is coherent**, revisit face generation:
   - The draw records give bone assignments in draw order
   - If runtime vertex order can be reconstructed, strips may work
   - Otherwise, use the draw record boundaries as strip boundaries

3. **Alternative:** Find the YMG loader in the DOL to understand how draw records become GX commands.

## Files
- This doc: `docs/wmxix-face-generation-investigation-20261017.md`
- Test renders: `/tmp/wrestler_tris_matplotlib.png`, `/tmp/wrestler_strips.png`, `/tmp/wrestler_quads.png`, `/tmp/base_strips_transformed.png`, `/tmp/batch4_delaunay.png`, `/tmp/base_3d.png`, `/tmp/wrestler_analysis.png`
