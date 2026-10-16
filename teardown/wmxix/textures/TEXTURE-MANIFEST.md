# WMXIX Texture Manifest

**Generated:** 2026-10-16 (lane worker (c) TEXTURE DECODE — "WMXIX 100% Retail")
**Coverage:** 1,167 PNGs decoded from GameCube TPL textures — **0 corrupt, 0 unreadable** (every PNG opened and pixel-loaded with PIL).

## 1. Inventory — per directory

All PNGs are in `teardown/wmxix/textures/<dir>/`, decoded by `teardown/wmxix/decode_tpl.py`
(TPL → PNG, all formats: I4/I8/IA4/IA8/RGB565/RGB5A3/RGBA8/C4/C8/C14X2/CMPR).
Extractor: `teardown/wmxix/extract_arena_textures.py` (streams from ISO, no intermediates).
Source `.tex` names and entry counts are in `TEX-MANIFEST.txt` (this file duplicates them for convenience).

| Dir | PNGs | Total size | Size range (px) | Most common size | Source `.tex` (ISO path) |
|-----|------|-----------|-----------------|------------------|--------------------------|
| 00 | 75 | 963 KB | 16×8 – 256×256 | 32×32 (×12) | bg/00.tex (665,920 B, 77 entries) |
| 02 | 54 | 759 KB | 16×16 – 256×512 | 256×256 (×7) | bg/02.tex (687,264 B, 56 entries) |
| 0_0 | 63 | 1036 KB | 16×16 – 256×256 | 32×32 (×14) | bg/bs/0_0.tex (529,952 B, 63 entries) |
| 0_1 | 66 | 925 KB | 16×16 – 256×256 | 32×32 (×13) | bg/bs/0_1.tex (390,336 B, 67 entries) |
| 0_2 | 73 | 1122 KB | 16×16 – 512×256 | 32×32 (×14) | bg/bs/0_2.tex (613,600 B, 73 entries) |
| 0_3 | 69 | 1107 KB | 16×16 – 512×512 | 32×32 (×15) | bg/bs/0_3.tex (683,520 B, 69 entries) |
| 1_0 | 63 | 1653 KB | 8×32 – 512×512 | 64×64 (×14) | bg/bs/1_0.tex (810,176 B, 63 entries) |
| 1_1 | 76 | 1382 KB | 8×8 – 512×512 | 64×64 (×17) | bg/bs/1_1.tex (663,264 B, 76 entries) |
| 1_2 | 76 | 1382 KB | 8×8 – 512×512 | 64×64 (×17) | bg/bs/1_2.tex (663,264 B, 76 entries) |
| 1_3 | 76 | 1382 KB | 8×8 – 512×512 | 64×64 (×17) | bg/bs/1_3.tex (663,264 B, 76 entries) |
| 1_4 | 76 | 1382 KB | 8×8 – 512×512 | 64×64 (×17) | bg/bs/1_4.tex (663,264 B, 76 entries) |
| 2_0 | 109 | 624 KB | 8×8 – 256×256 | 64×64 (×33) | bg/bs/2_0.tex (523,840 B, 109 entries) |
| 2_1 | 110 | 629 KB | 8×8 – 256×256 | 64×64 (×34) | bg/bs/2_1.tex (525,984 B, 110 entries) |
| 2_2 | 98 | 724 KB | 8×8 – 512×512 | 64×64 (×31) | bg/bs/2_2.tex (689,952 B, 98 entries) |
| 5_0 | 2 | 14 KB | 64×64 – 512×256 | — | bg/bs/5_0.tex (69,856 B, 2 entries) |
| 5_1 | 8 | 492 KB | 128×128 – 256×512 | 128×512 (×2) | bg/bs/5_1.tex (213,792 B, 8 entries) |
| f01 | 4 | 105 KB | 32×32 – 256×256 | — | bg/f01.tex (52,128 B, 4 entries) |
| kaijo_x8 | 55 | 1071 KB | 8×8 – 512×512 | 128×128 (×11) | bg/kaijo_x8.tex (698,432 B, 55 entries) |
| ring | 14 | 430 KB | 32×32 – 512×512 | 32×32 (×4) | bg/ring.tex (282,976 B, 14 entries) |

**Total: 1,167 PNGs / ~17.6 MB. Every file readable, none corrupt.**

Notes:
- 00 = primary weekly show arena (RAW), 02 = PPV / WrestleMania XIX main arena,
  `0_x/1_x/2_x` = backstage corridor/room sets, `ring` = ring + apron props.
- Eye-verified earlier: `ring/ar_a3.png` is the WWF.com ring-apron banner.
- `01` has no `.tex` companion on disc (shares the 00/02 texture set or is untextured);
  same for `*_ad2` LOD variants (share base-arena textures) and the small untextured
  pieces (`add_x8, eff_x8, gt_x8, scr_x8, scr_wm, post, c_mat, mat, dummy_x8`).

