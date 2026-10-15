# AKI (No Mercy) → Tekken 3 Retarget — v1 (2026-10-13)

First working pipeline that plays a No Mercy (AKI engine) wrestling animation
on a Tekken 3 skeleton. One move animation (`0x339A`, 58 frames) → King
(BNS record 95, `tekken3/models/king95/`).

## Pipeline (tool: `tools/aki_to_tekken3.py`)

1. **Decode** the AKI animation via `wwf-no-mercy/tools/anim_extract.py`:
   19× 1-DOF `PivotRotation` (s8 rotation + 12-bit pivot XZ) + root movement.
2. **Calibrate**: s8 rotation value EQUALS degrees (measured: pelvis s8 −39..121
   = doc's −39°..+121°). So `Tekken_s16 = s8 × (65536/360)` = s8 × 182.04.
3. **Map** AKI joints → Tekken 3 FK Euler joints (provisional anatomical):

   | AKI joint | Tekken joint |
   |---|---|
   | Pelvis | joint0 (pelvis) |
   | LowerAb, UpperBody | joint1 (chest) |
   | Neck, Head | joint3 (head) |
   | UpperRightArm | joint4 (R shoulder) |
   | UpperLeftArm | joint5 (L shoulder) |
   | LowerRightArm | joint6 |
   | LowerLeftArm | joint7 |
   | UpperRightLeg, LowerRightLeg | joint8 |
   | UpperLeftLeg, LowerLeftLeg | joint9 |

   (Multiple AKI joints averaged when mapping to one T3 joint.)
4. **Overlay**: `tekken(t) = stance0 + (aki(t) − mean(aki))` on the X channel
   (provisional axis, same pattern as YANM v1).
5. **Root**: AKI OverallMovement → Tekken root_x/y/z (scale 0.5, provisional).
6. **Output**: `docs/aki_to_tekken3_v1.json` — 58 × 49-channel s16 pose vectors.

## Verification (measured)

Source-vs-retarget motion-shape correlations (mean-subtracted degrees):
- Pelvis → joint0: **+1.000** (perfect)
- UpperBody → joint1: +0.901
- UpperRightArm → joint4: +0.924
- Head → joint3: +0.796 (Neck+Head averaged)
- UpperLeftLeg → joint9: +0.742 (Upper+Lower averaged)
- UpperRightLeg → joint8: +0.689 (Upper+Lower averaged)

All 9 driven channels move; curves track the source choreography. The lower
leg/head correlations are from averaging, not from failed transfer.

## v1 scope limits (honest)

- **Axis provisional**: AKI 1-DOF hinge → Tekken X for all joints. True
  hinge→Euler-axis mapping needs AKI joint frame data (open).
- **Averaging**: Upper+Lower arm/leg collapsed to single T3 joints; T3 has
  10 Euler joints vs AKI's 19 hinges — a fuller mapping needs T3 joint anatomy.
- **Root scale** (0.5) is a guess; AKI movement units vs T3 units uncalibrated.
- **No IK**: T3 limbs use IK channels (not driven here); v2 should do
  AKI FK → T3 IK like YANM v2 did.
- **No render yet**: same as YANM v1 — numeric + plots, not pixels.

## What this unblocks

The full No Mercy AKI animation library (~1,360 clips) can now be retargeted
to Tekken 3 models via this pipeline. This is the Western Heart "wrestling
animations on Tekken models" path for the AKI engine (complements the Yukes
YANM→Tekken3 path).
