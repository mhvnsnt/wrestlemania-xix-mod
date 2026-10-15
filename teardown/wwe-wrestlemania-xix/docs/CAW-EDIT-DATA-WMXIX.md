# WMXIX CAW edit_data layout (MEASURED 2026-10-13)

The CAW part library lives in the ISO at `edit_data/`. The created-wrestler
SAVE itself lives on the GameCube memory card (not in the ISO) — its byte
layout is **blocked** pending a real `.gci` dump (see "What's needed").

## edit_data structure (measured from ISO FST)

| dir | files | content |
|---|---|---|
| `edit_data/MODEL` | 1,213 | part meshes (YOBJ) |
| `edit_data/TEX` | 1,469 | part textures (`.tex`) |
| `edit_data/COL` | 8 | `.ycg` files (2×2356 B + 6 small) |

### MODEL: part naming scheme

`edit_data/MODEL/{Man,Woman}/{Category}/{style}_{variant}/{l0,r0}.ymg`

- Gender: `Man`, `Woman`.
- Categories (10): `Elbow`, `Face`, `Gears`, `Gloves`, `Hair`, `Knee`,
  `Lower_Body`, `Shoes`, `Upper_Body`, `Wrist`.
- Style ids: `m{C}0_{NNN}` where C = category letter
  (e=Elbow, f=Face, z=Gears, g=Gloves, k=Hair, n=Knee, c=Lower_Body,
  s=Shoes, p=Upper_Body, r=Wrist).
- Style counts (Man): Elbow 5, Face 77, Gears 140, Gloves 12, Hair 76,
  Knee 6, Lower_Body 25, Shoes 22, Upper_Body 62, Wrist 4.
  (Woman similar; Face 76, Lower_Body 23, Shoes 28, Hair 77.)
- Each style: `l0.ymg` + `r0.ymg` (left/right). Parts are YOBJ
  (same magic/version `0x00030001` as wrestler models).

### TEX

`edit_data/TEX/64gara/{t…}_{NNN}.tex` — 1,469 textures for parts.
(`64gara` = pattern/design group.)

### COL

8 `.ycg` files: `000_0.ycg` (2356 B) + `000_1..3.ycg` (228/340/284 B),
same for `001_`. The 2356 B files match wrestler `.ycg` size (skeleton);
the small ones are palettes/overrides (content not yet decoded).

## What the save references (inferred, not measured)

A created wrestler = per-category style+variant ids (10 categories ×
gender) + texture ids + color ids + name/stats. The part-id → file mapping
above is the complete dictionary the save's ids index into.

## What's needed (to unblock the save-record layout)

1. Dolphin emulator + WMXIX ISO.
2. Create a CAW with KNOWN values (e.g. all parts = first style,
   name = "TEST").
3. Export the memory-card `.gci` (or raw card image).
4. Diff the save against the part-id tables above to fix byte offsets.

Without a real save, the record's field order, string encoding, and stats
layout cannot be determined from the ISO alone. **Blocked.**
