# WMXIX Arena Faces — Reconstructed Meshes (2026-10-16)

**Lane:** ARENA FACE DECODE (WMXIX 100% Retail), worker (b)
**Tool:** `teardown/wmxix/tools/reconstruct_arena_faces.py`
**Status:** 37 of 40 arenas → mesh OBJ (verts + faces); 3 → documented points fallback.

## What this is

The arena OBJs in `teardown/wmxix/arenas/` are vertex-only point clouds extracted
from YMG files (f32 triplets). The YMG face-index records were cracked for one
material group (see `ARENA-FORMAT.md`), but no YMG/ISO is available locally, so
ground-truth faces are unrecoverable. These meshes are **algorithmic
reconstructions** from the point clouds — every face comes from a deterministic
reconstruction algorithm, never hand-patched.

## Pipeline (per position array, per spatial component)

The extractor mixed position arrays with normal/UV attribute arrays. The
pipeline first drops attribute runs (long runs with all |components| < 3.0),
then reconstructs each position array with a cascade:

1. **GRID** — axis-aligned structured grids → quad faces between grid neighbors
   (mat slabs, box posts). Outward winding from neighbor occupancy.
2. **LOOP-STACK** — closed loops stacked along one axis:
   - dense smooth loops (≥16 pts/level) + curve-like (local-PCA linearity) → **TUBE**
     (parallel-transport frames; radius = 0.25× point spacing — documented estimate)
   - faceted loops → **convex HULL** if the part is a sampled solid, else **BRIDGE** band
3. **GAP-SPLIT** — recursively split at the largest 1D gap separating two compact
   groups; reconstruct each piece (stops alpha-shapes bridging separate parts).
4. **CONVEX HULL** (Qhull) — accepted only when most points are hull vertices and
   nearly every hull triangle has nearby samples.
5. **ALPHA SHAPE** — Delaunay boundary at 2×/4×/8×/16× point spacing, with a
   bridge guard (rejects triangles floating far from samples).
6. **POINTS fallback** — documented per component with the reason.

Acceptance per mesh: ≥8 triangles, zero degenerate faces, sane edge lengths,
≥30% of input points used, <15% bridge triangles.

Outputs: `faces/<arena>.obj` (merged) + `faces/parts/<arena>_p<N>.obj` (per part —
parts live in different local frames for the ring; the integrator positions them).
`MANIFEST.json` records per-component method/counts/fallback reasons.

## The ring (ring.obj) — 4 parts, 1092 faces ✅ own-eyes verified

| Part | Method | Faces | Notes |
|------|--------|-------|-------|
| Octagon trim | convex_hull | 24 | 16-pt chamfered-octagon prism |
| Post plate | convex_hull | 28 | 104×642×642 box |
| Ropes (2) | loopstack tubes | 896 | rounded-rect loops, r≈21 (estimate) |
| Mat sides (2) | gap_split → alpha_shape | 144 | sparse; lumpy but valid |

Render: ring mesh verified in Blender (Cycles) — ropes read as tubes, solids closed.

## Arena status

37 meshes, 3 points fallbacks. Arena clouds are **sparse wireframe/edge/text
samplings** (e.g. 02.obj: 4859 pts over a 24000-unit arena, incl. text signage
strokes and truss lines) — not dense surface scans. Meshes cover the solid-like
parts; thin/linear/text fragments fall back to points.

Points fallbacks (render as THREE.Points with original positions):
- **eff_x8.obj** — 59 arrays of 5–7 pts: effects/sprite data, not surface geometry.
- **post.obj** — 30 verts in tiny arrays: too sparse for any surface method.
- **0_1_ad2.obj** — 92-pt component too thin/noisy + 7-pt fragment (LOD variant).

## Honest limitations

- These are **approximations**, not the original retail meshes. True retail faces
  need the YMG index records (see ARENA-FORMAT.md face-index crack) — when a YMG
  or ISO is available, `tools/yobj_arena_faces.py` extracts ground truth.
- Rope tube radii are estimated (0.25× spacing); true radii are in the YMG.
- Arena parts are positioned in world frame (coherent scene); ring parts are in
  separate local frames (node transforms were in the YMG, unavailable).
- Text signage (e.g. 02.obj arr1, 1971 pts) is mostly points — 3D text extrusion
  is future work.
- No vertex colors in the source OBJs; meshes are uncolored (testbed materials apply).

## Verification

- Ring: own-eyes Blender render (4 parts, 1092 tris) — verified.
- 02.obj: mesh (2508 faces) + points fallback manifest — rendered, partial.
- All 40 OBJs parse as valid `v`/`f` (loader-checked).
