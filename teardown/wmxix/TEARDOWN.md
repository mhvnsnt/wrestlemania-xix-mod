# WWE WRESTLEMANIA XIX — Teardown for Western Heart

**Role in Chimera Build:** Wrestling Mode — modes, arena traversal, Revenge Mode structure.
**Developer:** THQ (Yukes engine — different philosophy from No Mercy's AKI engine)
**Platform:** Nintendo GameCube (Game ID `GW9E78`)
**Roster:** ~40 WWE wrestlers. **Revenge Mode:** mission-based objectives in settings beyond the ring.
**Create-a-Wrestler / Shopzone:** upgrade economy (attire, weapons, moves, ability points) informs the chimera customization meta-progression.
**Last updated:** 2026-10-13 (full asset extraction: 111 wrestler slots, 170 YANM clips, CAW catalog, arena textures)

**Directory layout (this teardown has two homes):**
- `teardown/wmxix/` — **arena/stage integration lane**: `ARENA-UNIVERSE-MAP.md` (every arena → Western Heart stage), `arenas/` (40 decoded OBJ point clouds + `ARENA-FORMAT.md` + extraction tools), `wrestlers/` (126 wrestler OBJs, all slots 000–110), `animations/` (170 decoded YANM clips), `caw-parts/` (2,690-file CAW catalog), `textures/` (1,167 arena PNGs), this doc.
- `teardown/wwe-wrestlemania-xix/` — **format research lane**: `docs/` (measured format specs), `tools/` (26 decoder/analysis tools), `objs/` (eye-verified strip OBJs), `YANM-FORMAT.md`, `YOBJ-SKINNING-NOTES.md`, `WRESTLER-SKELETON.md`.
- Research log: `docs/WMXIX-TEARDOWN.md` (running notes). Full file listing: `docs/WMXIX-FILE-LISTING.txt`.

---

## 1. ISO — Downloaded + Verified (2026-10-12)

- `WWE Wrestlemania XIX (USA).iso` — 1,459,978,240 bytes, MD5 `c13c47a5ed24a675545c99a15e44529d` (matches source listing)
- Disc header: name `WRESTLEMANIA XIX`, Game ID `GW9E78`, magic `C2339F3D`
- Source: CDRomance (via browser task, no signup/payment). Mirrors: gamulator.com, Coolrom, freeroms
- Local working copy: `~/workspace/game-reverse-engineering/wwe-wrestlemania-xix/` (ISO + tools + docs; mirrored best-of into this repo per TEARDOWN-TO-REPO LAW)

## 2. File Structure — Mapped (2026-10-12)

Streaming FST parse via `tools/gcn_fst.py` (pure-stdlib GCN disc FST reader; no full extraction — streams from ISO byte ranges, disk-safe):
- **5,016 FST entries, 4,222 files, ~1.41GB** (scrubbed ISO 1.46GB on disk)
- FST offset/size at disc header `0x424`/`0x428` (`0x362F00`/`0x1A8A3`) — NOT the usual `0x420`; `gcn_fst.py` handles this

| Dir | Files | Content |
|---|---|---|
| `model/wrestler/` | 484 | Per-slot model groups `NNN_M`, slots 000–110 (111 slots — more than the ~40-man roster; extras likely CAW parts, managers, refs, divas). `_0` = `.tex` + `.ymg` + `.ycg`; `_1` second variant (alt attire) on 66 slots; `_2`/`_3` on a handful |
| `ringmotion/` | 340 | Move animation **pairs**: `.yag` (YANM skeletal anim, median 38.6 KB) + `.atr` (`DATA` metadata, median 388 B — 16-byte records describing its `.yag` companion). Letter groups a=68, b=46, c=208, d=12 — likely move categories (attack/grapple/strike/special). Includes `cnv.bat` (build-time converter left on disc) |
| `motion/*.mpc` | — | Shared move packages (`common`, `move`, `win`, `nyujo_ch` entrance) |
| `edit_data/` | 2,690 | CAW creation suite: `MODEL/` 1,213 part meshes (YOBJ), `TEX/` 1,469 part textures, `COL/` 8 `.ycg` (skeleton-size 2,356 B + small palette/override files) |
| `bg/` | 373 | Arena sets: per-arena `.ymg`/`.ycg`/`.tex` + `.pac` arena packages, `weapon/` 61 (hardcore weapons), `object/` 61 (Revenge Mode props), `placard/` 51 (crowd signs/banners) — Revenge Mode out-of-ring environments live here |
| `Entrance/` | — | Create-an-Entrance data (`CamData.dat`, `EffData.dat`, `entpac.mpq`) |
| `viewer/`, `2d/`, `thp/`, `tutorial/`, `paint_tool/` | — | Dev viewer assets, UI, videos, CAW paint-tool UI |

## 3. Wrestler Skeleton — Decoded (2026-10-12/13)

**70 bones**, measured from `model/wrestler/000_0.ymg` (64-byte slots at file `0xF3BC`): parent (0-based, −1 = root), local translation (f32 ×3), local euler XYZ (f32 ×3, rad), bone length.
- Full measured table + JSON: `../wwe-wrestlemania-xix/WRESTLER-SKELETON.md`, `../wwe-wrestlemania-xix/docs/wrestler-skeleton-000.json`
- Structure: Bip → Pelvis → Spine → Spine1 → Neck → Head (+ face bones: lips, teeth, eyes, brows); R/L clavicle → upper arm → forearm → hand (+ 5 × 3-segment fingers); R/L thigh → calf → foot → toe. Bip root at y = −102.695 (Yukes authoring convention: local y+ = R for clavicles and thighs)
- **`.ycg` joint groups** (the animation rig): 42 records = 8 singles + 5 L/R pairs + 8 3-chains; every record is a **1-DOF hinge**. Hinge axis uniform per group — local X (13 groups: limbs/torso/pelvis), local Z (6: head/neck + accessory chains), local Y (2) — FK-confirmed. 3-chain groups: ch1→rec1 (hip/shoulder), ch2→rec2 (knee/elbow), **rec3 = −(rec1+rec2)** (measured ≤0.03° end-effector stability — holds foot/hand world orientation)

## 4. YOBJ Mesh Format — Two Variants Cracked

### 4a. Arena variant — POSITIONS CRACKED ✅ (2026-10-13, PR #20)

- Version `0x00030013`. **f32 (float32) vertex triplets, big-endian** — NOT quantized like wrestler models
- **43 arena files extracted → OBJ point clouds, 324,425 vertices total** (`arenas/`: `00.obj`–`02.obj` main arenas, `0_0.obj`–`2_2.obj` bs/ sub-arenas, `ring.obj` = wrestling ring 809 verts, `kaijo_x8.obj` 14,170 verts, `*_ad2.obj` detail/LOD variants, entrance/ground/lighting/screen pieces)
- Point-cloud renders verified with own eyes: bg/00 = full arena bowl, ring.ymg = ring with posts/ropes, kaijo_x8 = arena structure
- File structure (bg/00.ymg, 304,480 B): object/bone names (`kaijo_rw`) @0x46BB4, material table (25 × 20-byte records) @0x47404, texture name table (`rw19.bmp`…) @0x470B4, mesh metadata @0x0830
- Material records: `[u32 color1][u32 color2][u32 color3][u32 0][u16 0x0004][u16 idx_offset]` — index offsets are ABSOLUTE file offsets pointing to ~52-byte u16 chunks
- **Face indices: OPEN** — the u16 chunks at material index offsets are mixed data (interleaved attributes or different stride), not clean triangle indices. Next: parse mesh descriptors at 0x0830+ to link vertex arrays to index arrays, or Blender Poisson reconstruction on the point clouds
- Tools: `arenas/extract_all_arenas.py` (all 43), `arenas/yobj_arena_extract.py` (single). Format doc: `arenas/ARENA-FORMAT.md`

### 4b. Wrestler variant — POSITIONS + CONNECTIVITY CRACKED ✅ (2026-10-13, PR #24)

- Version `0x00040001`. **s16x3 vertices, dequantized /64** — different from the arena variant's f32
- **Connectivity = implicit triangle strips, NO index buffers** (`../wwe-wrestlemania-xix/tools/yobj_strips.py`): vertex runs are strip-ordered (ladder/zigzag); split at jump boundaries (threshold max(400, 4× median step)); single near-origin separator verts between strips. The "dense u16 runs" in file gaps are NOT index buffers (coordinate-scale values + zero runs; no valid index buffer referencing the vertex list exists anywhere in the file)
- Eye-verified: `model/wrestler/000_0.ymg` → 13 skin batches (8-byte records @0x7CA0, 606 s16x3 verts) → 58 strips → **383 tris**; elbow CAW part (148 verts) → **113 tris**; OBJs at `../wwe-wrestlemania-xix/objs/`
- **Batch descriptor table**: 58 × 16-byte records at header `[0x5C]` (0x5AE0) — payload offset (base file 0x80), material/part id (b8, range 3–70), unit count (4-byte units). Fully measured in `../wwe-wrestlemania-xix/docs/YOBJ-BATCH-SEMANTICS.md` (group-header pattern: records 1–7 counts sum to record 0's count; `marker_hi = b8−1`; payload is (u16, 0) pairs whose exact semantics are OPEN)
- **Skinning — per-batch bone bind REJECTED** (`../wwe-wrestlemania-xix/YOBJ-SKINNING-NOTES.md`): hierarchical/inverse-bind/translation-only/local-matrix transforms all scattered; 6 axis permutations all scattered. The elbow (rigid CAW part) renders coherent, so s16/64 is valid — wrestler batches need per-VERTEX weights from an unlocated table, or positions are delta-encoded. OPEN
- Note: `000_0.ymg` == `000_1.ymg` byte-identical (69,176 B) — the `_1` alt attire is texture-only

**Full roster extraction (2026-10-13):** all 111 slots `model/wrestler/000–110` processed
(`wrestlers/`, `EXTRACTION-MANIFEST.txt`; tool: `extract_wrestlers.py`):
- **126 OBJs, 62,034 verts, 44,233 tris** across 78 slots
- Batch-table locator: longest run (≥3) of 8-byte records `[bone][count][00][count][u16 0][u16 off-rel-0x80]` at 8-alignment, with the **byte1==byte3 (count duplicated) discriminator** — kills all false-positive runs, preserves every validated table 10/10
- 9 `_2` variants are **DUMY placeholders** (no mesh); 34 slots (021, 060–080, 086–089, 098, 103–109) have **no .ymg at all** (tex+ycg only)
- 6 files are YOBJ sub-variants (v1: 110_0, v2: 100_0/101_0/102_0, named-bone v4: 096_0/097_0) with a different batch layout — extracted via **smooth-pool scan fallback** (`*_pools.obj`, heuristic, batch boundaries unknown)
- Byte-identical variants deduped per slot (e.g. 000_1 == 000_0)

## 5. YANM Animation Format — Decoded (2026-10-13, PR #26)

Measured against 170 `ringmotion/*.yag` files; streaming from ISO. Full spec: `../wwe-wrestlemania-xix/YANM-FORMAT.md`. All fields big-endian.

**Header (56 bytes):** `YANM` magic; u32 payload size (file size − 56); `0x011F0000`; `0x08`; `0xCD89A39E`; `0x0010B4F0` @0x30 (constant, semantics open); **f32 seconds-per-tick** @0x3C (e.g. 0.0279688; clip seconds = tick_total × this; 0.0 in some files — not always valid); f32 ×3 anim params @0x40–0x48 (root-motion/blend candidates)

**Track directory — 29 × 32-byte records @0x50–0x3F0:** joint hash (matches `.ycg` group hash for 21/29 tracks), A-stream offset (0 = single track), B/key-stream offset, f32 ×3 (nonzero ⟺ dual track), w24 (nonzero ⟺ dual), key count / packed (ca,cb). All-zero terminator @0x3F0. Track hash sets DIFFER per clip.

**Key formats:**
- **Single track — 5-byte keys** `(s16 ch1, u8 dt, s16 ch2)`: dt is the middle byte and is a DELTA (0–255). Channel = **32767·sin(hinge angle)** → angle = asin(s16/32767); saturates ±90° (proven by circularity + small-angle smoothness tests)
- **Dual track — A: 4-byte keys** `(s16 value, u8 flags, u8 dt)`, **B: 5-byte keys**: A = bilateral COMMON-MODE hinge angle (asin encoding), B = per-side trims; `rec_i(t) = A(t) + B_i(t)` on the group's hinge axis; r²(A~B) ≈ 0.00–0.05 (independent component). Duals exist ONLY for symmetric-motion 2-record groups
- 21 tracks ↔ 21 `.ycg` joint-groups 1:1 (hash match); 8 track hashes appear in NO wrestler `.ycg` (0/154 files — identity open: 2nd performer / camera / prop / referee candidates)
- Per-track durations vary up to 2× within a clip (large-dt hold-key authoring variance); retarget handling: hold-last + clip

**Mapping evidence:** `docs/yanm-track-joint-map.json` (29-track table × 3 clips), `docs/yanm-task2-finish.json` (dual-A semantics, chain assignment, hinge axes), `docs/yanm-rec3-rule.json` (rec3 = −(rec1+rec2) proof), `docs/ycg-group-mapping.json`. Probe tools: `yanm_census.py`, `yanm_track_probe.py`, `yanm_keyseg.py`, `yanm_semantics.py`, `yanm_unitfit.py`, `yanm_gait.py`, `yanm_hashscan.py`.

**Full clip decode (2026-10-13):** all **170 `ringmotion/*.yag` → `animations/*.json`**
(tool: `extract_yanm.py`). Each JSON: header (payload size, sec_per_tick, params),
29 tracks (hash → anatomy via `ycg-group-mapping.json`, single/dual, key counts,
tick totals, est. seconds), and every key decoded — single keys as
`[dt, ch1_s16, ch2_s16, asin_deg1, asin_deg2]`, dual-A as `[dt, flags, value_s16, value_deg]`
(A-stream 8-byte head stored raw hex), dual-B same as single. Leg-group tracks
(BD5B2A59/BD5B5259) also carry the half-angle series (`2·unwrap(atan2(c2,c1))`).
`.atr` companions included as raw 16-byte records. 169/170 decode clean;
`c138_0a.yag` is a **72-byte stub** (wrong magic words, no track directory).

### 5b. Detail tracks — fingers / thumbs / toes / ECD / 0C5BF279 — Resolved (2026-10-13)

The 8 track hashes absent from every `.ycg` are **per-move hand/foot detail POSES**
(w28 key count = 1 = static, except when animating). Full analysis:
`../wwe-wrestlemania-xix/YANM-ITEM5-CYCLE.md`.

- **Fingers** `A4955E6E`/`BA955E6E` (L/R pair, XOR `0x1E000000`): one hand each;
  ch1 = proximal-curl, ch2 = distal-curl (independent — decoupled clips
  `c100_0a` ch1-only 58°, `c007_0a`/`c124_0a` ch2-only −72°). `c000_0a` shows
  asymmetric grapple roles: one hand grip→releases while the other holds.
  Anatomical L/R provisional (needs visual verification).
- **Thumbs** `579B89D0`/`579B8E50` (L/R pair, XOR `0x780`) — STRONG: default
  (0°, 80°) = rest abduction; grapple poses (80°, 0°) = wrapped into grip,
  (0°, 0°) = flat. Side-paired with finger tracks by 170-clip contingency
  (same-side: thumb never leaves default unless its finger track animates,
  0/149 and 0/154; cross-side: no association).
- **Toes** `007FD58C`/`1E7FD58C` (L/R pair, XOR `0x1E000000`): static per clip,
  30 distinct poses — posed per move, never keyframed.
- **0C5BF279** = per-wrestler detail track (degenerate dual, static): embedded
  once per wrestler `.ymg` in a binary table (`000_0 @0x10d4c`, `002_0 @0x1302c`)
  + 9 identical param words; `001_0` carries `40911198` in the analogous slot
  (unused in ringmotion clips). Likely wrestler-specific attire/hair/accessory.
- **ECD28978** = 8th detail track, identity OPEN: 82 discrete static poses
  (0/80°-grid pose selector), independent of all core tracks (max |r| = 0.27).
  Candidates: facial-expression selector, second-performer detail, prop.
- **Hash construction**: `track_id = joint_base_id XOR side_code` — side codes
  `0x0F`, `0xF0`, `0x780`, `0x7800`, `0x1E000000`, `0xA0`, `0xA00` per joint
  type. Base IDs are ASSIGNED, not string-hashed (`00008102…0000D502` are
  literal small IDs; 26-function + linear root batteries = 0 hits). Related
  joints share base-ID deltas (`60F8^6198 = 0x1600102`).

### 5c. Item-6 cycle — ECD probes, base-ID generation fn, anatomical L/R (2026-10-13)

Full analysis: `./YANM-ITEM6-CYCLE.md`. Measured over the full 215-clip
universe (ringmotion 170 + viewer/motion 37 + viewer 3 + 2d 4 + bg/bs 1).

- **ECD28978 — per-move-variant 2-channel static pose selector, identity
  still OPEN**: present in 208/215 clips, 0/208 animated within a clip;
  87 distinct poses at 1° rounding; both channels share one value
  vocabulary (top: 79.9°, 75.7°, 3.6°); fully independent of body /
  fingers / thumbs / 0C5BF279 (all |r| ≤ 0.13). Variant-specific:
  `c200_0a` (63.0,24.5) vs `c200_1a` (0.9,1.1) vs `c200_2a` (1.8,0.2) —
  poses go to rest across variants, NOT mirror-flipped (mirror-selector
  rejected 3/3). Second-performer hypothesis weakened: the one clip with
  all 7 slot-entity tracks (`a033_0a`) has NO ECD. 9×9-grid, thumb-related,
  and 0C5B-related hypotheses rejected with counts. Leading hypothesis:
  face-bone driver (20 face bones in ymg; fits static-per-move + ±80°
  extremes + variant-specificity) — needs mesh/FK or visual to confirm.
- **Base-ID generation fn — narrowed, still OPEN**: 472-hash universe →
  24 side pairs → 445 base IDs = 28 entities + 417 joint/system tracks.
  Entities = `(slot<<8)|0x02`, 25 slots (0–255; all 7 ringmotion slots
  co-occur in the single `a033_0a` setup clip). Rejected with numbers:
  fixed-key XOR (best 7/417), nibble-permutation (25/417, all small IDs),
  verbatim ID table in model files (hits = ycg records' own hash slots),
  DDF67B-run relation (min popcount 9), index-hash battery 0–4999 (1 hit
  on a small family ID). Real structure: non-joint systems use
  `(family<<16)|member` (`4AAF`×9, `F7AB`×5, `5D9B`×7, `579B`×5,
  `010000`×7…); joint base IDs are tool-assigned opaque. Correction:
  `613B7507 ^ 637B7003` = **0x02400504** (was miswritten 0x02400544).
- **Anatomical L/R — bridge unachievable headless**: side-bit→ycg-y is
  solid (`0x04000000` SET ↔ y<0, 6/6; ycg records mirror-symmetric);
  ymg anatomical solid (R=+y, L=−y from thigh ±10.40); but ycg↔ymg frame
  correspondence fails — no euler order aligns (R bones never at y>0),
  nearest-neighbor 15 agree / 7 disagree / 20 abstain (ycg 42-joint rig is
  a different scale/proportion rig; bind pose is mirror-symmetric = zero
  intrinsic L/R info). Provisional mapping stays LOW confidence; for
  retargeting, map side-bits consistently — result is correct up to a
  global mirror. Resolving the final bit needs YOBJ mesh assembly or
  visual reference.

## 6. Arenas — Decoded + Mapped to Western Heart

- **40 arena OBJ point clouds decoded** (see §4a; `arenas/`). The 43-file filter matches 43 `.ymg` files, but `c_mat.ymg`, `dummy_x8.ymg`, `mat.ymg` contain **zero vertices** (material/dummy files) — 40/43 is complete.
- **Arena textures decoded (2026-10-13):** `.tex` container format cracked — `[u32 LE count][u32 0x10000][u32 0][u32 0x10]` + count × `[16B name]["tpl\0"][u32 LE size][u32 LE offset][u32 0]`; each entry is a standard GameCube **TPL** (magic `0x0020AF30`), decoded with new `decode_tpl.py` (I4/I8/IA4/IA8/RGB565/RGB5A3/RGBA8/C4/C8/C14X2/CMPR + palettes). **Validated against ground truth:** the artist's source `.tga` for `tq0_417` (left on disc next to its `.tpl`) — mean abs diff 4.2/255; eye-verified `ring/ar_a3.png` = WWF.com ring-apron banner.
- **1,167 PNGs** in `textures/` (19 of 43 arenas have same-basename `.tex`; `TEX-MANIFEST.txt`). No `.tex` on disc for: `01`, all `*_ad2` LODs (share base textures), `add_x8/eff_x8/gt_x8/scr_x8/scr_wm/post/c_mat/mat/dummy_x8` (untextured pieces). Doc: `textures/README.md`; extractor: `extract_arena_textures.py`.
- **`ARENA-UNIVERSE-MAP.md`** (PR #18): ~45 arena configurations inventoried; **all 7 Western Heart stages mapped to WMXIX donors**. Principle: WMXIX gives **geometry** (arena layouts, wall structures, outdoor environments, cage frameworks); Eastern Mind gives **soul** (bitmaps, textures, atmosphere, meaning)
- Mapping summary: `bg/00` → Helix Palace (Stage 2, walled); `bg/01` → Octagonal Shrine Par-Fang (Stage 6, walled); `bg/02` → Phantom Marketplace (Stage 5); Revenge Mode outdoor slots (A/C/F/H/P/S/T, 35 env packages) → Plains of Chi-U / Tree of Life / Palace of Dreaming (open stages); `bg/bs/` backstage interiors → Helix interior rooms; `bg/cage/hell.pac` (Hell in a Cell) → **The Drill Wound** (Stage 7 secret — the most direct mapping in the set); `cage.pac` → cage-match concept; prop libraries (`object/` 61, `placard/` 51, `weapon/` 61) → stage dressing
- Decode priority: `hell.pac` → `bg/00` → `bg/01` → one open Revenge Mode environment → `bg/02` → remaining
- Pipeline: decoded arena → OBJ → Blender cleanup (strip WWE branding, rescale to 16.8-unit combat plane) → Eastern Mind retexture → Godot 4 import

## 7. CAW edit_data — Structure Mapped, Catalog Complete (PR #27)

- `edit_data/MODEL/{Man,Woman}/{Category}/{style}_{variant}/{l0,r0}.ymg` — 1,200 part meshes (YOBJ v0x00030001, same as wrestler). 10 categories (Elbow, Face, Gears, Gloves, Hair, Knee, Lower_Body, Shoes, Upper_Body, Wrist); Man Face 77 styles / Hair 76 / Gears 140; Woman similar
- `edit_data/TEX/64gara/` — 1,470 part textures; `edit_data/COL/` — 8 `.ycg` (2× 2,356 B skeleton-size + 6 small palette/override files)
- **Full catalog (2026-10-13):** all **2,690 files** listed with sizes + content signatures in `caw-parts/files.tsv` + `caw-parts/CATALOG.md` (tool: `catalog_caw.py`; files stay on ISO, 54.3 MB total). YOBJ versions present: v00030001 (754), v00040001 (175), v00040002 (32), v00040003 (31), v00030002 (3), v00000000 (3); 202 DUMY placeholders.
- **Artist working files left on disc:** `MODEL/Woman/Face/tq0_417/` contains the source `.tga` art, a `.tm2` (PS2 TIM2), 2 `.psd` (Japanese filenames), a `.tpg`, and `tq0_417_TPL/` with 2 cooked `.tpl` + `script.txt` revealing the build path `D:\MAX_Wwfgc2\edit\woman1\edit_face_woman\mouth\tex\` — this pair validated the TPL decoder (§6). 3 `.ymm` files under `MODEL/Woman/Hair/` (Yukes material format, unexamined).
- Doc: `../wwe-wrestlemania-xix/docs/CAW-EDIT-DATA-WMXIX.md`
- **Blocked:** the created-wrestler SAVE lives on the GameCube memory card, not the ISO. Unblocking needs: Dolphin + ISO → create a CAW with known values → export the `.gci` → diff against the part-id tables. Without a real save, field order/string encoding/stats layout cannot be determined from the ISO alone

## 8. Retarget Pipelines — Proven

### YANM → Tekken 3 (Yukes path)
- **v1** (2026-10-12): `ringmotion/a000_0a.yag` (entrance, 13.93s) → King (BNS record 95); 465 frames @30fps; 6 ycg groups → T3 FK Euler joints; mean-subtraction overlay keeps King's stance, adds wrestling motion; output `docs/yanm_to_tekken3_v1.json` (+ plot). FK only, legs not retargeted
- **v2** (2026-10-13): leg/arm IK (FK the ycg chains → ankle/wrist targets → T3 normalized-skeleton IK channels, pure IK, no double-drive); hinge = ycg local X → world lateral; **leg tracks use half-angle encoding** (`hinge = 2·unwrap(atan2(c2,c1))`, ±180° — the c1 sign-flip "spikes" are the wrap, not glitches; legs swing −13°..+36° sane walk); arms use small-regime asin; hinge→Euler driven on the **Z channel** (sagittal pitch; v1's X was yaw); ycg y+ = R with chirality-preserving map. 574 frames @30fps (19.13s); **render-verified with own eyes** (`docs/retarget_v2_render.png`, `docs/retarget_v2_paths.png`). Tools: `yanm_to_tekken3_v2.py`, `fk_ycg.py`, `render_retarget_v2.py`. Doc: `docs/YANM-TEKKEN3-RETARGET.md`
- Open: knee DOF (YANM leg is 1-DOF); ycg forward sign; absolute ycg L/R proof (needs in-game pose); swivel modulation; root translation (YANM has no root track)

### AKI → Tekken 3 (No Mercy cross-engine path)
- **v1** (2026-10-13): No Mercy move `0x339A` (58 frames) → King; 19 × 1-DOF `PivotRotation` (s8 = degrees, calibrated: `Tekken_s16 = s8 × 182.04`); 9 AKI joints → T3 FK joints; source-vs-retarget motion correlations **0.69–1.0** (pelvis 1.000). This unlocks the ~1,360-clip AKI library for retarget
- Doc/tooling lives in the sister lane: `../wwf-no-mercy/AKI-TEKKEN3-RETARGET.md`, `../wwf-no-mercy/aki_to_tekken3.py`, `../wwf-no-mercy/aki_to_tekken3_v1.json`
- Cross-engine comparison: `../wwe-wrestlemania-xix/docs/YUKES-VS-AKI-ANIMATION.md` — AKI is frame-based (N × 98-byte frames, 25 fixed-order joints, s8 degrees + pivots, explicit root motion); Yukes is track-based (29 sparse delta-timed key streams, 21 1-DOF hinge groups, s16 sin-encoding, common-mode+trim bilateral factorization). Yukes = finer (finer resolution, ~10× more compact); AKI = broader (1,360 anims + move DB linkage)

## 9. Tools

`../wwe-wrestlemania-xix/tools/` (26 tools — streaming, ISO-safe unless noted):

| Tool | What it does |
|---|---|
| `gcn_fst.py` | Pure-stdlib GCN disc FST reader: `list` / `get <path>` / `extract <dir>` (streams from ISO) |
| `yukes_fmt.py` | Yukes format helpers (big-endian readers, `stream_file`) |
| `extract_all_arenas.py` | Extracts all 43 arena YMGs → OBJ point clouds (repo copy in `arenas/`) |
| `yobj_arena_extract.py` | Single-arena extractor (repo copy in `arenas/`) |
| `yobj_strips.py` | Wrestler YOBJ triangle-strip connectivity → OBJ + render (elbow, 000_0) |
| `yobj_diag.py`, `yobj_validate.py`, `yobj_v3_probe.py`, `yobj_batches.py`, `yobj_batch_semantics.py` | Batch-table probes and semantic validation |
| `ycg_parse.py`, `ycg_ymg_map.py`, `fk_ycg.py` | YCG joint-group parsing, ycg↔ymg mapping, ycg FK |
| `yanm_census.py`, `yanm_track_probe.py`, `yanm_keyseg.py`, `yanm_semantics.py`, `yanm_unitfit.py`, `yanm_gait.py`, `yanm_hashscan.py` | YANM track/key probes and semantic fits |
| `yanm_track_joint_map.py`, `yanm_task2_finish.py`, `yanm_task2b.py`, `yanm_rec3_rule.py` | Track→joint mapping, dual-A semantics, rec3 rule proof |
| `yanm_to_tekken3.py`, `yanm_to_tekken3_v2.py`, `render_retarget_v2.py` | YANM→Tekken3 retarget v1/v2 + render |

No Mercy-side tools for the AKI path: `../wwf-no-mercy/tools/anim_extract.py`, `../wwf-no-mercy/aki_to_tekken3.py`.

**Full-extraction tools (2026-10-13, this lane):**

| Tool | What it does |
|---|---|
| `extract_wrestlers.py` | All 111 wrestler slots → OBJ (batch-table locator + pool-scan fallback + DUMY detection + per-slot dedupe; writes `wrestlers/EXTRACTION-MANIFEST.txt`) |
| `extract_yanm.py` | All 170 `ringmotion/*.yag` → `animations/*.json` (full key decode, hash→anatomy, `.atr` companions) |
| `catalog_caw.py` | All 2,690 `edit_data/` files → `caw-parts/files.tsv` + `CATALOG.md` |
| `decode_tpl.py` | GameCube TPL → PNG (all 11 texture formats + palettes; validated vs artist `.tga`) |
| `extract_arena_textures.py` | `.tex` container parse → TPL carve → `textures/<arena>/*.png` (`TEX-MANIFEST.txt`) |

## 10. What's Blocked and Why

1. **Arena face indices** — u16 chunks at material index offsets are mixed data, not clean indices. Parse mesh descriptors at 0x0830+ to link vertex arrays → index arrays, or Poisson-reconstruct the point clouds. (Geometry is usable as point clouds; faces needed for real stage builds.)
2. **Full YANM channel mapping** — directory f32-triple + w24 semantics; A-stream first-8-bytes (header vs 2 keys); authoritative clip duration (`.atr` lead); per-clip hash-set → move-category mapping; identity of the 8 non-ycg track hashes. (Does NOT block retarget — the 21 mapped groups carry the wrestler's motion.)
3. **Wrestler per-vertex skinning** — per-batch bone bind matrices rejected by measurement; need the weight table or the true position-pool semantics. (Rigid CAW parts decode clean; skinned wrestlers need this.)
4. **CAW save-record layout** — blocked on a real Dolphin `.gci` memory-card dump (see §7).
5. **Revenge Mode slot→location identities** — which lettered slot (A0–A4, C0–C2, F1–F6, H3–H9, P0–P3, S0–S5, T0–T3) is the construction site vs parking lot vs mall. Decodes will identify visually; doesn't block the type-based universe mapping.
6. **Wrestler per-vertex skinning for the 6 sub-variant files** — 096_0/097_0 (named-bone v4), 100_0/101_0/102_0 (v2), 110_0 (v1): pool-scan OBJs exist, batch tables unlocated.

## 11. Chimera Build Value

- **Wrestling Mode arenas:** WMXIX arena geometry (rings, cages, outdoor environments) feeds the Eastern Mind stage set — the universe map assigns each arena its destination (see `ARENA-UNIVERSE-MAP.md`)
- **Revenge Mode structure:** mission-based objectives outside the ring → template for Western Heart's arena-traversal missions
- **Create-a-Wrestler / Shopzone:** upgrade economy (attire, weapons, moves, ability points) informs the chimera customization meta-progression
- **YANM retarget pipeline:** proven path for bringing WMXIX wrestling animations onto chimera skeletons (v2: leg/arm IK, render-verified); AKI path gives the 1,360-clip No Mercy library the same door

## 12. Next Steps

1. Arena face indices → real stage geometry (parse mesh descriptors or Poisson reconstruction)
2. Assign decoded Revenge Mode slots to specific Western Heart stages (replaces the type-based mapping with slot-exact assignments)
3. Wrestler per-vertex skinning → fully assembled skinned wrestler meshes
4. Dolphin `.gci` dump → CAW save-record layout
5. YANM 8-unknown track identities (second performer / camera / prop / referee)
6. Wrestling Mode arena pass (separate from the Eastern Mind stage transformation — main show arenas kept closer to wrestling origins)

### 5d. Item-6 cycle 2 — ECD via semantic clips, record-type taxonomy, byte-ramps (2026-10-13)

- **ECD28978 — face-driver DOWNGRADED, camera-framing now leads**: the only
  semantically-named clips (`viewer/motion/FACE.yag` / `HAND.yag` /
  `FIGHTING.yag` / `SAMPLE.yag`) were probed. FACE.yag is **fully static**
  (0/36 tracks animated) — the face showcase animates nothing, and its ECD
  pose (0, 79.9) is identical to HAND.yag's and shared with 11 ringmotion
  moves. No face-specific ECD behavior exists anywhere. New leading
  hypothesis: **per-move camera framing preset (yaw/pitch)** — static per
  move, 87 presets, ±80° as angles, variant-specific cinematics,
  engine-consumed (0/1464 ymg + 0/175 ycg contain ECD bytes, full-file scan),
  FIGHTING≈(0,0) = default cam, 85xx showcases reuse 9 framings. Eye-gaze
  possible; opponent-setup weakened; face-pose has no positive evidence.
- **Record-type taxonomy (new)**: Type A (`a==0`) = keyframed angle tracks
  (body, fingers, ECD w28=1 static pose). Type B (`a!=0`,
  `w28=0x0001xxxx`) = static detail/attachment records — **0C5BF279 was never
  a track** (it is Type-B, with the ymg ID-block binding); 24 more Type-B
  hashes exist only in FACE/HAND.yag (viewer-showcase rig extras, identical
  values in both). CORRECTION: the prior cycle's r(ECD,0C5BF279)=0.072/0.010
  correlations are VOID (Type-B "channel values" were misread key offsets).
- **Byte-ramp curves characterized**: record 14 (66 words) = `[selfptr,0]
  [3,0x32] [3 byte-packed words] [0C5BF279] [12-word ID block] [3 ID-like
  words] [0xA8=168 length] [168-byte region]`. The 168B region: 18 distinct
  values, 0x44-dominated (109/168), smooth ramp segments + 8 outlier bytes —
  most consistent with quantized remap curves / 1D LUT. Identical for
  000_0/047_0 (correlates with ID block, not wrestler); 045_0/016_0 use a
  different table format without byte ramps.
- Base-ID gen fn and anatomical L/R: unchanged (still open / still blocked
  headless). Full analysis: `./YANM-ITEM6-CYCLE.md` (cycle-2 section).
