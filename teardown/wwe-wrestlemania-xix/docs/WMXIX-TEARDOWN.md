# WWE WrestleMania XIX — Teardown

## Game #4 in Western Heart Chimera Build
- **Role:** Additional modes, arena traversal, Revenge Mode structure
- **Developer:** THQ (Yukes engine — different from AKI)
- **Platform:** Nintendo GameCube
- **Game ID:** GW9E78
- **ROM Status:** ✅ DOWNLOADED + VERIFIED 2026-10-12 — `WWE Wrestlemania XIX (USA).iso`
  (1,459,978,240 bytes, MD5 `c13c47a5ed24a675545c99a15e44529d` — matches source listing;
  disc header: Game ID `GW9E78`, name `WRESTLEMANIA XIX`, magic `C2339F3D`).
  Source: CDRomance (via browser task, no signup/payment needed).

## Download Sources (for parent browser delegation)
1. https://cdromance.org/gamecube/wwe-wrestlemania-xix-usa/ (Game ID GW9E78, MD5: c13c47a5ed24a675545c99a15e44529d)
2. https://www.gamulator.com/roms/gamecube/wwe-wrestlemania-xix (has "Direct" download option)
3. https://Coolrom.com/roms/gcn/40659/WWE_WrestleMania_XIX.php
4. https://www.freeroms.com/roms/nintendo_gamecube/wwe_wrestlemania_xix.htm

## Known Features (from research)
- ~40 WWE wrestlers on roster
- **Revenge Mode:** mission-based mode (not traditional story) — objectives in various settings beyond the ring
- **Create-a-Wrestler:** highly customizable, modify "every little nuance"
- **Create-an-Entrance:** more control than any wrestling game to date
- **WWE Shopzone:** spend earned money on attire, weapons, moves, ability points
- Improved graphics over WrestleMania X8, more realistic moves

## Key Differences from No Mercy (for Western Heart design)
- Yukes engine vs AKI engine — different animation philosophy
- GameCube hardware — higher poly, better textures than N64
- Revenge Mode arena traversal — fighting OUTSIDE the ring in various environments
- This informs the "Wrestling Mode" arena design in Western Heart

## TODO
- [x] Download ISO (verified MD5) — DONE 2026-10-12
- [x] Map file structure — DONE 2026-10-12 (streaming FST parse, no full extraction —
  disk at 89%, so no 1.4GB duplicate; tool reads directly from ISO offsets)
- [ ] Extract character models (YOBJ format decode — streaming via gcn_fst.py `get`)
- [ ] Decode YANM animation format
- [ ] Document Create-a-Wrestler save format (edit_data/ layout)
- [ ] Document Revenge Mode arena designs (bg/ arena sets)
- [ ] Compare Yukes vs AKI animation approach

## File Structure (mapped 2026-10-12 via tools/gcn_fst.py — pure-Python GCN FST reader)
- 5016 FST entries, 4222 files, 1.41 GB total (compressed/scrubbed ISO = 1.46 GB on disk)
- FST header note: on this disc the FST offset/size live at header 0x424/0x428
  (0x362F00 / 0x1A8A3), NOT 0x420 — tool handles this.
- `model/wrestler/` — 484 files: per-slot model groups `NNN_M` (slots 000–110 = 111 slots):
  `_0` always `.tex` + `.ymg` + `.ycg`; `_1` second variant (alt attire) on 66 slots;
  `_2`/`_3` on a handful. More slots than the ~40-man roster — extras likely CAW
  parts, managers, refs, divas.
- `ringmotion/` — 340 files: move animation pairs `.yag` (YANM skeletal anim, median
  38.6 KB) + `.atr` ("DATA" metadata, median 388 B — 16-byte records, describes its
  .yag companion). Letter groups: a=68, b=46, c=208, d=12 — likely move categories
  (attack/grapple/strike/special). Includes `cnv.bat` (build-time converter left on disc).
- `motion/*.mpc` — shared move packages (common, move, win, nyujo_ch entrance).
- `edit_data/` — 2690 files: CAW creation suite parts — MODEL/ (1213), TEX/ (1469), COL/ (8).
- `bg/` — 373 files: arena sets (per-arena `.ymg`/`.ycg`/`.tex` + `.pac` arena packages,
  `weapon/` 61, `object/` 61, `placard/` 51 — Revenge Mode out-of-ring environments here).
- `Entrance/` — Create-an-Entrance data (CamData.dat, EffData.dat, entpac.mpq).
- `viewer/` — dev-viewer assets (TestEffect.gef, motion/ test anims).
- `2d/`, `thp/` (videos), `tutorial/`, `paint_tool/` (CAW paint tool UI).

## Proprietary Format Magic (first structural pass)
- `.ymg` → **`YOBJ`** — YUKE's mesh/object format (models, arenas, ring).
  Sample `model/wrestler/000_0.ymg` (69,176 B): `59 4F 42 4A` = "YOBJ".
- `.yag` → **`YANM`** — YUKE's skeletal animation. Header: `59 41 4E 4D` "YANM",
  then u32 (payload size ≈ file size − header), constant `0x011F0000`, u32 = 8,
  then `0xCD89A39E`. Sample `ringmotion/a000_0a.yag` (22,674 B): header size 22,500.
- `.atr` → **`DATA`** — 16-byte records, per-animation attribute table (36–2532 B,
  median 388). Sample `ringmotion/a000_0a.atr` (218 B = 100-byte header + 8 records × 16?).
- `.ycg` — no ASCII magic (`00 00 00 2A ...`); small (2.3 KB) — skeleton/graph or
  camera data, always paired with `.ymg`.
- `.tex` — textures (need TPL/TXTR check), `.mpc` — move packages, `.pac` — arena packs.

## Tool: tools/gcn_fst.py
Pure-stdlib GCN disc FST reader. Modes: `list` (full file listing), `get <path>`
(extract single file by streaming from ISO — no full extraction, disk-safe),
`extract <dir>` (full tree — avoid at high disk usage).

## Tool: tools/yukes_fmt.py (new 2026-10-12)
Structural probe for YOBJ/YANM/YCG: streams files from ISO byte ranges (disk-safe),
prints u32/float header words, finds plausible file-internal offsets, scans for
ASCII section tags. Usage: `python3 tools/yukes_fmt.py <disc/path/file> [...]`.

