# YANM (.yag) Format Specification — MEASURED

WWE WrestleMania XIX (GameCube, Yukes). All fields big-endian. Verified against
170 `ringmotion/*.yag` files, streaming from ISO (tools read ISO byte ranges;
no extraction). Sample: `ringmotion/a000_0a.yag` (22,556 B).

## Header (56 bytes)

| offset | type | value / meaning |
|---|---|---|
| 0x00 | char[4] | `YANM` magic |
| 0x04 | u32 | payload size = file size − 56 |
| 0x08 | u32 | `0x011F0000` (constant) |
| 0x0C | u32 | `0x08` (constant) |
| 0x10 | u32 | `0xCD89A39E` (magic constant) |
| 0x30 | u32 | `0x0010B4F0` (constant across files; semantics open) |
| 0x3C | f32 | **seconds per dt tick** (e.g. 0.0279688; clip seconds = tick_total × this). NOTE: 0.0 in `ringmotion/a.yag` — not always valid |
| 0x40–0x48 | f32 ×3 | anim params (0.5146 / 1.887 / −0.2931 on sample; TBD — root-motion/blend candidates) |

## Track directory: 29 × 32-byte records at 0x50..0x3F0

Record layout:

| offset | type | meaning |
|---|---|---|
| +0 | u32 | joint hash (matches `.ycg` group hash for 21/29 tracks) |
| +4 | u32 | A-stream offset (0 = single track) |
| +8 | u32 | B/key-stream offset |
| +12..+20 | f32 ×3 | nonzero ⟺ dual track (singles are exactly (0,0,0)); semantics open |
| +24 | u32 | nonzero ONLY on duals (≈ ±0.00018 as f32); semantics open (A gain/bias candidate) |
| +28 | u32 | single: key count; dual: (ca << 16) \| cb |

Terminator: all-zero record at 0x3F0. **All key streams live at/after 0x3F0**
(verified 3 clips). Track hash sets DIFFER per clip (not a global table).

## Key formats

**Single track — 5-byte keys** `(s16 ch1, u8 dt, s16 ch2)`:
- dt is the MIDDLE byte and is a DELTA (non-monotonic, 0–255).
- Channel encoding: **ch = 32767 · sin(hinge angle)** → angle = asin(s16/32767).
  Saturates at ±32767 (±90°). NOT atan2-angle, NOT direct-s16-angle (proven by
  circularity test on BD5B5259 and small-angle smoothness on 099CD766).

**Dual track — A: 4-byte keys `(s16 value, u8 flags, u8 dt)`, B: 5-byte keys.**
- A stream = ca × 4 bytes, byte-contiguous (region-length proof; no separate
  header region). First 8 bytes ambiguous: C13F-magic style on sparse tracks
  vs 2 decodable keys on dense tracks — interpretation open, layout fixed.
- A = bilateral COMMON-MODE hinge angle (same asin encoding, to ±80°);
  **rec_i(t) = A(t) + B_i(t)** on the group's hinge axis; B = per-side trims.
  r²(A ~ B) ≈ 0.00–0.05 (independent component). Duals exist ONLY for the
  symmetric-motion 2-record groups (7CC9B660, 64DB300F, 0C5BF279 + per-clip
  variants like CD9642DA/1DD93523/FE9A7A50/CD9648DA/0C5A75E5).
- A key pattern (sparse/C13F style): (0, 0, dt=47–255) = HOLD; (≈±32000,
  flags≠0, dt=2) = ANGLE. Dense style: dt=2 constant.
- dt-sum(A) ≈ dt-sum(B) is NOT general (518-duals recheck: 212/27/279
  header/no-header/neither). A may end early; player holds last A value.
- Degenerate dual (ca=1, cb=1): 1 bare 4B A-key + 1 5B B-key, static.

## Track → joint mapping

- 21 tracks ↔ 21 `.ycg` joint-groups 1:1 (hash match). `.ycg` = 42 records =
  8 singles + 5 L/R pairs + 8 3-chains; each record is a 1-DOF hinge.
- Each 5B channel drives one hinge: pairs ch1→L / ch2→R; 3-chains ch1→rec1
  (hip/shoulder), ch2→rec2 (knee/elbow); **rec3 = −(rec1+rec2)** (measured:
  holds foot/hand world orientation to ≤0.03° over 686–1317 ticks).
- Hinge axis is uniform within a group: local X (13 groups: limbs/torso/pelvis),
  local Z (6: head/neck + accessory chains), local Y (2: 60F8 group).
- 8 track hashes appear in NO wrestler `.ycg` (0/154 files): 007FD58C,
  0C5BF279, 1E7FD58C, 579B89D0, 579B8E50, A4955E6E, BA955E6E, ECD28978.
  Not always static; values look L/R-paired. Identity open (2nd performer /
  camera / prop / referee candidates).
- Per-track durations vary up to 2× within a clip (authoring variance via
  large-dt hold keys); retarget handling: hold-last + clip.

## Tools

- `tools/yanm_track_joint_map.py` → `docs/yanm-track-joint-map.json` (29-track
  table × 3 clips: hashes, kinds, key counts, tick totals, seconds, anatomy)
- `tools/yanm_task2_finish.py`, `tools/yanm_task2b.py` → `docs/yanm-task2-finish.json`
  (dual-A semantics, chain assignment, hinge axes)
- `tools/yanm_rec3_rule.py` → `docs/yanm-rec3-rule.json` (rec3 rule proof)
- `tools/yanm_census.py`, `tools/yanm_track_probe.py`, `tools/yanm_keyseg.py`,
  `tools/yanm_semantics.py`, `tools/yanm_unitfit.py`, `tools/yanm_gait.py`,
  `tools/yanm_hashscan.py` (probes)
- Retarget: `tools/yanm_to_tekken3_v2.py` (+ `docs/YANM-TEKKEN3-RETARGET.md`)

## Open

- Directory f32-triple semantics; w24 semantics; header [0x30]/[0x40–0x48].
- First-8-bytes of A stream (header vs 2 keys).
- 8 unknown track identities. Authoritative clip duration (`.atr` lead).
- Per-clip hash-set → move-category mapping (a/b/c/d letter groups).
