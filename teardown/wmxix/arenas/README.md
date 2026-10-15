# WMXIX Arena Extracts

43 arena geometry files extracted from WWE WrestleMania XIX (GameCube).

## Format
- **OBJ point clouds** (vertices only, no faces yet)
- **Vertex format:** f32 triplets, CRACKED 2026-10-13
- **Total:** 324,425 vertices across 43 files

## Files
- `00.obj`, `01.obj`, `02.obj` — main arenas
- `0_0.obj` through `2_2.obj` — bs/ sub-arenas
- `ring.obj` — wrestling ring (809 verts)
- `kaijo_x8.obj` — arena (14,170 verts)
- `*_ad2.obj` — detail/LOD variants
- `ARENA-FORMAT.md` — full format documentation
- `extract_all_arenas.py` — extraction tool
- `yobj_arena_extract.py` — single-arena extractor

## Status
✅ Vertex positions: CRACKED (f32, verified via renders)
⚠️ Face indices: OPEN (see ARENA-FORMAT.md for details)

## Renders
Point-cloud renders confirmed correct geometry:
- bg/00 = full arena bowl
- ring.ymg = wrestling ring with posts
- kaijo_x8 = arena structure

## Next
Parse mesh descriptors to link vertex arrays to index arrays,
or use Blender Poisson reconstruction on point clouds.
