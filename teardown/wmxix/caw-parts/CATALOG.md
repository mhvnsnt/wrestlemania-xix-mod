# CAW edit_data catalog

**2690 files, 54.3 MB total** (streamed from ISO, 2026-10-13)

## By extension

| ext | count |
|---|---|
| .tex | 1470 |
| .ymg | 1200 |
| .ycg | 8 |
| .ymm | 3 |
| .tga | 2 |
| .psd | 2 |
| .tpl | 2 |
| .tm2 | 1 |
| .tpg | 1 |
| .txt | 1 |

## By content signature (first bytes)

| type | count |
|---|---|
| RAW (02000000) | 781 |
| YOBJ v00030001 | 754 |
| RAW (01000000) | 259 |
| DUMY placeholder | 202 |
| YOBJ v00040001 | 175 |
| RAW (04000000) | 105 |
| RAW (0e000000) | 92 |
| RAW (07000000) | 67 |
| RAW (06000000) | 50 |
| YOBJ v00040002 | 32 |
| YOBJ v00040003 | 31 |
| RAW (0a000000) | 26 |
| RAW (08000000) | 26 |
| RAW (03000000) | 20 |
| RAW (05000000) | 13 |
| RAW (26000000) | 12 |
| RAW (10000000) | 9 |
| YOBJ v00030002 | 3 |
| YOBJ v00000000 | 3 |
| RAW (09000000) | 3 |
| RAW (0c000000) | 3 |
| RAW (0000002a) | 2 |
| RAW (00000004) | 2 |
| RAW (00000006) | 2 |
| RAW (00000005) | 2 |
| YOBJ v00040004 | 2 |
| TGA image | 2 |
| PSD photoshop | 2 |
| TPL texture | 2 |
| RAW (0b000000) | 2 |
| YOBJ v00030000 | 1 |
| TM2 (PS2 TIM2) | 1 |
| RAW (00000002) | 1 |
| TXT-ish | 1 |
| RAW (0d000000) | 1 |
| RAW (1a000000) | 1 |

## By top-level dir

| dir | count |
|---|---|
| Man/ | 670 |
| Woman/ | 543 |
| Face/ | 351 |
| Upper_Body/ | 218 |
| Face_op/ | 208 |
| Gears/ | 149 |
| Lower_Body/ | 142 |
| Shoes/ | 84 |
| Hair/ | 70 |
| Wrist/ | 60 |
| Gloves/ | 50 |
| common/ | 50 |
| 64gara/ | 41 |
| Knee/ | 24 |
| Elbow/ | 22 |
| 000_0.ycg/ | 1 |
| 000_1.ycg/ | 1 |
| 000_2.ycg/ | 1 |
| 000_3.ycg/ | 1 |
| 001_0.ycg/ | 1 |
| 001_1.ycg/ | 1 |
| 001_2.ycg/ | 1 |
| 001_3.ycg/ | 1 |

## Notable finds

- `MODEL/Woman/Face/tq0_417/` contains the ARTIST WORKING FILES: .tga source art, .tm2 (PS2 TIM2), 2 .psd (Japanese filenames), .tpg, and `tq0_417_TPL/` with 2 .tpl + `script.txt` revealing the build path `D:\MAX_Wwfgc2\edit\woman1\edit_face_woman\mouth\tex\`
- `.tpl` files carry the standard GameCube TPL magic `0020AF30`
- 3 `.ymm` files (Yukes material?) under `MODEL/Woman/Hair/`
- `COL/` 8 `.ycg`: 2x 2,356 B skeleton-size + 6 small palette/override files

Full per-file listing: `files.tsv`
