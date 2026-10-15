# Revenge Mode Arenas — WWE WrestleMania XIX (GameCube)

**Measured from:** `bg/` FST listing (373 files), `docs/WMXIX-FILE-LISTING.txt`
**Revenge Mode:** mission-based mode fighting OUTSIDE the ring in various
environments — this is the arena-traversal reference for Bannon and
Western Heart's wrestling mode.

## Arena sets (measured)

| Location | Files | Contents |
|---|---|---|
| `bg/00.*`, `bg/01.*`, `bg/02.*` | 3 arenas | Main ring arenas: `.tex` + `.ycg` + `.ymg` each, plus `_ent` (entrance), `_gt`, `_light`, `_sc2`, `_scr` variants |
| `bg/bs/` | 61 | **Backstage** areas: `N_M.tex` + `.ycg` + `.ymg` + `_ad2.ymg` (N=area, M=variant) |
| `bg/A0.pac`–`bg/A4.pac`, `bg/C0.pac`... | ~10 | Arena packages (~1.1MB each) |
| `bg/cage/` | 2 | Steel cage structure |
| `bg/object/` | 61 | Interactable/destructible objects |
| `bg/weapon/` | 61 | Weapons (chairs, tables, etc.) |
| `bg/placard/` | 51 | Crowd signs / arena dressing |
| `bg/audi.pac` | 1 | Arena audio package |

## Backstage areas (Revenge Mode environments)

`bg/bs/` uses `N_M` numbering — N = distinct location, M = variant.
These are the out-of-ring fighting environments unique to Revenge Mode.
Each has texture + skeleton + mesh + `_ad2` (additional detail mesh).

**For Bannon:** these are the template for Bannon's backstage brawl areas.
**For Western Heart:** arena-traversal reference — fighting across connected
spaces, not just the ring.

## Weapons & objects

61 weapons + 61 objects. Cross-reference with `bg/placard/` (51) for full
arena dressing inventory. Weapon meshes are the reference set for Bannon's
weapon system and AshLane/UR-style brawler weapon pickups.

## Extraction status

- [x] File listing mapped (373 files)
- [ ] `.pac` package format decode (A0–A4, C0, audi.pac)
- [ ] Arena `.ymg` geometry extraction (same YOBJ format as wrestlers — blocked on skinning decode)
- [ ] Texture conversion (TPL → PNG via `teardown/wmxix/decode_tpl.py`)
- [ ] Backstage area count + names (N_M → location names needs in-game or string-table lookup)

## Related

- Wrestler models: `WRESTLER-IDENTITY-MAP.md`
- YOBJ format: `YOBJ-SKINNING-NOTES.md` (assembly blocked — see RE worker)
- Arena universe map: `teardown/wmxix/ARENA-UNIVERSE-MAP.md`