## YOBJ (.ymg) structural decode v1 — MEASURED (sample: model/wrestler/000_0.ymg, 69,176 B)
- Header 64+ bytes of u32 fields. Confirmed internal offsets (u32 value < file size,
  target non-zero):
  - `[0x04]` → `0x10D80` (target blob `ddfd 7a6e dffb a6f5 0f46 3000 0000 0a8…`) —
    dense packed data = **vertex/index payload region** (last ~1.2 KB of file).
  - `[0x1C]` → `0x10704` (target `32 00 70 00 cc cc cc cc b2 b2 b2 ff …`) —
    GCN GX display-list region (0x32/0x98-class primitive bytes, matrix indices).
  - `[0x3C]` → `0x10D44` (target `04 07 07 07 00 50 04 0c 0c 5b f2 79 00 18 79 6d…`) —
    byte-triplet descriptor table = **vertex attribute format descriptors**.
  - `[0x38]` = `0xF360`, `[0x14]` = `0xF3B4` — mid-file section area.
- Section tags found in file (ASCII scans): `GCTC` @0xF370, `FIXE` @0xF384 —
  real section markers (not keyframe noise). Trailing `ABBB…/DDDD/EEEE/WWWW` runs
  @0x10D90+ are saturated-data patterns inside the vertex payload, not tags.
- HYPOTHESIS (not yet verified): layout = header → GCTC/FIXE section table (~0xF370)
  → GX display list (~0x10704) → attribute descriptors (~0x10D44) → vertex payload
  (~0x10D80). Next: decode GX DL command bytes to recover draw calls + attribute
  strides, then map vertices to triangles.

## .ycg structural decode v1 — MEASURED (sample: model/wrestler/000_0.ycg, 2,356 B)
- `[0x00]` = `0x2A` = **42** — matches the No Mercy wrestler-ID-table count (42) by
  coincidence; here it reads as a joint/entry count.
- From `0x14`: repeating records of the form `05 00000000 00000000` + four f32 that
  are all ±0.5 variants (`0x3F000001`=0.5, `0xBEFFFFFE`≈−0.5, 0.5001/−0.4999…) =
  **normalized rotation quaternions** (±0.5 components = 120°-class base rotations).
- Pairs like `415030A1`=13.01 f, `40EA72D6`=7.327 f, `413922DC`=11.57 f read as
  floats (plausible joint-scale or bone-length values); interleaved `00000005`
  counts suggest per-joint child-count fields.
- VERDICT (measured): `.ycg` is the **skeleton file** — joint count + per-joint
  local rotations (quats) + scalar params — always paired 1:1 with a `.ymg` mesh.
  This is the Western Heart retarget source: Yukes joint rotations → Tekken 3 bones.
  Next: segment the 42 records, recover parent/child hierarchy from the count fields.
- UPDATE v3 (2026-10-12): `.ycg` refined to **animation rig**: 42 records /
  21 unique joint hashes (dup counts 2–3); 21 of 29 YANM track hashes match it
  exactly. The 70-bone `.ymg` is the separate RENDER rig. See "YANM (.yag)
  track-directory decode v3" above.

## YANM (.yag) structural decode v1 — MEASURED (sample: ringmotion/a000_0a.yag, 22,556 B)
- `[0x04]` = `0x57E4` = 22,500; file size − 22,500 = **56 (0x38) = header size**.
- `[0x08]` = `0x011F0000` (constant), `[0x0C]` = `0x08`, `[0x10]` = `0xCD89A39E`
  (magic constant — same as noted in v0 pass).
- Section offsets in header (all land on non-zero data): `0x3E8`, `0x3EC`, `0x3F4`,
  `0x7E0`, `0xCC8`, `0xE6C`, `0x124C`, `0x1564`, `0x1574`, `0x1804`, `0x180C`, `0x1C80`.
- `0x3C` = `0x3CE51EBD` = **0.02797 as f32** — plausible per-frame delta (≈1/35.75 s;
  NTSC-adjacent; exact frame rate TBD). `0x40`–`0x48` = 0.5146 / 1.887 / −0.2931
  floats (anim params — root-motion or blend values, TBD).
- `0xCC8` region bytes (`59 02 ff 59 ff 59 02 bf c1 3f c1 3f 00 c1 3f c1…`) and
  `0x124C` (`00 01 00 02 00 01 00 02 ff f9 00 7e 00 ff f9 00…`) read as
  **s16 keyframe delta streams** (small signed 16-bit values around 0).
- `0x57F4` "ABAG/BAGAHGA…" hits are s16-stream byte patterns, not section tags.
- VERDICT (measured): 56-byte header + ~12 section offsets + s16 delta keyframe
  streams. Next: associate each offset with a joint from the .ycg skeleton
  (42 joints vs N tracks), recover frame count from the 0x3E8 track table.

## YOBJ (.ymg) structural decode v2 — MEASURED (2026-10-12, sample: model/wrestler/000_0.ymg, 69,176 B)

### YOBJ header map (all offsets MEASURED, big-endian u32)
| offset | value | meaning |
|---|---|---|
| 0x00 | `YOBJ` | magic |
| 0x04 | 0x10D80 | tail/descriptor region offset |
| 0x08 | 0x00040001 | version? |
| 0x0C | 0x40 = 64 | (header-related) |
| 0x10 | 0x47 = 71 | bone-slot count (matches 71×64B table) |
| 0x14 | 0xF3B4 | bone name/table offset |
| 0x18 | 0x0F = 15 | ? |
| 0x1C | 0x10704 | material/draw table offset |
| 0x20 | 0x19 = 25 | ? |
| 0x24 | 0x10574 | texture-name table offset |
| 0x38 | 0xF360 | GCTC/FIXE section-table offset |
| 0x3C | 0x10D44 | 60-byte vertex-format descriptor? (unverified) |
| 0x5C | 0x5AE0 | ? (region has 0xFFFF strip-like u16 runs — unidentified) |
| 0x60 | 0x7CA0 | per-bone skin batch table offset |
| 0x64–0x6C | −98.21 / −4.252 / 142.0 | f32 triple — bounding? (unverified; 142 ≈ model height) |

v1's "GX display list @0x10704" hypothesis is WITHDRAWN — that region is the
material table (below). No GX DL signature found; vertex data is quantized
(s8/s16), not f32 (f32 scan found only zero padding).

### Skeleton: 70-bone table (FULLY DECODED — the retargeting gold)
- 71 slots × 64 bytes at 0xF3BC. Slot 0 = "null" sentinel (parent 0xFFFFFFFF).
  Slots 1–70 = bones. Full table: `docs/WRESTLER-SKELETON.md` + `docs/wrestler-skeleton-000.json`.
