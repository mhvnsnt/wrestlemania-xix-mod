# YANM Item-3 / Item-4 Cycle Results — 0C5BF279 detail table, 40911198 correction, base-ID pairing
Measured 2026-10-13 (watchdog continuation cycle). Streamed from ISO
(`WWE Wrestlemania XIX (USA).iso`); probes: `tools/yanm_item3_probe.py`,
`tools/yanm_baseid.py`. This doc supersedes the item-3/4 sections of
`YANM-ITEM5-CYCLE.md` (which are updated to point here).

## Item 3 — 0C5BF279 ymg detail table: 15 self-pointer part records

Each wrestler `.ymg` (000_0-format; 000_0, 047_0 verified; 002_0/016_0/045_x
carry the same track+block at different offsets, see below) contains a table
of **15 self-pointer records** — record headers are `u32 == own file offset`
at `0x10850, 0x108ac, 0x10908, ...` (stride 0x5C mostly), each followed by a
`00000000` word.

Record structure (verified on all 15 records of `000_0.ymg`):
- `w0` = self pointer (own offset), `w1` = 0, then **5-word entries**:
  `[0F0A080F, 04070707, 005004XX, w4, hashslot]`
- The last byte of `005004XX` = **part index 0–12** (record n has XX = n;
  verified records 0–14 → XX 0x00–0x0C). Parts 0–11 carry `E4E4E4E4` in the
  hash slot (no track).
- **ONLY the last record (part 12, @0x10d30)** carries a track in the hash
  slot: `0C5BF279`, followed by a **12-word ID block** (CORRECTED — the
  earlier "9 param words" claim was wrong):

```
0018796D 5D98B7F1 0D187764 1D3CF9CD
001B32E7 ECB96CB2 ECB96CAC 2DFBFA75
0CD871E5 9493F6CE 00197CE5 4B2CA0FE
```

- Records 9/11/13 are short/variant (33, 13, 13 words) but keep the same
  entry prefix; record 14 is 66 words (entries + ID block + byte-ramp
  curves `44/42/45/57` — likely remap curves, semantics open).
- Non-track records also carry per-entry 5th words `00000032` / `00009003`
  / `00010000` / `00030000` / `00050000` (variant flags; open).

### ID block is per-MODEL-group, not per-track

`0C5BF279` is the same track in 201/215 yag clips, but the ID block after it
in the ymg is **per wrestler model group** (measured):

| wrestlers | track offset | ID12 block |
|---|---|---|
| 000_0, 002_0, 047_0 | 0x10d4c / 0x1302c | `0018796D 5D98B7F1 0D187764 1D3CF9CD 001B32E7 ECB96CB2 ECB96CAC 2DFBFA75 0CD871E5 9493F6CE 00197CE5 4B2CA0FE` (identical) |
| 016_0 | 0x11a44 | permuted variant, shares `5D98B7F1`: `0D187764 1D3CF9CD 0018796D CCB9EFEA CCB9EFF4 001B32E7 0CDBF7F4 5D98B7F1 6C38F2B7 0CBE72B1 96507F14 49FB677B` |
| 045_0, 045_1 | 0x12d44 / 0x129e4 | shares `5D98B7F1` + **consecutive run** `DDF67B76–7F` (+ `DDF67BFE`): `5D98B7F1 DDF67B7E DDF67B7F DDF67B7C DDF67B7D DDF67B7A DDF67B7B DDF67B78 DDF67B79 DDF67B76 DDF67B77 DDF67BFE` |

- `5D98B7F1` appears in all three variants → likely a shared element/attire ID.
- The `045` consecutive run `DDF67B76–7F` looks like a sequential ID allocation
  — the ONE place IDs look sequential (contrast: yag track base IDs are not).

### ID-block semantics: OPEN (measured negatives)

Ruled out (0 hits each): yag track hashes, ycg hashes, bone-table words,
file offsets, bone-name hashes. Leading hypothesis: **driven-element IDs in
mesh ID space** (the table binds a per-wrestler detail part to a static
dual track + its driven mesh elements).

## Item 3 — 40911198: CORRECTED, NOT a track

- `0x40911198` appears in **0/215 yag clips** → it is not a YANM track hash.
- In `001_0.ymg` at offset `0x10d4c` (coincident with 000_0's track-table
  offset) the bytes `40 91 11 98` sit in the **bone-name table** next to the
  `"Bip R Finger4"` string, among other floats (`411B1097`, `3F000000`…).
- As big-endian f32 = **4.533397674560547** (a per-bone parameter float —
  likely a scale/bias for that finger bone). No clip role, no track role.
- The prior "analogous slot" claim was wrong: `001_0.ymg` has NO self-pointer
  record table in the 000_0 format (0 self-pointer headers found), so there
  was no "slot" — the file-offset coincidence misled the reading.

## Item 4 — base-ID exact-XOR pairing

