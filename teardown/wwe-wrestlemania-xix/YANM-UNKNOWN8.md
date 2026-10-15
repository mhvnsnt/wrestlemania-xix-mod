# YANM 8 Unknown Track Hashes — IDENTIFIED (measured 2026-10-13)

All 170 `ringmotion/*.yag` clips decoded (streamed from ISO). The 8 track hashes
absent from every `.ycg` (0/175 files, re-verified) are **hand/foot detail
joints — fingers and toes**. The `.ycg` holds only the 21 body-core groups;
the 8 detail tracks drive the ymg's finger/toe bones directly (no ycg records).

## The 8 unknowns (4 pairs)

| track(s) | hash pair | verdict | evidence |
|---|---|---|---|
| 10 / 16 | A4955E6E / BA955E6E | **FINGERS (strong)** | animates in 19/15 clips, 28 of 29 are `c*` (grapple) clips; grip→release motion (start curled −30°/57.5°, release to ~0°); 120–131 distinct static poses across clips; pair hashes share suffix `955E6E` |
| 22 / 27 | 1E7FD58C / 007FD58C | **TOES (moderate)** | positional: distal to leg runs C/D (after LEG/ARM/torso chains); 30 distinct static poses per clip (0°, 44° bends); never animated within a clip (0/170) — toes are posed per-move, not keyframed |
| 11 / 17 | 579B8E50 / 579B89D0 | hand detail, likely thumb/spread (weak) | most distal in arm runs A/B; static (0°, 80°) in 153–154/170 clips, 5 rare variants — a default-pose joint, occasionally overridden |
| 5 / 28 | ECD28978 / 0C5BF279 | unclear (weak) | center block; ECD28978 takes 82 distinct static poses; 0C5BF279 is dual and appears once per wrestler `.ymg` in a per-wrestler binary table (value varies: 0C5BF279 in 000_0, 40911198 in 001_0) |

## Key measurements

- **Grip-release signature** (`c000_0a`, track 10): t=0 (−30°, 57.5°) held 250
  ticks → release to (0.2°, 0°) → tiny re-curl at t=364. Exactly a grapple grip.
- **Letter distribution** of animated finger clips: `c`=28, `a`=1, `b`/`d`=0.
  Finger animation is a grapple-clip phenomenon.
- **Static-pose counts** (rounded 1°, 170 clips): A4955E6E 120, BA955E6E 131,
  007FD58C/1E7FD58C 30/30, ECD28978 82, 579B pair 5 (dominated by (0°,80°)).
- **Pair coupling**: 579B pair members identical in 146/168 clips; finger/toe
  pairs rarely identical (independent L/R posing).
- **ycg record structure** (bonus discovery): 42 records × 56 B =
  `[u32 track_hash][u32 group_idx 0–5][u32 0][u32 0][f32×3 pos][f32×4 quat][f32 len][u32 0][u32 0]`.
  group_idx maps records to yag track runs (0=run B, 1=run A, 2=run D, 3=run C,
  4/5=center). Each record's hash IS its yag track hash (3 records/hash for
  3-chains, 2 for L/R duals, 1 for singles).

## Hash function: NOT FOUND (negative result, documented)

- Battery: 26 functions (crc32, crc32-bzip2, fnv1/1a-32/64, djb2, djb2a, sdbm,
  lose-lose, elf, jenkins, dek, bp, ap, js, rs, bkdr31/131, murmur2/3 (3 seeds),
  xxh32, adler32) × 70 ymg bone names × ~40 name variants (case, `_`/space,
  `Bip`-strip, side prefix/suffix moves, null-term) × 2 encodings (ascii,
  utf-16-le) = **0 hits** on all 29 track hashes.
- Pair-XOR structure (lead for future): pair members differ by XOR of a few
  contiguous bits — 0x0F (×2 pairs), 0xF0 (×4), 0x0780, 0x7800, 0x1E000000 (×2),
  0x1E800000. Suggests `hash = H(root) XOR side_code` or index-derived IDs,
  NOT a plain string hash (which would avalanche).
- 001_0.ymg has a 77-entry string table (70 bone names + textures) in the tail;
  000_0.ymg has binary data instead (per-wrestler format difference). Neither
  contains track hashes (full-tail scan: 0 hits).

## Tools

- `tools/yanm_unknown8.py` — animation census + neighbor correlation over 170 clips
- `tools/yanm_hash_battery.py` — 26-function hash battery (0 hits, documented)

## Open

- Exact finger articulation split (track 10 vs 16: curl vs spread? proximal vs
  distal?) — needs a clip with isolated finger motion.
- 579B (0°, 80°) default: which hand joint rests at 80°? Candidate: thumb.
- ECD28978/0C5BF279 identity; 0C5BF279's ymg table role.
- Hash construction (pair-XOR lead).
