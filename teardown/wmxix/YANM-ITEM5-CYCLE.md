# YANM Item-5 Cycle Results — fingers / thumbs / ECD / 0C5B / hash construction
Measured 2026-10-13 (watchdog continuation cycle). All streamed from ISO; tools:
`tools/yanm_item5_cycle.py`, `tools/yanm_item5b_cycle.py`.

## (a) Finger articulation split — RESOLVED (relative sides)

- `A4955E6E` / `BA955E6E` (dir idx 10 / 16) are an **L/R pair** (XOR `0x1E000000`,
  co-occur 168/168 clips). Each is one hand's finger track.
- Each track is a single 5B-key track with **two INDEPENDENT finger DOF**
  (ch1/ch2). Decoupled clips prove independence:
  - `c100_0a` `A4955E6E`: ch1 alone 0.2°→58.4°, ch2 static ~0°
  - `c007_0a`, `c124_0a` `A4955E6E`: ch2 alone 0°→−72.4°, ch1 static ~0°
  - `c128_0a`, `c220_0a` `BA955E6E`: ch2 small motion −4.8°→0.4°, ch1 static
- "Curl vs spread" REJECTED: 72° range far exceeds anatomical finger spread;
  spread would be small and symmetric. Verdict: **ch1 = proximal-curl
  (MCP/knuckle), ch2 = distal-curl (PIP+DIP), opposite sign conventions**
  (MEDIUM confidence — signs differ because distal segments sit in a mirrored
  local frame; both relax to ~0° on release).
- Asymmetric hand roles in grapples (`c000_0a`): `A4955E6E` does a full
  grip→release (−30.0°/57.5° held 250 ticks → 0.2°/0.0°, release onset ch1@250
  ch2@250, simultaneous) while `BA955E6E` holds a static curled pose
  (47.9°/39.3°) the whole clip — one hand releases, the other maintains grip.
- Detail tracks are **per-move POSES**: w28 (key count) = 1 (static) for all
  detail tracks except when animating (`A4955E6E` w28=10 here doing the release).
- Anatomical L/R: PROVISIONAL (LOW confidence). `A4955E6E` has the smaller
  side-code value (`0x04000000` < `0x1A000000`); by the ycg convention
  (side_bit 0 = ycg y<0; ymg anatomical R = +y) → `A4955E6E` = LEFT hand,
  `BA955E6E` = RIGHT hand. **Needs visual verification once YOBJ full model
  assembly lands** — the ycg bind frame's axis alignment to ymg space is
  unproven (bind quats are 120° axis-permuting rotations).

## (b) 579B = THUMBS — STRONG

- `579B89D0` / `579B8E50` (dir idx 17 / 11) are an L/R pair (XOR `0x780`).
- Default pose (0.0°, 79.9°) in 128/128 non-grapple clips and most grapple
  clips: **thumb rest = abducted ~80°** (anatomically correct for a thumb).
- In grapple clips the thumb co-poses with the SAME-SIDE finger track:
  - (79.9°, 0.0°): thumb wrapped into the grip (curl 80°, adducted)
  - (0.9°, 0.2°) ≈ (0°, 0°): thumb pressed flat/adducted
- Side pairing PROVEN by contingency over all 170 clips:

| finger track | thumb track | finger static → thumb non-default | finger anim → thumb non-default |
|---|---|---|---|
| A4955E6E | 579B8E50 (same side) | 0/149 | 15/19 |
| BA955E6E | 579B89D0 (same side) | 0/154 | 14/15 |
| A4955E6E | 579B89D0 (cross) | 9/149 | 5/19 |
| BA955E6E | 579B8E50 (cross) | 10/153 | 5/15 |

  Same-side: thumb NEVER leaves default unless its finger track animates
  (0/149, 0/154 — perfect). Cross-side: no association. **(A4955E6E, 579B8E50)
  = one hand; (BA955E6E, 579B89D0) = the other.**
- Never animated WITHIN a clip (posed per move) — consistent with thumbs being
  posed, not keyframed.
- Coverage: finger track (ch1/ch2 = 4-finger proximal/distal curl) + thumb
  track (ch1 = thumb curl, ch2 = thumb abduction) drives all 15 finger bones
  per hand (Finger0/01/02 = thumb, Finger1-4 + segments).