- Slot layout (MEASURED): name[16] ASCIIZ | u32 parent (1-based slot idx) |
  f32 pos xyz | f32 euler xyz (radians) | f32 bone-length | 16 zero bytes.
- Hierarchy: Bip→Pelvis→Spine→Spine1→{Neck→Head→12 facial bones, L/R Clavicle};
  Clavicle→UpperArm→{UpperArm_s (twist helper), Forearm→Hand→{Hand_s, 15 finger bones/side}};
  Pelvis→{L/R Thigh→{Thigh_s, Calf→Foot→Toe0}}.
- 30 finger bones + 12 facial bones + 28 core = 70. Left/right symmetric
  (verified: L/R positions mirror, eulers mirror).
- NOTE: child position ≈ (parent_length, ~0, ~0) for limb bones — bones extend
  along local +X. Bip root pos = (0, −102.69, 0) (measured; axis convention TBD).

### .ycg = 42-joint file (header [0x00]=42 MEASURED; record layout OPEN)
- Size 2,356 B. First record @0x14 shows unit quats (±0.5)⁴ = 120° rotations.
- Count observation: 30 finger + 12 facial = 42 EXACTLY. Hypothesis: .ycg holds
  the finger+face "detail" joints (or another 42-subset) — NOT verified, do not
  treat as fact. The .ymg table is the authoritative skeleton.

### Skin batch table @0x7CA0 (MEASURED, 8-byte records)
- Record: u8 bone_idx, u8 count, u8 0, u8 count, u32 offset (offset relative to
  file 0x80 = bulk-data start; last batch ends at 0xF338, just before GCTC —
  confirms the base).
- 13 records covering bones 0–12 (root + spine chain + face) — this table is the
  HEAD part's skinning; other parts have their own tables (not yet located).
- Target blocks are u16 triplets (606 total here). Interpretation OPEN:
  as s16 positions they overlap per-bone (not bone-local); as
  (pos_idx, nrm_idx, uv_idx) the attribute arrays are unlocated.

### Material table @0x10704 (MEASURED)
- 4-byte header `32 00 70 00`, then 57 records × 28 bytes:
  [u32=0xCCCCCCCC][RGBA diffuse][RGBA ×2][u32=0][u16=1][u16 offset].
- u16 offsets increment by 0x5C (92): 0x830, 0x88C… — relative to 0x7CA0;
  each 92-byte chunk is u16 index-like data (all values < 3000, max 1842).
- Record 0's 46 indices form a plausible triangle list (low degenerate count).

### Texture-name table @0x10574 (MEASURED)
- Null-padded entries: `Ehhh_body.pic`, `AMEhhh_arm.pic`, … then `.bmp` entries
  (`m_hhh_waists.bmp`, `pm_hhh_arm.bmp`, …, `g_dummy.bmp`, `blood.tmd`).
- Prefixes E/AME/m_/pm_/g_ = texture variants (unverified semantics).

### Mesh vertex positions: CRACKED (2026-10-13, verified)

- **Batch-table s16x3 runs ARE the position arrays.** For `000_0.ymg`:
  606 verts across 13 batches, values 0–1921 (Yukes units). Dequantization
  **/64** gives model units 0–30 (checked /16, /32, /64 — /64 is the sane
  character scale). Point cloud renders as coherent character geometry
  (verified by eye: `tools/yobj_validate.py` → OBJ + 3-view check renders).
- Batches overlap in one shared 0–1900 space (not bone-local); the `bone`
  field groups verts for skinning/materials, not separate spaces.
- **CAW parts use the same scheme with u16x3.** Elbow
  `me0_000/l0.ymg`: **148 verts** as u16x3 at file `0x4D8`–`0x850`
  (values 0–1224, /64 → 0–19 units); renders as a coherent curved shell =
  the elbow-pad shape. Preceded by a 16-byte descriptor at `0x4C8`.
- **Correction to v3 notes:** the "150-triangle u16 index list @0x4C8
  (max idx 1224)" was a misread — 1224 was a *coordinate*, and the region
  is descriptor + 148 vertex positions, not triangles.
- `tools/yobj_validate.py`: streams from ISO, extracts batch verts, writes
  OBJs at /16 /32 /64 + matplotlib check renders (disk-safe, no extraction).

### Mesh triangle connectivity: CRACKED (2026-10-13, verified by eye)

- **There are NO separate index buffers.** Triangles are formed implicitly by
  **triangle strips**: each vertex run is strip-ordered (ladder/zigzag), and
  triangles = consecutive triples (v_i, v_{i+1}, v_{i+2}) within a strip.
- **Strip boundaries** are found by edge-length bimodality: intra-strip steps
  (~100–200 raw units) vs inter-strip jumps (800–2100). Split at jumps >
  max(400, 4×median). Separator verts are single near-origin verts
  (e.g. `(35,0,19)`, `(0,0,0)`) between strips — not part of any triangle.
- **Evidence:** each strip renders as a smooth surface patch (verified
  visually, per-strip colored renders). The "dense u16 runs" in file gaps are
  NOT index buffers (coordinate-scale values, zero runs); no valid index
  buffer referencing the vertex list exists in the file.
- **Exports:** `objs/elbow_me0_000_l0.obj` (148 verts, 14 strips, 113 tris),
  `objs/wrestler_000_0.obj` (606 verts, 58 strips, 383 tris).
  Tool: `tools/yobj_strips.py` (streams from ISO, disk-safe).
- OPEN: strips are smooth individually but scattered globally — vertex
  positions need per-strip/per-vertex skinning transforms (bone matrices)
  to assemble. That is a position issue, not connectivity. Also open:
  assembling `000_0` + `000_1` into the full base mesh.

### Create-a-Wrestler part format (MEASURED)
- `edit_data/MODEL/{Man,Woman}/{Elbow,Face,Gears,Gloves,Hair,Knee,Lower_Body,Shoes,Upper_Body,Wrist}/<style>_<variant>/{l0,r0}.ymg`
- Parts ARE YOBJ files (same magic, same header version 0x00030001).
  Sample `MODEL/Man/Elbow/me0_000/l0.ymg` (6,936 B): header [0x10]=0x48,
  [0x14]=0x854, [0x1C]=0x1A84 — smaller tables, same layout family.
