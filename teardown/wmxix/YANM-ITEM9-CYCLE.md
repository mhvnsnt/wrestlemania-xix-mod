# YANM Item-9 Cycle Results — ID-block routing, Type-B X/Y/Z, base-ID generation

Measured 2026-10-14 (watchdog continuation cycle). Probes:
`tools/yanm_idblock_routing.py`, `tools/yanm_baseid_hier.py`.
ymg files re-extracted via range-ISO into `.scratch/files/` (git-ignored).

## Item (b) — ID-block → POF0 segment routing: NO deterministic routing

### Data (6 wrestler ymgs)

| wrestler | ID block (12 words) | POF0 | notes |
|---|---|---|---|
| 000_0 | 0018796D…4B2CA0FE | 168B, 12×14B segs | reference |
| 047_0 | identical to 000_0 | identical | **byte-identical file** (MD5 5ef43f92…; duplicate slot) |
| 002_0 | identical to 000_0 | 268B, segs 0,1,9,10,11 differ | same rig, different body |
| 045_0 | 13+ words (5D98B7F1 + DDF67Bxx run) | 264B, different segmentation | different rig |
| 016_0 | permuted 12 words (5 shared with 000) | 172B, 12 segs | shared/permured rig |
| 001_0 | **none** | **none** | no detail system at all |

### Key results

1. **ID block is rig-shared, NOT a routing key.** 000/047/002 share the
   identical 12-word block (same rig). 047_0 == 000_0 byte-identical, so
   "shared block + shared region" is trivial.
2. **POF0 is per-wrestler-body, NOT a function of the ID block.**
   002_0 shares 000_0's ID block exactly, but segs 0,1,9,10,11 differ
   (byte patterns completely different — different marker positions,
   e.g. seg0 000:`…4196a4444444` vs 002:`…4149424197`). **Deterministic
   word→segment routing: REJECTED.**
3. **Positional correspondence (seg k ↔ word k): PLAUSIBLE but UNPROVEN.**
   Counts match (12↔12; 045's longer block ↔ longer region). Confounded by
   body differences; no same-body/different-order case exists. The 045
   duplicate-ID test was invalid (no duplicates; 264B not 14B-segmented).
4. **Flat-0x44 is per-wrestler, not per-ID.** Shared IDs differ in flatness:
   0018796D active in 000 (seg0) but flat in 016 (seg2); 0D187764 flat in
   000 (seg2) but active in 016 (seg0); 5D98B7F1 flat in 000 (seg1) but
   active in 016 (seg7). (1D3CF9CD and 001B32E7 flat in both — 2/5.)
5. **Remap-LUT hypothesis: REFINED.** 14B segments cannot be 256-entry LUTs.
   They are quantized 14B curves (values 0x41–0x61 + ≥0x80 markers, e.g.
   seg0:`41 42 42 42 45 41 46 42 41 96 a4 44 44 44`). If LUTs, they are
   14-entry/control-point curves, not full tables. "Flat 0x44 = identity/
   no-op" remains plausible but is wrestler-dependent.
6. **045_0 structural difference confirmed.** 264B POF0 (66 words,
   0x44-dominated byte curves, 29 distinct bytes) with a 13+-word ID list
   (5D98B7F1 + DDF67B76–7F run + repeats DDF67BFE×4, 001D72B1×4 before POF0).
   Different rig → different detail structure (not 14B-segmented).

**Verdict:** The ID block names the rig's detail elements (shared by
wrestlers on the same rig); the POF0 holds per-body correction curves.
There is no ID→segment routing function to find — the mapping (if positional)
is 1:1 by order, and the curve content is body-specific. 001_0 lacking the
system entirely suggests it's optional per-wrestler detail.

## Item (c) — Type-B X/Y/Z vs ymg bind pose: REJECTED

0C5BF279 X/Y/Z (asin-decoded) for c200 variants:
- c200_0a: (−35.0, +25.4, −35.0)
- c200_1a: (−34.6, +25.4, +25.4)
- c200_2a: (+25.2, 0.0, −36.2)

(Varies per clip+variant ✓; quantized presets ~{0, ±25, ±35} ✓.)

Compared against:
- **ymg 70 bone bind eulers** (`docs/wrestler-skeleton-000.json`): all clean
  (0/±90/180; e.g. Pelvis (90,180,90), Head (0,0,0)). **0/70 match within 6°.**
- **ycg 42 record bind quats** → eulers: all clean (±90/180).
  **0/42 match within 8°.**

**Verdict: REJECTED.** The Type-B static orientation is NOT any model's bind
orientation. It is a variant-specific preset (quantized {0, ±25, ±35})
applied to the detail system — likely a per-variant base orientation for the
12 ID-block elements, modified by the POF0 curves. (Which element(s) it
drives is still open; the 12 elements' own binds are unknown.)

## Item (d) — base-ID generation fn: RESOLVED (tool-assigned hierarchical namespace)

### Decisive test: XOR popcount vs random

If base IDs were hashes/random, pairwise XOR popcounts of low16 fields
would average ~8 (Binomial(16, 0.5)). Measured per family:

| family | n | low16 range | XOR popcount (min/max/mean) |
|---|---|---|---|
| 0100 | 6 | 0x0000–0x0036 | 1 / 5 / 2.9 |
| 5D9B | 7 | 0x194F–0x1BC6 | 1 / 6 / 3.3 |
| 7AAF | 4 | 0xEC11–0xEE9B | 1 / 5 / 3.3 |
| F7AB | 5 | 0x5CAA–0x5FAF | 1 / 4 / 3.0 |
| C6F1 | 3 | 0x4E55–0xCFDF | 3 / 5 / 4.0 |

**All means 2.9–4.0, far below 8. Random/hash: REJECTED.**
The IDs are structured tool assignments, not hashes.

### Side-field consistency (16 pairs measured)

Each family's pairs use ONE consistent XOR code (side-field bits fixed
per family):
- 0xF0 (bits 4–7): 60F8, 613B, 6198, 637B, FDB8
- 0x1E000000 (bits 25–28): 007F, 0946, 64D4, 6746, A495 (fingers!)
- 0x0F (bits 0–3): 5B21, 6865
- 0x780 (bits 7–10): 579B (thumbs)
- 0x7800 (bits 11–14): BD5B (legs)
- 0xA0 (bits 5,7): FE9A; 0xA00 (bits 9,11): CD96

The side field lives at **family-specific bit positions** (not global).

### Packed-field example (4AAF)

`4AAF3560/3563/3660/3663/36E0/36E3/3760/37E0/37E3` =
family `4AAF` | group {5,6,7} | sub {6,E} | variant {0,3}
(3×2×2 of 12 possible). Textbook hierarchical namespace.

### Verdict: RESOLVED

**There is no mathematical generation function to reverse.** Base IDs are
allocated from a tool-assigned hierarchical namespace:
`(family:16 | group/sub/variant/side fields)`, with per-family field layouts
and family-specific side-field bit positions. This is consistent with ALL
prior rejections (H1–H7: no XOR-key, no permutation, no hash, no table —
because it's an assignment scheme, not a function).

**For the chimera build, the usable structure is:**
1. Family = high16 (namespace for categorization).
2. L/R pairing via family-specific XOR side codes (safe up to global mirror).
3. Low16 fields are opaque tool assignments — do not try to decode further.

The "generation fn" item is CLOSED. The remaining usable work is the
side-pairing (done) and family categorization.