## (c) ECD28978 / 0C5BF279

**0C5BF279 = per-wrestler detail track** (dir idx 28, DEGENERATE dual
ca=1/cb=1, static per clip):
- Appears exactly ONCE per wrestler `.ymg`, in a binary table:
  `000_0.ymg @0x10d4c`, `002_0.ymg @0x1302c`, always followed by the same
  9 words: `0018796D 5D98B7F1 0D187764 1D3CF9CD 001B32E7 ECB96CB2 ECB96CAC
  2DFBFA75 0CD871E5` (track params — identical across wrestlers sharing the
  hash, so params belong to the track, not the wrestler).
- `001_0.ymg` has `40911198` in the analogous slot (different table layout —
  string table at that offset instead). `40911198` is NOT a yag track in any
  ringmotion clip → that wrestler's detail track is unused here (or lives in
  entrance/victory clips).
- No other yag-track hash occurs in the table region → single-slot table,
  not a general part→track map. Likely a wrestler-specific detail piece
  (attire/hair/accessory) with its own (static) dual track.

**ECD28978 = 8th detail track, identity OPEN** (dir idx 5, center block,
single, w28=1 static per clip):
- 82 distinct static poses across clips; NEVER animated within a clip (0/170).
- Static values cluster at discrete (0/80°-grid) poses: (0,0), (0,80),
  (80,0), (80,4), (1,1), (2,1) — a POSE SELECTOR, not a continuous joint.
- Max |correlation| with any core track's static pose = 0.27 (6865B2CF) —
  fully independent of body motion.
- No small-XOR partner in the 45-hash universe; not in any `.ycg` (0/175);
  not in the ymg table.
- Hypotheses (all LOW): facial-expression selector (effort faces per move —
  fits the static-per-move + 80° extremes + independence); second-performer
  detail; prop. Needs mesh/FK or visual to resolve.

## (d) Hash construction — ID scheme, not string hashes

- 45 distinct track hashes across 170 clips. Pair-XOR census (popcount ≤ 6):
  side codes are **XORed per joint type**: `0x0F` (×2), `0xF0` (×4),
  `0x780` (×1, thumbs), `0x7800` (×1, LEG), `0x1E000000` (×3: fingers, toes,
  64D45E02/7AD45E02), `0xA0` (×1, per-clip dual), `0xA00` (×1, per-clip dual).
- `track_id = joint_base_id XOR side_code`. Base IDs are ASSIGNED, not hashed:
  - `00008102, 00009202, 00009302, 00009D02, 00009E02, 0000D402, 0000D502`
    are literal small IDs (`(index<<8)|0x02`) appearing in 1 clip each
    (per-clip entities — second performer/referee/prop candidates).
  - Root battery (side bits cleared): linear/additive/poly/XOR-fold hashes ×
    ~200 name variants (bone names, Finger/Thumb/Toe spellings, case/space/
    Bip-stripped, ascii+utf16le) = **0 hits** on 174 target roots.
    Combined with the prior 26-function battery: 0 hits total.
- Joint-family structure in base IDs: `60F8F527 ^ 6198F425 = 0x1600102`
  (and same for their pair-mates `60F8F5D7 ^ 6198F4D5`); `613B7547 ^
  637B7003 = 0x2400544` (and pair-mates). Related joints share base-ID
  deltas — the ID table has family structure. Full decode open.
- ECD28978 and 0C5BF279 have NO small-XOR partners → not L/R pairs
  (consistent with (c): per-wrestler/detail singles).

## STOPPED HERE (next cycle)
1. Anatomical L/R of finger/thumb/toe tracks — needs rendered mesh + FK
   visual check (YOBJ full model assembly still open).
2. ECD28978 identity — needs face-bone/mesh correlation or visual.
3. 0C5BF279's 9 param words semantics; 001_0's 40911198 track (find which
   clips, if any, use it — check entrance/victory clip dirs).
4. Joint base-ID table decode (family deltas 0x1600102, 0x2400544).
5. CAW `.gci` — still blocked headless (needs parent Dolphin task with KNOWN
   CAW values).
