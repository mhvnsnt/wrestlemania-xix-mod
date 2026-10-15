# WrestleMania XIX Mod

A clean workspace for research, tooling, and user-created mods for **WrestleMania XIX**. The original game files are intentionally not included; add your own local game dump/files when ready and keep them out of public commits unless you have the rights and permission to distribute them.

## Complete teardown mirror (2026-10-15)

The full WrestleMania XIX (GameCube, GW9E78) teardown is mirrored here under `teardown/` — 1,691 files copied 1:1 from the western-heart repo (`teardown/wmxix/` + `teardown/wwe-wrestlemania-xix/`), which remains the canonical home. This mirror exists so modding work can reference the complete reverse-engineering output in one place.

**What's in `teardown/wmxix/`:**
- `wrestlers/` — 126 extracted wrestler model OBJs (slots 000–110, alt attires)
- `animations/` — 170 YANM skeletal animations decoded to JSON (ringmotion a/b/c/d groups)
- `arenas/` — 43 arena OBJs (ring + Revenge Mode environments)
- `caw-parts/` — 2,690 Create-A-Wrestler parts catalog (`CATALOG.md`, `files.tsv`)
- `textures/` — extracted textures
- `docs/` — format research: YOBJ/YANM/YCG decode notes, wrestler skeleton (70 bones, fully decoded), CAW edit-data layout, Yukes-vs-AKI animation comparison, retargeting notes
- `tools/` — extraction scripts (`extract_wrestlers.py`, `extract_yanm.py`, `extract_arena_textures.py`, `decode_tpl.py`, `catalog_caw.py`, GCN FST reader)

**Formats decoded:** YOBJ (meshes), YANM (skeletal animation), YCG (joint detail), ATR/DATA (animation event timelines), TPL/TXTR (textures), GCN FST (disc filesystem).

**Known gaps (in progress):** YOBJ per-strip skinning assembly, CAW `.gci` save-record layout (needs a real Dolphin save dump), wrestler slot→identity mapping, Revenge Mode arena design docs.

## Project status

- [x] Repository located and verified
- [x] Project scope and safe asset-handling notes
- [ ] Identify game archive/container formats from user-provided files
- [x] Build a read-only inventory/report tool
- [x] Add read-only signature inspection and candidate YDSP scan
- [ ] Add format-specific extract/replace tools only after formats are verified
- [ ] Run and verify tests in the repository's CI
- [ ] Test on backups and document reproducible steps

## Layout

- `docs/` — research notes, workflow, and implementation plan
- `tools/` — project-owned utilities (add only when the format is understood)
- `assets/reference/` — optional user-created reference images and notes; no game dumps
- `mods/` — source files for original or authorized mod work
- `build/` — generated output; ignored by Git

## Working principles

1. Work from a backup; never overwrite the only copy of game data.
2. Start with file inventory and metadata before attempting edits.
3. Preserve original files and record hashes for any file that is modified.
4. Keep proprietary game data, extracted assets, keys, and large binary dumps out of Git unless distribution is explicitly permitted.
5. Prefer small, documented, reversible changes.
6. Do not assume tools or file formats from another game are compatible. Verify each format against actual WrestleMania XIX files.

## First milestone

Once the game files are added locally, record the platform/version and a file listing (names, sizes, extensions). Use that inventory to choose the next investigation step without uploading the game itself.