## 2. Texture → model mapping

Texture directories are named after the arena `.tex` they were decoded from, which
matches the arena `.ymg` mesh of the same basename. Mapping:

| Model mesh (teardown/wmxix/arenas/) | Texture dir | Testbed file |
|------------------------------------|-------------|--------------|
| bg/00.ymg | textures/00/ | — |
| bg/02.ymg | textures/02/ | testbed/arena_02.obj |
| bg/bs/0_0.ymg … bg/bs/5_1.ymg | textures/0_0/ … textures/5_1/ | — |
| bg/f01.ymg | textures/f01/ | — |
| bg/kaijo_x8.ymg | textures/kaijo_x8/ | — |
| bg/ring.ymg (ring props shared by all arenas) | textures/ring/ | — |

Caveat: the current testbed OBJs (`arena_02.obj`) are vertex point clouds with **no
UV coordinates yet** — texture assignment to geometry is pending the UV-mapping
lane. The manifest records the source-of-truth pairing so it plugs in when UVs land.

Notable textures in `02/` (WrestleMania XIX main arena, 54 PNGs):
`rope.png`, `kage.png` (crowd), `l_phon.png`, `add.png`, `ss01–ss38` (screens/signage),
`st_au_01–st_au_06` (large audience/Titantron screens, up to 256×512),
`ar_00, ar_04–ar_09, ar_a3`, `kan01/04/05` (kanji signage).

## 3. Wrestler textures — STATUS: NONE LOCAL

**No decoded wrestler PNGs exist anywhere in this repo or workspace** (checked
`teardown/wmxix/`, `teardown/wwe-wrestlemania-xix/`, `~/workspace/wwe-wrestler-models/`).
The wrestler texture containers (`model/wrestler/*.tex`) are **not on local disk**
and there is no ISO locally — decoding more is impossible in this lane.

How slot identity was confirmed (without textures): the 000 model file's embedded
texture-name table (`@0x10574` in the YOBJ, see
`teardown/wwe-wrestlemania-xix/docs/YOBJ-SKINNING-DECODER-REPORT.md`) lists
`hhh_body, hhh_arm, hhh_hand, hhh_waists, hhh_l_leg, hhh_knee, hhh_foot,
face, head_back, eye, head_top, mouth, tooth` (+ `m_`/`pm_` variants) → slot 000
is **Triple H** (confirmed 2026-10-15, recorded in WRESTLER-IDENTITY-MAP.md).

## 4. Missing-textures list for the ISO pull (TeraBox lane)

Pull these from the ISO, then decode each with `teardown/wmxix/decode_tpl.py`
(same `.tex` container + TPL format as arena textures — no new tooling needed).

### P0 — Triple H (slot 000), needed for the testbed now
- `//model/wrestler/000_0.tex` (301,760 B) — base attire
- `//model/wrestler/000_1.tex` (301,760 B) — alt attire

Expected decoded names (from the model's texture-name table): `hhh_body, hhh_arm,
hhh_hand, hhh_waists, hhh_l_leg, hhh_knee, hhh_foot, face, head_back, eye, head_top,
mouth, tooth` plus `m_`/`pm_` variants. **The `face` texture is the visual-ID key**
for future slots — decode it first per slot.

### P1 — roster slots with alt attire (67 slots)
The identity-map heuristic (unverified): slots with `_0` + `_1` ≈ playable roster.
All `//model/wrestler/NNN_0.tex` + `//model/wrestler/NNN_1.tex` for those 67 slots.
Full list in `docs/WMXIX-FILE-LISTING.txt` (`grep '//model/wrestler' … .tex`).

### P2 — everything else (completeness)
Remaining `//model/wrestler/NNN_2.tex`, `NNN_3.tex`, `NNN_4.tex` (13 + 5 + 1 = 19 files)
for CAW parts / NPCs / multi-attire slots. Per identity map: 162 wrestler `.tex`
files total (77 `_0`, 67 `_1`, 13 `_2`, 5 `_3`).

### Also still on disc (not yet pulled) — arena side
- `//bg/01.tex` does not exist; no action. `01_ent.tex` + `01_light` variants exist
  for arena 01 (SmackDown) — pull if SmackDown arena is in scope.
- Revenge Mode `.pac` environment sets (A0–A4, C0–C2, F1–F6, H3–H9, P0–P3, S0–S5,
  T0–T3 — 35 packages) contain their own textures; pull list comes from the arena lane.

## 5. Testbed copies

`testbed/textures/` contains **copies** (source of truth stays here):
- `02/` — all 54 WrestleMania XIX main-arena PNGs (759 KB) — matches `testbed/arena_02.obj`
- `ring/` — all 14 ring PNGs (430 KB) — shared ring props (apron/banner)
- No wrestler textures copied — none exist locally. Triple H textures go here as
  `testbed/textures/000_*/` the moment the ISO pull lands.