- So the CAW suite assembles wrestlers from YOBJ part files per body region —
  directly reusable: extract any part with the same YOBJ parser as base models.

## YANM (.yag) track-directory decode v3 — MEASURED (2026-10-12, sample: ringmotion/a000_0a.yag, 22,556 B)

### Track directory (0x50–0x3EF, 29 × 32-byte records)
- The bytes at `0x50`–`0x3EF` parse cleanly as **29 records of 32 bytes each**
  (`0x50 + 29*0x20 = 0x3F0`); parsing stops exactly at the `0x3E8/0x3EC/0x3F4`
  section offsets noted in v1 — those offsets are the END of the directory, not
  a separate table.
- Record layout (all big-endian):
  `[u32 joint_hash][u32 trackA_off | 0][u32 keystream_off][u32 0][f32 f32 f32 | 0][u32 keycount_word]`
- **Single-track** records (`trackA_off = 0`): `keycount_word` = key count `n`;
  key stream = `n` × 5-byte keys at `keystream_off`, padded to a 4-byte boundary.
- **Dual-track** records (`trackA_off ≠ 0`): `keycount_word` packs
  `(countA << 16) | countB`; track A = `countA` × 4-byte keys at `trackA_off`,
  track B = `countB` × 5-byte keys at `keystream_off`.
- Measured on a000_0a.yag: 26 single + 3 dual tracks. Dual example
  `7CC9B660`: trackA_off=0xE6C with ca=248 (4B keys), keystream_off=0x124C with
  cb=158 (5B keys).

### Hash → joint confirmation (the rig question, ANSWERED)
- **21 of the 29 track hashes EXACTLY match the 21 unique joint hashes of
  `model/wrestler/000_0.ycg`.** Re-verified 2026-10-12 20:00 CDT via
  `tools/yanm_census.py` (29 tracks, 21 matched).
- `.ycg` = 42 records (2,356 B = 42×56+4), 21 unique hashes (duplicate counts
  2–3 per hash — joint-groups, not clean L/R mirroring).
- This CONFIRMS: **`.ycg` is the animation rig YANM targets** — 42 records /
  21 unique joint-groups — and the 70-bone `.ymg` skeleton is a SEPARATE
  render rig. YANM tracks drive the 42-record rig.
- ycg hash sets are universal across wrestler slots (12 slots checked — each
  slot's set is a subset of 000_0's 21): **one YANM decode retargets to ALL
  wrestlers.**

### Key stream formats (measured via `tools/yanm_keyseg.py` smoothness tests)
- **5-byte keys**: two s16 value channels + one u8 `dt` (time-delta) channel.
  Segmentation tests on 3 streams: `y` as the FINAL 2 bytes is strongly
  confirmed (smooth_y 27.9–548.5 vs 619–2389 for y-in-middle). Smoothest read
  overall: `(x: s16/u16, dt: u8, y: s16)` — dt in the middle byte,
  mean dt ≈ 3–11 per key. x-vs-dt byte order in the first 3 bytes still under
  test.
- **4-byte keys**: `(s16, s16)` pairs. In dual-track 7CC9B660-A (248 pairs),
  the second channel reads as near-constant small values (…,2,2,2,2,2,…) after
  the first two keys — suggestive of a 2-channel curve sharing track B's time
  base (hypothesis: track A = 2 components, track B = 1 component + dt =
  one 3-component rotation/position curve split across two tracks).
- Single-track key counts verified by stream-length math (`n×5 + pad-to-4`)
  across a/b/c-group files: same 29-hash directory order, same 8 unknown
  hashes in each file.

### The 8 unknown-hash tracks (measured, identity OPEN)
- `ECD28978, A4955E6E, 579B8E50, BA955E6E, 579B89D0, 1E7FD58C, 007FD58C`
  (7 single tracks, each exactly 1 key) + `0C5BF279` (dual, ca=1, cb=1).
- These hashes appear in NO wrestler `.ycg`. All are static 1-key tracks —
  candidates: second performer, camera, or prop attachment points.
- Same 8 appear in a/b/c-group files → they are structural, not per-file noise.