Method: over the track-hash universe, pair hashes whose exact XOR is one of
the known small side codes `{0x0F, 0xF0, 0x780, 0x7800, 0x1E000000, 0xA0,
0xA00}` (greedy, smallest-a first). Reproducible via `tools/yanm_baseid.py`.

### ringmotion universe (45 hashes): 13 pairs + 19 singles

| pair (a, b) | XOR (side code) | root (a XOR code) |
|---|---|---|
| 007FD58C / 1E7FD58C | 0x1E000000 (toes) | 007FD58C |
| 64D45E02 / 7AD45E02 | 0x1E000000 | 60D45E02 |
| A4955E6E / BA955E6E | 0x1E000000 (fingers) | A0955E6E |
| 5B214D41 / 5B214D4E | 0x0F | 5B214D40 |
| 6865B2C0 / 6865B2CF | 0x0F | 6865B2C0 |
| 60F8F527 / 60F8F5D7 | 0xF0 | 60F8F507 |
| 613B7547 / 613B75B7 | 0xF0 | 613B7507 |
| 6198F425 / 6198F4D5 | 0xF0 | 6198F405 |
| 637B7003 / 637B70F3 | 0xF0 | 637B7003 |
| 579B89D0 / 579B8E50 | 0x780 (thumbs) | 579B8850 |
| BD5B2A59 / BD5B5259 | 0x7800 (LEG) | BD5B0259 |
| CD9642DA / CD9648DA | 0xA00 (per-clip dual) | CD9640DA |
| FE9A7A50 / FE9A7AF0 | 0xA0 (per-clip dual) | FE9A7A50 |

Side-code census: `0xF0` ×4, `0x1E000000` ×3, `0x0F` ×2, `0x780`/`0x7800`/
`0xA00`/`0xA0` ×1 each. (An earlier cycle note said "18 singles"; the
verified count here is 19 — one-count discrepancy, this run is authoritative.)

Singles (no small-XOR partner): 0010B4F0, 095CD669, 099CD766, 0C5A75E5,
0C5BF279, 1DD93523, 347D3654, 64DB300F, 7CC9B660, CD89A39E, ECD28978, +
7 slot-entities below.

### full 215-clip universe (97 hashes): 16 pairs + 65 singles

Adds 3 pairs vs the ringmotion subset: `0946CF9A/1746CF9A` and
`6746AF9A/7946AF9A` (both XOR `0x1E000000` — more high-byte-side pairs),
`FDB87F60/FDB87F90` (XOR `0xF0`). Side-code set is unchanged (no new codes).

### per-clip entities = (slot<<8)|0x02

Literal small IDs in the universe with low byte `0x02`: slots **129**
(0x81), **146** (0x92), **147** (0x93), **157** (0x9D), **158** (0x9E),
**212** (0xD4), **213** (0xD5) — each appears in 1 clip only. Second
performer / referee / prop candidates. (Note: `64D45E02`/`7AD45E02` also
end in 0x02 but are 1E000000-paired joint tracks, not slot entities.)

### family deltas in base IDs

Related joints share base-ID XOR deltas across side-pairs:
- `60F8F507 ^ 6198F405 = 0x01600102` (and their pair-mates likewise)
- `613B7507 ^ 637B7003 = 0x02400544` (and their pair-mates likewise)
The ID table has joint-family structure — but the **generation function
is OPEN**:
- Base IDs are NOT sequential: sorted roots have random gaps
  (`00009002 → 00009C02 → 0010B4F0 → 007FD58C → 095CD669 …`).
- Base IDs are NOT shifted-index: side-code bits land at scattered bit
  positions (`0x0F` low nibble vs `0x1E000000` high byte vs `0x780` bits
  7–10) — a clean index<<shift would put side bits in one place. Bit-spread
  proof: no single shift maps roots to small integers.
- Root battery (additive/poly/XOR-fold hashes × ~200 name variants:
  bone names, Finger/Thumb/Toe spellings, case/space/Bip-stripped,
  ascii+utf16le): **0 hits**. Combined with the prior 26-function battery:
  0 hits total. IDs are assigned, not derived from strings by any tested fn.

## STOPPED HERE (next cycle)
1. Anatomical L/R of finger/thumb/toe tracks — rendered mesh + FK visual
   (provisional mapping in YANM-ITEM5-CYCLE.md (a), LOW confidence).
2. ECD28978 identity — 82-pose static selector, max |r|=0.27 vs core;
   needs face-bone/mesh correlation or visual.
3. ID-block semantics (ruled-out list above; leading hypothesis mesh ID
   space) + byte-ramp curves after the ID block.
4. Base-ID generation function — family deltas measured, assignment
   algorithm open; the 045 consecutive run `DDF67B76–7F` may be a clue.
5. CAW `.gci` — blocked headless (needs parent Dolphin task with KNOWN
   CAW values). Out of scope for this lane.
