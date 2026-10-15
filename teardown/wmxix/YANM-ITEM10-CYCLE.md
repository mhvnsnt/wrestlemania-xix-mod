# YANM Item-10 Cycle Results — ECD high-preset, POF0 sub-structure, .atr semantic decode

Measured 2026-10-14 (watchdog continuation cycle, attempt 35). Probes:
`tools/yanm_ecd_highpreset.py` (high-preset census + renders + camera/event
correlations), `tools/yanm_pof0_substructure.py` (POF0 segment grammar +
linearity fits + 045), `tools/yanm_atr_semantics.py` /
`tools/yanm_atr_semantics2.py` / `tools/yanm_atr_motion_xcorr.py` (.atr
semantic decode; probes committed in 1b21c56, results documented here).
`docs/atr_all_events.json` = full 167-clip .atr census (REGENERATED this
cycle to cover all 167; the previous version had only 108).
High-preset renders: `docs/ecd-render-test/*_highpreset_view.png`,
`c139_control_below.png`, metrics `highpreset_metrics.json`.

## (a) ECD (0,~75) high-preset role + elevation sign

### Elevation sign: CONFIRMED (+elev = above horizon)

Viewed `FACE_ecd_view.png` (elev=+79.9, azim=0) with own eyes: the performer
is foreshortened from directly above — a top-down "mugshot" of the
head/shoulders. A below-ring camera is physically impossible (the ring has
a floor). Control render `c139_control_below.png` (same clip at elev=−80)
is the geometric mirror — no additional information, confirming the sign
reading is a pure convention choice and +above is the only physical one.

### High-preset population (measured)

215-clip ECD census classes: high (ch1≈0, ch2≈70–80°) = **51 clips**,
default (|ch|≤12°) = 79, side (ch1≈75°) = 61, other = 17.
The high preset spans all move families (a/b/c/d/showcase) — no
move-category exclusivity.

Exact shared presets (hand-tuned values reused across clips):
- **(0, 79.89): 12 clips** — `a002_0a, a004_0a, a015_0a, a023_0a`
  (a-family), `c013_0a, c113_0a, c118_0a, c140_0a, c211_0a, c226_0a`
  (c-grapples), `FACE`, `HAND` (viewer close-up showcases).
- **(3.6, 75.66): 8 clips** — showcases `8503/8514/8515/8516/8517/8519/8528/8541_0a`.

The FACE/HAND close-up showcases sharing the exact (0,79.89) preset with
4 a-taunts and 6 c-grapples is the strongest role evidence: this preset is
a **high close-up / "mugshot" camera** used for upper-body-focused beats
(face/hand showcases, taunts, and grapples that frame the head/upper body,
e.g. front-headlock-type holds). The renders (c139/a004/8503 from their
ECD views) show the performer framed head-on from above.

### Negative results (all measured)

- **Pelvis-height test: IMPOSSIBLE.** YANM animates joint rotations only;
  root translation is not carried by any track (no f32/translation keys;
  .atr 0x34 (a,b) are small-int IDs, not positions). The 21 ycg chains
  float at bind positions in the FK model, so mid-frame "pose" measurements
  (foot spread etc.) are not anatomically meaningful — the renders are
  camera-framing checks, not pose truth. Do not cite the *_highpreset_view
  renders as pose evidence.
- **No correlation with .atr 0x8B camera events**: mean 0x8B count
  high=3.18 vs default=2.40 vs side=2.88; 0x8B@t=0 present in 20/22 high
  vs 35/40 default (near-universal init event).
- **0x8B@t=0 param does NOT encode the preset**: param=1/2 spread across
  all ECD classes. The ECD track remains the sole camera-preset carrier.
- **Duration**: high-preset clips marginally longer (median 0x01-tick 863
  vs 766 default) — weak, not diagnostic.

### Verdict

Elevation sign CLOSED (+elev = above horizon, own-eyes confirmed).
High-preset role: **"high close-up" camera for upper-body beats** —
supported by the FACE/HAND/taunt/grapple preset sharing and the mugshot
framing; the exact per-grapple trigger stays OPEN (needs engine or visual
confirmation of which holds get it).

## (b) POF0 sub-structure / linearity / 045

Starting points `tools/yanm_item3_pof0.py`, `tools/yanm_item3_byteramp2.py`;
ymg files from `.scratch` (range-ISO). New probe:
`tools/yanm_pof0_substructure.py`.

### ID-list structure (new)

The POF0 container sits after a **variable-length ID list** following the
`0C5BF279` word (prior cycles assumed 12 words):

| wrestler | ID words | POF0 bytes |
|---|---|---|
| 000_0 | 14 (classic 12 + DDFD7A6E 4DFBFA6F) | 168 |
| 002_0 | 32 (classic 12 + 20 more) | 268 |
| 016_0 | 14 (permuted 12 + 0DB87A31 97604B5F) | 172 |
| 045_0 | 19 (5D98B7F1 + DDF67B76–7F run + DDF67BFE/FF + 6) | 264 |

### Segment grammar (measured)

