# YANM w24 / f32-triple correlation hunt — MEASURED (2026-10-13)

Tool: `tools/yanm_f32_corr.py` (12 non-degenerate duals, 7 clips).

## Measured facts
- **f2 (w24, track dir +24):** tiny (0–0.00017 as f32), nonzero ONLY on
  non-degenerate duals; (0,0,0) for degenerate (ca=1,cb=1) and singles.
  Best correlation: f2 vs A-channel mean angle **r=0.717** (n=12).
- **f1 (track dir +20):** varies per clip AND per joint (−1.16..+0.22 rad
  = −66°..+12°). **NOT a rest pose** — varies per clip for the SAME joint
  (7CC9B660: −0.0, +0.0095, +0.221, −0.093, −0.220, −1.157, −0.535 across
  7 clips). **NOT derived from B keys** — f1 lies OUTSIDE [min(B),max(B)]
  (e.g. a004_0a: f1=−66.3°, B∈[−22°,+2°]).
- **f0 (track dir +16):** small (−0.04..+0.002), weak correlations
  (|r|≤0.36).
- f1 magnitude depends on JOINT: 7CC9B660 has large |f1|, 64DB300F has
  tiny |f1| (−0.001..+0.00001) across the same clips.

## Leading hypothesis: per-channel biases (OPEN, needs FK verify)
A dual has 3 angle channels (A: 4B keys → 1 ch; B: 5B keys → x,y = 2 ch).
The f32-triple may be **per-channel biases in radians**:
`(f0,f1,f2) = (A-bias, B_x-bias, B_y-bias)`, keys = deltas.
Example (a004_0a 7CC9B660): B_x = −66.3° + (−22°..+2°) = −88°..−64°
(plausible joint swing); A = −2.4° + (−1°..+2.4°); B_y ≈ 0°.
**Not confirmed** — needs FK against the skeleton to verify the biased
angles produce coherent poses. Semantics: OPEN (narrowed to bias-vs-rest).

## Rejected
- f32-triple as rest/bind pose: REJECTED (varies per clip, same joint).
- f1 as B-stream statistic (min/max/mean): REJECTED (outside B range,
  |r|≤0.12 vs bmean).
- w24 as gain: REJECTED (would be negligible vs s16 B; prior).
