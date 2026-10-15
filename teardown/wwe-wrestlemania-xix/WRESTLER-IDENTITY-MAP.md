# Wrestler Identity Map — WWE WrestleMania XIX (GameCube)

**Measured from:** `model/wrestler/` FST listing (484 files), `docs/WMXIX-FILE-LISTING.txt`
**Status:** STRUCTURE MAPPED. Individual slot→wrestler identity needs owner
visual ID (he knows the roster by sight). Do NOT invent identities.

## Slot structure (measured)

| Fact | Value |
|---|---|
| Total model slots | **108** (numbered 000–110, some numbers unused) |
| Files per slot | `_0` = base (.tex + .ymg + .ycg); `_1` = alt attire on 67 slots; `_2` on 22 slots; `_3` on 5 slots |
| Total files | 484 (265 `_0`, 169 `_1`, 38 `_2`, 11 `_3`, 1 `_4`) |
| Geometry | `_0.ymg` == `_1.ymg` byte-identical on tested slots — alt attires are **texture-only** |
| Skeleton | 70-bone table in every `.ymg` (see WRESTLER-SKELETON.md) — universal across slots |

## Slot → roster reasoning

The game shipped with ~45 playable wrestlers + 20 Revenge Mode bosses + 4 NPCs
= ~69 named characters (see `~/workspace/agent-ops/MAT-LEGENDS-RENAME-WORKSHEET.md`).

108 slots > 69 named characters. The extras are:
- **CAW parts** (create-a-wrestler body part library)
- **Managers / referees / divas** (non-wrestler NPCs)
- **Duplicate slots** for different attires beyond `_1`

**Heuristic (unverified):** slots WITH `_1` alt attire (67) ≈ the playable roster +
major bosses. Slots with only `_0` (41) ≈ CAW parts / NPCs / minor characters.
This is a hypothesis — verify by visual ID.

## Identity assignment table

Owner assigns. Fill the WH Name column from the mat-legends worksheet.

| Slot | Has alt | Likely role | WWE Identity | WH Name |
|---|---|---|---|---|
| 000 | _0,_1 | roster | **Triple H** (confirmed 2026-10-15: hhh_ textures) | PENDING |
| 001 | _0,_1 | roster? | PENDING | PENDING |
| ... | ... | ... | ... | ... |

(Full 108-row table to be filled during owner visual-ID session.
Render each slot's `_0.tex` face texture for the ID session.)

## How to identify a slot

1. Extract `NNN_0.tex` → convert TPL → PNG (see `teardown/wmxix/decode_tpl.py`)
2. The face/head texture is the fastest visual ID
3. Cross-check attire colors against known WMXIX roster attires
4. CAW part slots have generic/unbranded textures

## Related

- Bone/skeleton: `WRESTLER-SKELETON.md`, `wrestler-skeleton-000.json`
- CAW parts: `edit_data/` (2,690 files) — see `CAW-EDIT-DATA-WMXIX.md`
- Rename worksheet: `~/workspace/agent-ops/MAT-LEGENDS-RENAME-WORKSHEET.md`
- **RULE:** mat-legends physical rename deferred until owner assigns all names.
  Never invent WH names.
