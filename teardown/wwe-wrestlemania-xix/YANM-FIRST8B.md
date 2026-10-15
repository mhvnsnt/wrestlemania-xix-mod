# YANM A-stream first-8B: header-vs-keys — RESOLVED (2026-10-13)

Tool: `tools/yanm_first8b_test.py` (reproduces all numbers).

## Method: dt-sum test
For each dual track:
- `D_H` = dt-sum of 4B keys from **+8** (8B header → ca−2 keys)
- `D_K` = dt-sum of 4B keys from **0** (no header → ca keys)
- `D_B` = dt-sum of B-stream (5B/key, dt at byte 2; no header ambiguity)

Correct interpretation = the one with `|D_A − D_B|` minimized.
Definitive markers: 2nd 4B unit with `dt=0` → header (a zero-duration key
is invalid); `ca=1` → bare 4B key, no header room.

## Measured verdicts
| clip | hash | ca | D_H | D_K | D_B | verdict |
|---|---|---|---|---|---|---|
| a.yag | 7CC9B660 | 26 | 2014 | 2077 | 2394 | HEADER (dt=0) |
| a.yag | 64DB300F | 26 | 2010 | 2123 | 2394 | HEADER (dt=0) |
| a000_0a | 7CC9B660 | 248 | 494 | 690 | 498 | HEADER (\|494−498\|<\|690−498\|) |
| a000_0a | 64DB300F | 4 | 56 | 497 | 496 | KEYS (\|497−496\|<\|56−496\|) |
| both | 0C5BF279 | 1 | — | — | — | KEYS (bare 4B) |

## Structural rule (observed)
**Header IFF ca > 4; ca ≤ 4 → all ca units are keys.**
- ca=1: 1 key. ca=4: 4 keys. ca=26/248: 8B header + (ca−2) keys.
- Needs confirmation on ca ∈ {2,3,5,6…} from more clips.

## Notes
- a.yag's D_H/D_K (2014/2077) match neither D_B=2394; the A-stream is
  sparse (HOLD/ANGLE keys) vs dense B (581 keys). Track duration =
  max(A,B) with hold-last; the header verdict still stands via dt=0.
- The 8B header content varies (`C13FC13F 00000000`, `00C70071 02000000`,
  `C24006C2 40C24002`) — no single magic; dt=0 and dt-sum are the markers.