### Entrance-anim provenance
- `ringmotion/cnv.bat` found on disc (190 B): `yma2yag Nyujo_YMA/*.yma →
  ringmotion/*.yag` (Nyujo = 入場 = "entrance"). **ringmotion/*.yag are the
  wrestler ENTRANCE animations**, converted from Yukes' internal `.yma` by
  their `yma2yag` tool. Companions: `yma2atrgc` → `*.atr`.

### OPEN (next steps)
- ~~Exact channel→quaternion-component mapping: dual-track semantics, dt time
  unit vs the 0.02797 f32 at YANM header 0x3C, how key streams rebuild
  per-joint rotations.~~ → RESOLVED 2026-10-12 ~21:00 CDT, see
  "YANM task-2 finish" below.
- ~~Remaining: dual-A value semantics, chain 2ch→3rec assignment, hinge axis
  per record.~~ → ALL THREE RESOLVED 2026-10-13 ~06:20 EDT, see
  "YANM task-2 finish" (2026-10-13) below: dual-A = bilateral common mode
  (rec_i = A + B_i, key format corrected to (s16,u8,u8)); ch1→rec1,
  ch2→rec2, rec3 fixed; hinge axis per group (X limbs, Z head/accessory, Y 60F8).
- ycg-group → ymg-bone anatomical mapping (connect the 21-joint anim rig to
  the 70-bone render rig so YANM tracks can pose the visible model).

## YANM task-2 finish — MEASURED (2026-10-12 ~21:00 CDT; tools/yanm_semantics.py, tools/yanm_unitfit.py)

### 5-byte key format (CONFIRMED)
- Layout `(s16 ch1, u8 dt, s16 ch2)` — dt = **middle byte**, confirmed as a
  *delta* (not absolute time): the byte is non-monotonic (`[0,2,0,2,2,2,4,2,20,…]`,
  range 0–22 on typical tracks), bouncing rather than accumulating.
- Channel encoding: **ch = 32767 · sin(hinge angle)**, i.e.
  **hinge angle = asin(s16 / 32767)** radians (≈ s16/32767 rad for small angles).
  Evidence: (a) channels saturate at ±32767 (= sin ±90°: e.g. 32512, 31990,
  −29683); (b) track BD5B5259's (ch1,ch2) points lie on a circle of radius
  32767 with smoothly decreasing atan2 angle 85.1°→72.7° over 221 keys;
  (c) track 099CD766 decodes via asin to two small hinge angles (±6°) that stay
  smooth while atan2(x,y) is noise (magnitude≈0) — ruling out atan2-angle and
  direct-s16-angle readings.

### 4-byte key format / dual tracks (CORRECTED + RESOLVED 2026-10-13)
- Dual-track A keys are **(s16 value, u8 flags, u8 dt)** — CORRECTION of the
  earlier `(s16 value, s16 dt)` reading: the middle two bytes are a flags byte
  + a u8 dt (dt-sum check against B confirms: e.g. 2416 vs 2394 ticks on
  a.yag/7CC9B660; 494/498 and 1000/1000 on a000/a001-style dense tracks).
  Stream = 8-byte header (magic `C1 3F C1 3F` in some files, e.g. a.yag;
  per-track/per-file otherwise, e.g. `c24006c2 40c24002` in a000_0a) followed
  by (ca−2) keys. Flags byte = 0 on hold keys, varying on angle keys;
  8-byte header semantics still OPEN.
- **dt-sum(A) ≈ dt-sum(B)** verified on 310 dual tracks (169 ringmotion
  files): A and B span the same clip duration. Dense variant (a000-style):
  dt=2 constant; sparse variant (C13F-style): dt=2 on angle keys, 47–255
  hold keys.
- Structural rule holds across all 29 tracks: **dual ⟺ nonzero f32 triple**
  in the directory record (singles all have exactly (0,0,0); duals carry
  ≈(−0.0024, 0, 0.0002), semantics OPEN).
- **A's value semantics RESOLVED: bilateral COMMON-MODE hinge angle.**
  A uses the same asin(s16/32767) angle encoding as B (range to ±80° —
  translation ruled out). Per-record total: **rec_i(t) = A(t) + B_i(t)** on
  the group's primary hinge axis; B = per-side differential trims.
  Evidence: (1) r2(A ~ B1,B2) ≈ 0.00–0.05 on all 310 tracks — A is an
  independent component, not derived from B; (2) symmetric clip a.yag
  64DB300F: A = ±80° pulses dominate, B tiny (±6.5°/0–34°), totals
  corr(T1,T2) = +0.86 (bilateral symmetric); asymmetric clip a000_0a:
  A small (−8.3..0°), B large (B1 −0.7..77.5°, B2 −64.9..0.9°),
  corr(T1,T2) = +0.16; (3) max|A+B_i| ≤ 92.3° over all tracks — totals
  respect joint ROM, consistent with same-axis addition; (4) dual tracks
  exist ONLY for the symmetric-motion 2-record groups (64DB300F, 7CC9B660,
  0C5BF279); the other 2-record groups (347D3654, 613B7547/B7) use single
  tracks (ch1→rec1, ch2→rec2). The old "+0.93 pelvis correlation" was an
  artifact of the misparsed dt column — with correct parsing all
  |corr(A, pelvis)|, |corr(A, head)| < 0.35 (310 tracks).

### Header ↔ key time semantics (CONFIRMED)
- Header `[0x3C]` f32 = **seconds per dt tick** (re-verified value 0.0279688 on
  a000_0a.yag): 498 ticks × 0.0279688 = **13.93 s** clip; cross-file check
  a001_0a.yag: `[0x3C]`=0.03981318 × 1000 ticks = **39.81 s**.
- Header `[0x30]` = 0x10B4F0 is CONSTANT across files (not time; semantics open).
- Per-track tick totals: most animated tracks cluster 460–560; a few reach
  673–930 via large-dt hold keys (dt up to 255). Static 1-key tracks hold one
  pose (dt 0–2, or 252/255). The 460-vs-930 variance is real data, cause OPEN.

### How key streams rebuild per-joint rotations (MODEL, measured basis)
- `.ycg` = 42 records in **21 joint-groups**: 8 singles (1 record),
  **5 L/R pairs** (same quat, y-mirrored positions, e.g. 7CC9B660 at
  (10.82, ±4.54, 2.96)), 8 **3-chains** (positions stepping along a limb,
  e.g. 7AD45E02: x 5.82→15.20→22.57).
- The 21 YANM tracks (19 single + 2 dual) match the 21 groups 1:1.
- **Each ycg record is a 1-DOF hinge; each 5B channel drives one hinge.**
  Pairs: ch1→L record, ch2→R record (ch1–ch2 correlation +0.04 to +0.70 —
  in-phase, not anti-phase, so not a walk-cycle leg pair; anatomy TBD).
  Single-record groups (2 channels, 1 record) = 2-DOF joints.
  Dual-track pairs: B = (α_L, α_R), A = 1 extra shared channel.
- The ycg rest quats are all "nice" basis rotations (0.5/0.707/0/1 — 90°/120°
  frame alignments), i.e. **hinge frames**; the hinge rotates about the local
  principal axis that maps to world lateral ±Y — **RESOLVED per group, uniform
  within each group** (see "YANM task-2 finish" 2026-10-13 below).
- The 8 unknown-hash static 1-key tracks appear in NO wrestler .ycg —
  identity OPEN (2nd performer / camera / prop candidates, unchanged).

## YANM task-2 finish — MEASURED (2026-10-13 ~06:20 EDT; tools/yanm_task2_finish.py, tools/yanm_task2b.py, docs/yanm-task2-finish.json)

### Hinge axis per group — RESOLVED
- For every one of the 42 ycg records, the rest quat maps exactly one local
  principal axis to world lateral ±Y (mirror pairs differ in Y, so ±Y is the
  lateral axis). The mapping is **uniform within each group** but varies
  across groups:
  - **local X** (13 groups): legs BD5B2A59/5259, arms 6198F425/4D5, torso
    613B7547/B7, pelvis 099CD766, 347D3654, 64DB300F, 7CC9B660, 095CD669,
    637B7003/F3
  - **local Z** (6 groups): head/neck 5B214D41/4E, accessory chains
    7AD45E02, 6865B2C0/CF, 64D45E02
  - **local Y** (2 groups): 60F8F527/D7
- Independent FK confirmation (clip a000_0a, walk/hold section): hinging the
  leg chain about local X concentrates 100% of distal motion in the sagittal
  (world X–Z) plane (lateral/sagittal variance ratio 0.000) vs 9.241 about Y
  and 5.221 about Z. Arm chain: X → 0.000 vs Y 11.007 / Z 23.812. Accessory
  chain 7AD45E02: Z → 0.000 vs X 131.876 / Y 2.416 — proving the accessory
  chains genuinely hinge about a different local axis (their rest quats are
  a different family, as task-3 noted).
- This also explains task-3's "quat family differs" observation for 7AD/6865.

### Chain 2ch→3rec assignment — RESOLVED
- **ch1 → rec1 (proximal: hip/shoulder), ch2 → rec2 (middle: knee/elbow),
  rec3 (ankle/wrist) has NO channel — hold at bind** (or solve procedurally).
- Evidence: ch2 range over 331 leg tracks (169 clips): min 4.1°, median
  55.3°, **max 146.3°** — knee-scale motion, anatomically impossible for an
  ankle (ROM ≈ ±35°). Arm ch2 to 82.8° = elbow-scale. ch1 always spans
  ≈ ±80° (bind→stand snap + locomotion). No group has a third channel
  (21 tracks = 21 groups, 1:1), so rec3 is undriven in the data.
- Functional check: FK with ch1→hip shows +80° = leg straight down
  (standing); the ycg bind pose (0°) is legs-horizontal, i.e. animators key
  relative to a seated-style bind and the clip's first keys stand the
  character up.

### Still OPEN after task-2 finish — STATUS 2026-10-13 ~07:30 EDT (tools/yanm_track_joint_map.py, tools/yanm_rec3_rule.py, tools/yobj_batches.py; docs/yanm-track-joint-map.json, docs/yanm-rec3-rule.json)
- ~~Dual-A 8-byte header meaning~~ → REFINED: the A stream is **ca × 4 bytes,
  byte-contiguous** (region-length proof: next-stream-offset − a == ca*4 on all
  75 duals surveyed across 25 clips — there is NO separate header region).
  The first 8 bytes are AMBIGUOUS: C13F-magic style (`C13FC13F 00000000` in
  a.yag sparse tracks) vs 2 plausible keys (dense a000-style). Byte length is
  identical either way (8+(ca−2)*4 == ca*4), so only the first-8B *interpretation*
  is open, not the layout. **CORRECTION to the 2026-10-13 claim:** "dt-sum(A) ≈
  dt-sum(B) on 310 dual tracks" does NOT hold generally — recheck over 518
  duals: 212 match under header-model, 27 under no-header, 279 under NEITHER
  (e.g. a.yag/7CC9B660: A=2014/2077 vs B=2394 ticks). A-streams are sparse
  (hold/angle key pattern CONFIRMED: value=0,flags=0 = HOLD with dt 47–255;
  value≈±32000,flags≠0,dt=2 = ANGLE) and may end before B; the player evidently
  holds the last A value. Degenerate duals (ca=1,cb=1, e.g. 0C5BF279 in every
  clip) = 1 bare 4B A-key + 1 5B B-key, no header room (B starts at a+4).
- ~~Per-track tick-total variance (460 vs 930)~~ → EXPLAINED as authoring
  variance: measured all 29 tracks × 3 clips; totals differ up to 2× WITHIN one
  clip (a000_0a: 347D3654 = 930 ticks = 26.0 s vs dual-B = 498 = 13.9 s).
  Driven by large-dt hold keys (dt up to 255) at real motion points — NOT
  trailing padding (347D3654's 255/191-dt holds are at the START, motion
  continues throughout). Retarget-safe handling: hold-last-value when a track
  ends early; clip (or hold) when it runs long. Authoritative clip duration
  likely lives in the `.atr` companion (lead: `.atr` "DATA" records carry
  0x34_XXXXXX fields — 157/190/370 for a000_0a — decode open).
- ~~8 unknown static track identities~~ → VERIFIED in **0 of 154** wrestler
  `.ycg` files (all sizes): 007FD58C, 0C5BF279, 1E7FD58C, 579B89D0, 579B8E50,
  A4955E6E, BA955E6E, ECD28978. NOT always static (c000_0a: A4955E6E n=10 keys,
  007FD58C 167 ticks). Value patterns look paired (579B8E50 ≡ 579B89D0 =
  (0°, 79.9°); 1E7FD58C ≈ 007FD58C = (44.1°, ∓44°)) — like L/R joint pairs.
  Leading hypotheses: 2nd performer subset / camera / prop / referee tracks.
  Identity still OPEN.
- ~~rec3 (ankle/wrist) procedural handling~~ → **RESOLVED: rec3 = −(rec1+rec2)**.
  FK test (leg BD + arm 6198 chains, clips a000_0a/b000_0a): this rule holds the
  end-effector (foot/hand) world orientation constant to **≤0.03°** mean
  deviation over 686–1317 ticks, vs 91° (leg) / 12–62° (arm) for hold-at-bind.
  The ycg bind quats are authored so the distal hinge exactly counter-rotates —
  adopt rec3 = −(rec1+rec2) for all retarget posing.

## YANM track → joint mapping — MEASURED (2026-10-13 ~07:20 EDT; tools/yanm_track_joint_map.py, docs/yanm-track-joint-map.json)
- Track directory = 29 × 32B records at 0x50..0x3F0 (record: hash, a, keyoff,
  f32-triple, w24, w28). **All key streams verified at/after 0x3F0** (3 clips).
- Per-track frame counts (dt-sum ticks + seconds via header [0x3C]) tabulated
  for a000_0a (entrance), b000_0a, c000_0a; joined to ycg-group anatomy
  (docs/ycg-group-mapping.json). 21 tracks ↔ 21 ycg groups ↔ 70-bone ymg rig.
- Track hash sets DIFFER per clip (e.g. a033_0a.yag carries duals CD9642DA,
  1DD93523, FE9A7A50, CD9648DA, 0C5A75E5 — none in a000_0a) — the 29-track
  layout is per-clip, not global.
- Dual w24 field: nonzero ONLY on duals (0x390DD400 / 0x39237F80 / 0xB46BF500
  = f32 ≈ ±0.00018) — semantics open, candidate A-stream gain/bias.

## YOBJ (.ymg) structural decode v3 — MEASURED (2026-10-13 ~07:45 EDT; tools/yobj_batches.py)
- TODO (3) premise WITHDRAWN: **there is no GX display list in YOBJ**.
  Region @0x10D80 = saturated vertex payload (`DDDD…`/`ABBB…` runs), not
  commands. Byte scan of 000_0.ymg finds 292 GX-cmd-like bytes (0x90/0x98/0xA0
  + plausible u16 count) SCATTERED through the file — chance matches in vertex/
  texture data, no clustering, no DL.
- The real draw structure is the **16-byte batch table at header [0x5C]**
  (0x5AE0 in 000_0.ymg): **58 records** (000_0.ymg), fields
  (u32, u32, u8 type, u16 marker, u8 variant, u32 count); counts sum to 892.
  Two variants (v=1: marker=ffff; v=2: marker=XXff). Verified present in
  000_1.ymg (58 recs, same offset) and 009_2.ymg (variant u0 encoding).
  44 of 161 wrestler `.ymg` slots are real YOBJ (rest are `DUMY` placeholders).
- Per-field semantics (u0/u1/b8 exact meaning; count = tris vs indices;
  linkage to material table) OPEN — next step.

## YANM (.yag) structural decode v2 — MEASURED (sample: ringmotion/a000_0a.yag, 22,556 B)
- 56-byte header: "YANM" | u32 22500 (= size−56) | 0x011F0000 | u32 8 |
  0xCD89A39E | section offsets 0x3E8, 0x3EC, 0x3F4 | zeros | 0x00010001 |
  0x10B4F0 | (frame delta 0.02797 f32 noted in v1 — re-verify).
- Companion `.atr` ("DATA", 100 B here): header words, then 16-byte records
  from 0x20: (u32 type, u32 count, u32 tag_or_offset, u32 flags).
  Sample records: (2,10,0x340000BE,1), (2,10,0x34000172,0), (1,20,0x34000172,1),
  (1,20,"POF0",4). The 0x34xxxxxx values and "POF0" tag semantics are OPEN.
- Track→joint mapping and frame counts: OPEN (next step: parse section @0x3E8
  as the track table; 42 .ycg joints vs N tracks).

## Task-3: ycg-group → ymg-bone anatomical mapping — MEASURED (2026-10-12 ~22:30 CDT; tools: ycg_ymg_map.py, yanm_gait.py, docs/ycg-group-mapping.json)

### Method (four independent evidences, all measured)
1. **Segment ratios**: within-group joint distances vs ymg bone lengths
   (leg thigh:calf = 44.81:44.99 = 1.004; arm UA:forearm = 29.86:26.28 = 1.136).
2. **Gait analysis**: per-track hinge series (x-channel, asin unit) decoded from
   3 entrance clips (a000_0a, b000_0a, b001_0a); means/stds/ranges compared.
3. **Hinge-axis analysis**: ycg bind quats are clean basis rotations; rotating
   local axes into world frame shows which anatomical plane each hinge swings in.
4. **Kabsch chain fits**: ycg 3-chains vs ymg arm/leg chains (residuals/scales).
   (Global rigid ycg→ymg alignment FAILS — best mean err 52 units — so the
   anim rig's bind pose/proportions genuinely differ from the render rig;
   mapping is anatomical, not geometric.)

### The w0 field (DECODED)
ycg record word @+4 (`w0`) = **2·type + side_bit**: type 0 (w0 0/1), type 1
(w0 2/3), type 2/bilateral (w0 4/5). Mirror pairs always differ by exactly 1
(e.g. BD5B2A59=2 / BD5B5259=3); bilateral groups carry the same w0 on both
records (347D3654=4,4). ycg-Y-negative = "side A", ycg-Y-positive = "side B";
side A/B → anatomical R/L is PROVISIONAL (unresolved).

### Mapping table (confidence-graded; full JSON in docs/ycg-group-mapping.json)
| ycg group(s) | recs | Anatomy | Conf | Key evidence |
|---|---|---|---|---|
| BD5B2A59 / BD5B5259 | 3+3 | LEGS (hip→knee→ankle) | HIGH | seg ratio 0.991 = thigh:calf 1.004; dominant gait motion (range 153–163° all clips); L/R anti-phase; hinge→sagittal swing |
| 6198F425 / 6198F4D5 | 3+3 | ARMS (shoulder→elbow→wrist) | MED-HIGH | seg ratio 1.179 ≈ UA:FA 1.136 (closest); best arm Kabsch fit (resid 0.64); hinge→sagittal swing |
| 7AD45E02 / 64D45E02 | 3+3 | UNRESOLVED accessory chain | LOW | ratio 1.274 matches no limb well; quat family differs from BD/6198; hypotheses: 2nd arm segment chain / torso accessory |
| 6865B2C0 / 6865B2CF | 3+3 | UNRESOLVED accessory chain | LOW | ratio 1.216; 2nd-most-active in gait (std ≤10.6); paired with 7AD in position+quat |
| 613B7547 / 613B75B7 | 2+2 | UNRESOLVED torso 2-hinge | LOW | only vertical-in-z chain (0.49→11.25 @ x≈6.6); mirrored L/R (odd for spine) |
| 347D3654 | 2 | UNRESOLVED bilateral hinge | LOW | (3.40, ±5.38, −0.80) |
| 64DB300F | 2 | bilateral hinge, hip-abduction cand. | LOW-MED | widest y (±8.25); x/z near BD hip end; dual track |
| 7CC9B660 | 2 | UNRESOLVED bilateral hinge | LOW | (10.82, ±4.54, 2.96); dual track |
| 099CD766 | 1 | PELVIS/ROOT candidate | LOW-MED | centered (11.80,0,1.78); largest core motion (range 40°) |
| 095CD669 | 1 | static bent joint | LOW | centered; 1 static key = 79.89° fixed bend |
| 5B214D41 / 5B214D4E | 1+1 | head/neck candidate | LOW | (20.34, ∓0.13, 1.33); 4E range 70° in a000 |
| 60F8F527 / 60F8F5D7 | 1+1 | UNRESOLVED | LOW | (4.19, ±0.10, −1.2) |
| 637B7003 / 637B70F3 | 1+1 | UNRESOLVED | LOW | (7.07, ±0.32, 4.15); 7003 range 38° in a000 |

### Still OPEN after task-3
- 7AD/6865 identity (two extra mirrored 3-hinge chains beyond arms+legs).
- Per-record channel assignment: 5B key carries (x,y) two hinge series per
  track, but 3-record groups have 3 hinges — x used as primary (retarget v1).
- ycg-Y side → anatomical L/R.
- 8 unknown-hash static tracks (2nd performer / camera / prop?).

## TODO (updated)
- [x] Download ISO (verified MD5) — DONE 2026-10-12
- [x] Map file structure — DONE 2026-10-12
- [x] YOBJ/YANM/YCG structural probe v1 — DONE 2026-10-12
- [x] YOBJ v2: 70-bone skeleton fully decoded (names/parents/transforms) — DONE 2026-10-12
- [x] CAW part format identified (YOBJ parts, gender/body-part tree) — DONE 2026-10-12
- [x] YANM: track directory decoded v3 (29×32B records 0x50–0x3EF; 21/29 hashes =
  .ycg anim rig; key formats 5B/4B measured) — DONE 2026-10-12
- [x] YANM: channel→rotation mapping decoded (5B=(32767·sinα, dt, 32767·sinβ),
  dt=middle byte delta, [0x3C]=s/tick; 4B A=(value,dt) dt-sum=B; each ycg
  record = 1-DOF hinge, angle=asin(s16/32767)) — DONE 2026-10-12
- [x] ycg-group → ymg-bone anatomical mapping — DONE 2026-10-12 (BD=legs HIGH,
  6198=arms MED-HIGH, w0=2·type+side decoded, 7AD/6865 unresolved; table +
  docs/ycg-group-mapping.json)
- [ ] YOBJ v3: crack vertex position buffer + dequantization → export verified OBJ
- [ ] .atr record semantics (0x34xxxxxx offsets, POF0 tag)
- [ ] Document Revenge Mode arena designs (bg/ arena sets)
- [ ] No Mercy animation data isolation; recomp syms cross-ref (0x13E4A0 pointer table)
- [x] Retarget test: Yukes anim → Tekken 3 model — v1 DONE 2026-10-12
  (tools/yanm_to_tekken3.py: a000_0a entrance → King 49-channel pose seq,
  465f @30fps, FK joints pelvis/chest/hips/head/shoulders; verified numeric +
  plot; legs/IK = v2)
- [x] Compare Yukes vs AKI animation approach — DONE 2026-10-13
  (docs/YUKES-VS-AKI-ANIMATION.md)
- [x] .atr record semantics — DONE 2026-10-13 (event timeline, not duration;
  see "Cycle 2026-10-13 (a)–(f)" below)

## Cycle 2026-10-13 (a)–(f) — MEASURED

### (a) YOBJ batch-table per-field semantics → docs/YOBJ-BATCH-SEMANTICS.md
- 16B records at `[0x5C]` (58 for 000_0.ymg): (u0 off@0x80, u1, u8 b8,
  u16 marker, u8 variant, u32 count). **count = number of 4-byte payload
  units** (delta=count×4 on 40/58). Payload = (u16,0) pairs, coord-scale
  0–4096, strip-like repetition.
- Records 1–7 share u0=0x61C0; counts sum to 128 = rec0 count → rec0 is a
  group header. marker_hi = b8−1 (v=2, 51/52). b8 (0x03–0x46) is NOT bone
  (incoherent within groups) — likely material/part id.
- Payload NOT indices into any located pool (s16x3 pools at [0x80,0x6240)
  and [0x240,0x6240) both REJECTED); NOT (x,y) verts (2D plot = scribble).
  Exact payload semantics, u1, b8, material linkage: OPEN.
- Working assembly stays the 13 skin batches → 606 verts → 58 strips →
  383 tris (`tools/yobj_strips.py`).

### (b) .atr DATA decode — MEASURED (negative result)
- 167 `.atr` files. Structure: `"DATA"` magic, 32B header
  (record_count@0x0C, record_size=16@0x10, 0x34xxxxxx@0x18), then 16B
  records `(u32 type, u32 count, u32 tag, u32 flags)`; tag often
  `0x34000000|time` or `"POF0"`.
- 0x34xxxxxx = **event times in YANM dt ticks** (within tick range,
  incrementing; e.g. a000_0a: 157/190/370).
- The max event time does NOT equal the YANM max tick total (6 clips:
  370 vs 930, 425 vs 1147, 318 vs 911, 528 vs 1319, 1633 vs 1949,
  473 vs 1289). Ratios 1.2–2.9, not a clean unit.
- CONCLUSION: the `.atr` is an **event timeline**, not a duration record.
  No single authoritative clip-duration field exists in `.atr`; the
  animation duration is the YANM per-track max dt-sum (hold-last).

### (c) A-stream first-8B + w24 + f32-triple — MEASURED
- First-8B: two styles. Sparse (a.yag): `C13FC13F 00000000` magic-like,
  then real keys at +8 (`(0,0,118)`=HOLD, `(32258,251,2)`=ANGLE).
  Dense (a000_0a): `C24006C2 40C24002` (2 key-like structs). ca=1 duals
  have a bare 4B key, no header room. Interpretation OPEN (header vs keys).
- w24: nonzero ONLY on duals; always tiny (0–0.00016 as f32). Not a gain
  (would be negligible vs s16 B). Semantics OPEN.
- f32-triple: nonzero ⟺ non-degenerate dual; 0C5BF279 (ca=1) = (0,0,0).
  Values vary per clip (e.g. 7CC9B660: (0.003,0.002,0.010),
  (0.002,−0.003,−0.269), (0.006,−0.027,−0.910)). Semantics OPEN.

### (d) 8 unknown track identities — MEASURED (still open, narrowed)
- 0/175 `.ycg` files (154 wrestler + 21 bg/viewer/COL). Present in ALL
  `.yag` (ringmotion + viewer/motion, same 29-track layout).
- 7/8 static (n=1) in most clips; **A4955E6E animates (n=10, 30°/58°)
  in c000_0a**. L/R-paired values: 579B8E50≡579B89D0=(0°,79.9°);
  007FD58C≈1E7FD58C=(44.1°,∓44°).
- Static 80°/44° bends + pairing → finger/facial subset or simplified
  2nd-performer rig are leading hypotheses. Identity OPEN.

### (e) CAW edit_data layout → docs/CAW-EDIT-DATA-WMXIX.md
- `edit_data/MODEL/{Man,Woman}/{10 categories}/{style}_{variant}/{l0,r0}.ymg`
  (1,213 files); style counts per category measured; `edit_data/TEX`
  (1,469); `edit_data/COL` (8 `.ycg`).
- Save-record byte layout still **blocked** on a real `.gci` memory-card
  dump (precise input spec in the doc).

### (f) Yukes-vs-AKI animation comparison → docs/YUKES-VS-AKI-ANIMATION.md
- Frames (AKI: 25 joints × 98 B, s8 degrees) vs tracks (Yukes: 29 streams,
  s16 sin-encoding, 1-DOF hinges, dual common-mode factorization).
