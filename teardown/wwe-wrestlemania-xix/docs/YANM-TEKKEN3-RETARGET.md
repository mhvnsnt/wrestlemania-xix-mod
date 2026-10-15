# YANM → Tekken 3 Retarget — v1 (2026-10-12)

First working pipeline that plays a Yukes wrestling animation on a Tekken 3
skeleton. One animation (`ringmotion/a000_0a.yag`, entrance, 13.93 s) → one
model (King, BNS record 95, `tekken3/models/king95/`).

## Pipeline (tool: `tools/yanm_to_tekken3.py`)

1. **Decode** the YANM: per-track 5B key streams → hinge angle
   `α = asin(s16/32767)` rad, time from cumulative `dt × [0x3C]` s/tick.
2. **Resample** each mapped group's x-channel to a 30 fps uniform grid
   (465 frames for a000_0a).
3. **Map** ycg group → Tekken 3 FK Euler joint (v1, FK only):

   | ycg group | ycg anatomy (task-3) | Tekken joint | Tekken slot |
   |---|---|---|---|
   | 099CD766 | pelvis candidate | joint0 | 0 (pelvis) |
   | 613B75B7 | torso 2-hinge | joint1 | 1 (chest) |
   | 095CD669 | static bent joint | joint2 | 11 (hips) |
   | 5B214D4E | head/neck candidate | joint3 | 2 (head) |
   | 6198F425 | ARM side-A | joint4 | 3 (R shoulder) |
   | 6198F4D5 | ARM side-B | joint5 | 7 (L shoulder) |

   (Slot mapping per n0madic/tekken3remake `docs/research/formats/animation.md`:
   ten Euler joints → slots 0,1,11,2,3,7,6,10,14,17.)
4. **Overlay**: `tekken(t) = stance0 + (yanm(t) − mean(yanm))`, converted with
   65536 units = 360°. Mean-subtraction keeps King's fighting stance and adds
   the wrestling *motion* on top (absolute YANM angles would snap him into the
   Yukes bind pose). 1-DOF hinge → Tekken joint local **X** channel.
5. **Output**: `docs/yanm_to_tekken3_v1.json` — 465 × 49-channel s16 pose
   vectors + mapping metadata; `docs/yanm_to_tekken3_v1_plot.png` — driven
   joint deltas (visual proof of transfer).

## Verification (measured)
- All 6 driven channels move: pelvis ±37°, chest −8°..+72°, head −52°..+18°,
  R shoulder −7°..+9°, L shoulder −23°..+10° (deltas; hips static as expected).
- Curves match the source YANM choreography (ramps/holds/oscillations of an
  entrance). joint4_x clips at s16 max (+32767) on one peak — noted, harmless.
- No NaNs; all values in s16 range after clamp.

## v1 scope limits (honest)
- **FK only**: Tekken 3 drives limbs via IK (channels 3–14 = limb targets,
  15–18 swivel). Legs (BD groups, the biggest YANM movers) are NOT retargeted
  in v1.
- **Axis**: 1-DOF hinge → joint X is provisional; true hinge→Euler-axis mapping
  needs the Tekken joint frames (open).
- **L/R**: ycg side-A/B → Tekken R/L is provisional (task-3 open item).
- **No render yet**: Tekken 3 full-body bind pose is still pending on the
  tekken3 side (part→slot table), so v1 is verified numerically + plots, not
  pixels.

## v2 plan
1. Legs: FK the YANM BD chain (hinge about local-X→world-lateral) → ankle
   target in ycg space → transform to Tekken normalized-skeleton space →
   write IK target channels 9–14 (+ swivel 17–18).
2. Arms: same for wrist targets → channels 3–8 (+ swivel 15–16).
3. Resolve hinge→Euler axis per joint; resolve ycg L/R.
4. Render: compose King parts with the pose (needs part→slot table) and
   eyeball-verify against the YANM motion.

## v2 (2026-10-13) — leg/arm IK, corrected axes, resolved L/R

Tool: `tools/yanm_to_tekken3_v2.py` (uses `tools/fk_ycg.py`). Output:
`docs/yanm_to_tekken3_v2.json` (574 frames @30fps, 19.13s), renders
`docs/retarget_v2_render.png`, `docs/retarget_v2_paths.png`.

### (a) Leg/arm IK
FK the YANM ycg chains in ycg space → ankle/wrist trajectories → map to
Tekken3 normalized-skeleton IK targets (overlay on King stance0):
`ch = base + R·(tip(t) − mean(tip))·s`.
- Legs: BD5B5259→R (ik2/ch9-11), BD5B2A59→L (ik3/ch12-14). Hip = the YANM
  DOF; knee fixed at bind (YANM leg track carries 1 DOF; T3 2-bone IK solves
  the knee). Scale s_leg = 895/34.06 = 26.28 (T3 normalized leg / ycg leg).
- Arms: 6198F425→R (ik0/ch3-5), 6198F4D5→L (ik1/ch6-8). Shoulder/elbow from
  small-regime asin; pure IK (v1 shoulder-Euler drive removed — no double-drive).
  Scale s_arm = 533/26.08 = 20.44.
- Measured deltas: ankles ±150 fwd/back, ±50 up/down (T3 units); wrists ±95/±25.
  Swivels held at stance base.

### YANM decode corrections (measured)
- **Hinge axis = ycg local X → world lateral Y** (from bind quats; the doc's
  "local-X hinge" confirmed — my early manual calc was wrong).
- **Leg tracks use half-angle encoding**: (c1,c2) lies on circle r=32767;
  hinge = 2·unwrap(atan2(c2,c1)) wrapped to ±180°. The c1 sign-flip "spikes"
  are the quaternion-style half-angle wrap, not data glitches. Leg hips swing
  −13°..+36° (sane walk), not the ±77° the naive asin gave.
- **Arm tracks use small-regime**: shoulder=asin(c1/32767), elbow=asin(c2/32767)
  (two independent hinges; |(c1,c2)| small, not on circle).

### (b) Hinge → Euler axis
YANM hinge is about ycg lateral (Y). Tekken3 normalized lateral = Z
(shoulders/hips split in z). FK Euler joints (pelvis/chest/hips/head =
joint0-3) now driven on the **Z channel** (sagittal pitch). v1's X channel was
yaw — wrong for pitch. Measured: pelvis −41°..0°, chest −80°..0° (deep
entrance bow), head 0°..+47°, hips static (095CD669 1-key).

### (c) L/R
ycg y+ = R (Yukes authoring convention: ymg bone locals have y+=R for both
clavicles and thighs). ycg→T3 map `T3=(−ycg_x,−ycg_z,−ycg_y)`, det=+1
(chirality-preserving, no mirror). ycg-R→T3-R throughout. Absolute anatomical
L/R of ycg sides rests on the ymg convention link (documented, high-confidence).
ycg forward/back sign in the map is provisional.

### (d) Render verification (own eyes)
`docs/retarget_v2_render.png`: 4 frames of T3 schematic (normalized skeleton,
2-bone IK elbows/knees) — coherent humanoid, limbs track the YANM, no
explosions/NaNs. `docs/retarget_v2_paths.png`: ankle/wrist target paths are
smooth (spike-free after half-angle unwrap).

### Open / next
- Knee DOF: YANM leg is 1-DOF; if a knee signal exists it's undecoded.
- ycg forward sign; absolute ycg L/R proof (needs in-game pose).
- Swivel modulation from YANM; root translation (YANM has no root track —
  entrance stays in place).