Byte vocabulary: data `0x41`–`0x61`, markers `≥0x80` (observed
0x80–0xF5), pad `0x44`. 000_0's 168B parses as **exactly 12×14B segments**
with internal structure `[data bytes][0–2 marker bytes][0x44 pad]` —
e.g. seg0 `41 42 42 42 45 41 46 42 41 | 96 a4 | 44 44 44`,
seg9 `42×7 | 9d 98 | 43 44 | 84 e5 | 45` (markers can sit mid-segment).
The other wrestlers use the same vocabulary with different lengths
(172/264/268B, not clean 14B multiples) and body-specific marker
positions — consistent with item-9's per-body correction curves.

### Linearity: REJECTED

Active (non-0x44, non-marker) bytes are **not linear ramps**: per-segment
linear-fit R² mostly 0.0–0.4 (000 seg8: 0.83, seg9: 0.79, 002 seg10: 0.78
are the maxima). The bytes read as small control-point wiggles (±3 LSB
around `0x44`) — i.e. spatially-varying correction curves, not ramps.
Constant segments (all-`0x45`, all-`0x57`, all-`0x58`, all-`0x42` runs up to
27B) = uniform-bias curves. **`0x44` = identity/no-op, strengthened**:
dominant value everywhere (045: 125/264), flat segments are all-0x44,
wiggles center on it.

### 045: bigger rig, same system

045_0's 264B POF0 (11 markers, 29 distinct bytes) uses the identical
grammar (marker-terminated curves, 0x44 pads, constant-bias runs at
0x45/0x57/0x58). It is NOT a different system — just more detail elements
(19 IDs vs 14). No ID→curve-count function found (000: 14 IDs / 12
segments; 002: 32 IDs; 045: 19 IDs) — the trailing IDs have no curves or
share; mapping stays OPEN.

### Refined hypothesis

POF0 segments = **per-detail-element 1D correction curves over a small
sample domain, 0x44 = identity**; constant segments = uniform per-element
bias; marker bytes (≥0x80) = per-curve type tags (which attribute the
curve drives is still open).

## (c) Item-10(2): .atr event semantic decode

Layout (big-endian — **corrects the item-8 doc, which had LE fields**):
`DATA` + u32 trailer_offset (=16+16·event_count) + u32 `0x00000100` +
u32 event_count + 16B records `[u32 a][u32 b][u32 type<<24|tick][u32 param]`,
trailer `[u32 x][u32 y]` + `POF0` + u32 len + bytes. All 167 ringmotion
`.atr` parse under this layout.

### 13-type vocabulary (167-clip census)

| type | n | reading |
|---|---|---|
| 0x00 | 94 | init-ish (first event in only 6/94) |
| 0x01 | 94 | **end marker**: present in 94/167, always the LAST event when present; tick ≈ 0.6–0.8× yag duration where measurable (not 1.0 — not simply "duration") |
| 0x33 | 1117 | **cadenced one-shots**: c-family (98 clips) + d-family (5); median inter-event gap **36 ticks** (1014 gaps) |
| 0x34 | 1320 | **transition pairs**: params ∈ {0,1,2} (622/577/121); on/off pairing with violations (343 multi-ON) — not a clean state machine |
| 0x88 | 585 | paired 2-channel system with 0x89 (468/957 adjacent pairs alternate) |
| 0x89 | 474 | (see 0x88) |
| 0x8B | 299 | init @t=0 in ~all clips (params 2:58, 1:38, 0:2) + periodic through the clip ("camera-ish", unconfirmed) |
| 0x32 | 30 | rare |
| 0x14/0x30/0x49 | 2 each | very rare |
| 0x98 | 6, 0x99 | 1 — rarest |

### Trailer (x,y): final-(a,b) cache

`(x,y) == last event's (a,b)` in **122/167** clips; `== 0x8B@t=0 (a,b)` in
5/98; `(0,0)` in 108. Reading: the trailer caches the final event's
(a,b) pair (21 distinct values; top (0,0):108, (1,20):10, (16,0):10).

### Motion cross-correlation: no impact alignment

6 clips (c001/c101/c102/c016/c135/c200): per-frame motion energy (sum of
|Δ joint-angle vector|) vs event ticks. Mean energy percentile at event
ticks: 60–69th vs 50.0 random baseline; local-max hit rates 0.11–0.21 vs
0.12 baseline. **No event type aligns with motion-energy peaks** — .atr
events are NOT hit/impact moments of the performer's own motion (they may
drive the opponent, camera, sound, or particles instead).

### Semantics status

Structure CLOSED (layout, vocabulary, 0x01 end marker, 0x33 cadence,
0x34 pairs, 0x88/0x89 pairing, trailer cache). **Semantic labels OPEN**:
which type = camera cut / hit / sound / particle needs engine or
audiovisual confirmation. The .atr POF0 trailer (4B `42 00 00 00` on c200
variants) is the same container as the ymg byte curves — same detail
system, per-move instance.

## STOPPED HERE next

1. ECD high-preset exact trigger per grapple (needs engine/visual).
2. POF0 marker-byte semantics (which attribute each curve drives); ID→curve
   mapping for trailing IDs; 002_0's 20 extra IDs.
3. .atr semantic labels (camera/hit/sound/particle) — needs engine or AV.
4. CAW `.gci` — still blocked headless (needs parent Dolphin browser task
   with KNOWN CAW values; OUT OF SCOPE for this lane).
