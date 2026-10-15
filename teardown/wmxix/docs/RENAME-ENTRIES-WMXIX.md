# WMXIX Rename Entries — for RENAME-MAP.md (parent to append after PR #144 merges)

**Universe name:** `mat-legends` (per RENAME-MAP.md universe table)
**Status:** PLANNED ONLY — do NOT execute until watchdog lane (wrestling-game-teardown) completes.
Reason: watchdog tools/docs reference `teardown/wmxix/` and `teardown/wwe-wrestlemania-xix/` paths actively.

## Planned Renames (old → new)

| OLD | NEW | Status |
|-----|-----|--------|
| `teardown/wmxix/` | `teardown/mat-legends/` | PLANNED (post-watchdog) |
| `teardown/wwe-wrestlemania-xix/` | `teardown/mat-legends-research/` | PLANNED (post-watchdog) |
| `teardown/wmxix/wrestlers/000_0.obj` … (126 OBJs, slots 000–110) | `teardown/mat-legends/wrestlers/<WH-name>.obj` | BLOCKED — owner creates WH character names (char_inventory worker) |
| `teardown/wmxix/animations/*.json` (170 YANM) | `teardown/mat-legends/animations/<WH-name>.json` | PLANNED (post-watchdog) |
| `teardown/wmxix/caw-parts/` (2,690) | `teardown/mat-legends/caw-parts/` | PLANNED (post-watchdog) |
| `teardown/wmxix/arenas/` (43 OBJs) | `teardown/mat-legends/arenas/` | PLANNED (post-watchdog) |
| `WWE Wrestlemania XIX (USA).iso` (release wmxix-iso-v1) | `mat-legends.iso` | PLANNED (rename on TeraBox copy) |

## TeraBox Stage 1 (needs parent browser lane — subagent cannot browse)

- [ ] WMXIX ISO → TeraBox (currently GitHub release wmxix-iso-v1 ONLY; TeraBox presence unconfirmed)
- [ ] western-heart/teardown/mat-legends/ (post-rename) → TeraBox
