# YANM Item-8 Cycle Results — ECD render test (camera-framing verdict)

Measured 2026-10-14 (watchdog continuation cycle). Probes:
`tools/yanm_ecd_render_test.py` (FK + matplotlib renders + view-optimality
metric), `tools/yanm_ecd_marginals.py` (full 215-clip ECD census).
Files re-extracted via range-ISO into `wwe-wrestlemania-xix/.scratch/files/`
(git-ignored). Renders: `docs/ecd-render-test/*_ecd_view.png` (etc.),
metrics: `docs/ecd-render-test/metrics.json`,
full-universe ECD table: `docs/ecd-render-test/ecd_all_clips.json`.

## Method

FK skeletons built from `model/wrestler/000_0.ycg` (42 records / 21 groups)
+ mid-frame yag poses (asin channel decode; duals via A+B; hinge axes from
`docs/yanm-task2-finish.json`; rec3 rule for 3-chains). Display frame:
ycg (x=up, y=lateral, z=fwd) → (x=fwd, y=lateral, z=up), so
`view_init(elev=ch2, azim=ch1)` matches the hypothesized ECD=(yaw,pitch).
Each clip rendered from its ECD view + 3 controls (standard/front/top).
Quantitative check: projected-2D variance of action joints (limb tips + head)
at the ECD view vs a 10°×15° view grid (percentile + ratio-to-best).

## Finding 1 — ECD channels are bimodal: {~0°, ~+75°}, both-hi never occurs

Full 215-clip census (208 with ECD), asin-decoded degrees:

| ch1 bin | n | ch2 bin | n |
|---|---|---|---|
| 0..+10 | 108 | 0..+10 | 101 |
| +70..+80 | 53 | +70..+80 | 51 |
| +60..+70 | 11 | +60..+70 | 4 |
| else | 36 | else | 52 |

Joint (sign+band): (+lo,+lo)=52, (+hi,+lo)=47, (+lo,+hi)=38,
(+lo,−lo)=19, (−lo,+hi)=17, (+hi,−lo)=14, rare mids=10.
**(+hi,+hi) = 0.** ch1 < −40°: 1 clip. ch2 < −40°: 1 clip.
No move-category dependence (a/b/c/d all show the same lo/lo, hi/lo, lo/hi mix).

This is NOT a continuous (yaw,pitch) field — it is three preset regions:
(0,0)=default, (~75,0)=side, (0,~75)=high. The exact values vary 62–80°
(hand-tuned per move, not quantized IDs). Mutual exclusion (never both hi)
fits hand-authored camera presets (side+high together would be disorienting).

## Finding 2 — renders: ECD views are sensible camera framings

- `c200_0a` ECD=(63.0,24.5): 3/4 view from front-right, slightly above —
  reads as a genuine action shot (raised arm, extended legs clearly visible).
  (`docs/ecd-render-test/c200_0a_ecd_view.png`)
- `c200_1a` ECD=(0.9,1.1) / `c200_2a` ECD=(1.8,0.2): dead-front eye-level
  default camera; the variant's legs kick toward the camera (dramatic
  foreshorten, not a "bad" framing — the action faces the viewer).
- `showcase8503` ECD=(3.6,75.7): high front angle on a wide-legged
  arm-raised taunt — the full leg spread reads top-to-bottom on screen.
- `FIGHTING.yag` ECD=(0.2,3.6)≈(0,0): default camera for the stance showcase.
- `FACE.yag`/`HAND.yag` share ECD=(0.0,79.9): one close-up preset for both
  showcase clips (13 clips total at ≈(0,79.9)).

Variant pairs stay variant-specific: c200_0a=(63.0,24.5) vs _1a=(0.9,1.1)
vs _2a=(1.8,0.2); c224_0a=(77.6,9.0) vs _1a=(2.5,0.9) — different cinematics,
different cameras. (Only 2 multi-variant families in the 215 universe.)

## Finding 3 — view-optimality metric: ECD ≠ max-spread (expected)

Projected action-joint variance at ECD view vs view grid: c200_2a at 2nd
percentile (0.32×best), FIGHTING at 0th (0.31×best), showcase8503 at 32nd
(0.64×best); best grid view is consistently (elev=0, azim=90) = pure side.
This does NOT falsify camera-framing: the metric rewards maximum spread
(edge-on side view), while a framing camera trades spread for readability
(c200_0a's 3/4 view) or uses a fixed default (front). A "best camera"
is not a "maximum spread camera".

## Verdict

**Camera-framing (yaw/pitch preset) hypothesis: SUPPORTED.**
Evidence: renders show sensible framings; three preset regions
(default/side/high) with hand-tuned values; variant-specific;
FIGHTING=default; FACE/HAND share one preset; 85xx showcases reuse 9 presets;
static-per-move, engine-consumed, absent only in non-wrestler clips —
all consistent. Mapping (ch1,ch2)=(azim,elev) preferred over the swap
(the swap would make c200_0a a steep 63° top-down, implausible as an
action shot).

**Downgraded:** eye-gaze (bimodal 0/75 with mutual exclusion does not look
like gaze; face never animated; (75,75) gaze would be allowed but never
occurs); opponent-setup (no positive evidence; (0,75)="opponent above"
is nonsense).

**Open / needs engine or visual confirmation:**
- The (0,~75) "high" preset's exact role (hero high angle? top-rope moves?
  8 of 30 85xx showcases + FACE/HAND use it).
- Elevation sign: +elev read as above-horizon (a below-ring camera is
  physically implausible — the ring has a floor). Kept as assumption.
- FACE.yag's (0,79.9): near-top-down on a face showcase is odd; viewer
  clips may use ECD differently, or the showcase framing is genuinely
  a high "mugshot" angle.

## New lead (not ECD): .atr event timeline decoded (structure)

`ringmotion/*.atr` = `DATA` + u32 size + `00000100` + u32 event_count +
16B records `[u32 a][u32 b][u32 (type<<24|tick)][u32 param]`, trailing
`POF0` + u32 len + bytes (4B `42 00 00 00` on c200 variants — same container
as the ymg byte curves). c200_0a: 9 events, types 0x8B/0x33/0x88/0x34/0x49
at ticks 0–124; c200_1a: 36 events; c200_2a: 23 events. 0x8B events at t=0
in all three (params differ per variant). Full semantic decode (which type
is camera cut / hit / sound) is a separate item — carried forward.
