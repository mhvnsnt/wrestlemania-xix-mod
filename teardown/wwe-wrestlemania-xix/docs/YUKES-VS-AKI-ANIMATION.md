# Yukes (WMXIX) vs AKI (No Mercy) animation systems — comparison (MEASURED 2026-10-13)

Both are wrestling animation systems, but architecturally opposite. All
claims below are measured from `WWE Wrestlemania XIX (USA).iso` (Yukes,
GameCube) and `WWF No Mercy (USA) (Rev-A).z64` (AKI, N64).

## At a glance

| | AKI (No Mercy, N64) | Yukes (WMXIX, GameCube) |
|---|---|---|
| File | AkiAnimation in ROM FileTable | `.yag` (YANM), 1 per clip |
| Framing | **Frame-based**: N × 98-byte frames | **Track-based**: 29 key streams |
| Joints | 25 fixed-order joints/frame | 21 joint-groups + 8 unknown tracks |
| Rotation enc | s8 degrees + 12-bit pivots | s16 `32767·sin(angle)` (asin decode) |
| Time enc | implicit (frame index) | explicit u8 **delta** per key |
| Root motion | OverallMovementXYZ per frame | f32 triple in header (undecoded) |
| Interpolation | linear between frames (presumed) | hold-last + key deltas |
| Duration | `4 + N*98` size → N frames | per-track dt-sums (vary up to 2×) |
| Bilateral | L/R joints are separate entries | **dual tracks**: A=common-mode, B=trims |

## AKI AkiAnimation (measured)

- 4-byte `Toki2` header + N × **0x62 (98)-byte frames** (`4 + N*98` exact).
- Each frame: 19× `PivotRotation` (4 B: 12-bit pivot X, **s8 rotation**,
  12-bit pivot Z, packed 3-2-3) + 1× `OverallMovementXYZ` (4 B, same
  packing) + 6× `MovementXYZ` (3 B).
- Fixed joint order (25): Pelvis, OverallMovement, LowerAb,
  LowerAbMovement, UpperBody, UpperBodyMovement, Neck, Head, LowerLeftLeg,
  UpperLeftLeg, LeftLegMovement, LeftFoot, LeftHand, LeftFingers,
  LowerLeftArm, UpperLeftArm, LeftArmMovement, LowerRightLeg, UpperRightLeg,
  RightLegMovement, RightFoot, LowerRightArm, RightHand, RightFingers,
  UpperRightArm, RightArmMovement.
- s8 rotation = degrees (calibrated: `s8 × 182.04` … verified by retarget;
  motion correlation 0.69–1.0 onto Tekken 3).
- Frame counts 1–123 (mode 13). ~1,360 anim files (`0x2DD9`–`0x335F`).
- Move → anim linkage: move DB `AnimID` = file ID − 0x3322.

## Yukes YANM (measured)

- 56-byte header (`YANM`, payload size, `0x011F0000`, `0xCD89A39E`,
  f32 seconds-per-tick, 3 f32 params) + **29×32-byte track directory**
  + key streams at/after 0x3F0.
- Track record: joint hash, A-offset (0=single), key-offset, f32-triple
  (nonzero ⟺ dual), w24 (nonzero ⟺ dual), key count / packed (ca,cb).
- **Single**: 5-byte keys `(s16 ch1, u8 dt, s16 ch2)`, dt = delta (0–255).
  Channel = `32767·sin(hinge)` → `angle = asin(s16/32767)` (proven by
  circularity + smoothness tests; saturates ±90°).
- **Dual**: A = 4-byte keys `(s16 val, u8 flags, u8 dt)` = bilateral
  **common-mode** hinge angle; B = 5-byte keys = per-side trims;
  `rec_i(t) = A(t) + B_i(t)` on the group's hinge axis (r²(A~B) ≈ 0).
- 21 tracks ↔ 21 `.ycg` joint-groups 1:1 (hash match). Each ycg record is a
  **1-DOF hinge**; hinge axis uniform per group (local X: 13 groups,
  local Z: 6, local Y: 2 — FK-confirmed).
- 3-chain groups: ch1→rec1 (hip/shoulder), ch2→rec2 (knee/elbow),
  **rec3 = −(rec1+rec2)** (measured ≤0.03° end-effector stability).
- 8 tracks match NO ycg (0/175 files); 7/8 static in most clips.
- Per-track durations vary up to 2× within a clip (hold-key authoring
  variance); retarget: hold-last + clip.

## Key architectural differences

1. **Frames vs tracks**: AKI stores a full pose per frame (25 joints × 98 B);
   Yukes stores 29 independent key streams (sparse, delta-timed). Yukes is
   ~10× more compact for idle/hold-heavy wrestling anims.
2. **Rotation encoding**: AKI s8 degrees (±128° range, ~0.7° step) with
   explicit pivots; Yukes s16 sin-encoding (±90°, ~0.003° step, saturates).
   Yukes has finer resolution but can't exceed 90°/hinge.
3. **Bilateral motion**: AKI keys L/R joints independently; Yukes
   **factorizes** symmetric motion into common-mode (A) + trims (B) —
   a compression win for wrestling's mirrored holds.
4. **DOF model**: AKI joints have pivot+rotation (multi-DOF-ish); Yukes
   joints are strict **1-DOF hinges** (proven by quat-family + FK tests).
   Yukes trades expressiveness for a tiny, robust rig.
5. **Root motion**: AKI has explicit OverallMovementXYZ per frame; Yukes
   header f32 triple is undecoded (root-motion candidate).
6. **Retarget posture**: AKI→Tekken3 v1 works (s8 degrees direct);
   YANM→Tekken3 v2 works (asin decode + rec3 rule + hold-last).

## For Western Heart

- Use **Yukes YANM** as the animation source (finer, already retargeted v2).
- Use **AKI** for move-set breadth (1,360 anims + move DB linkage).
- Both retarget through the 1-DOF hinge abstraction; the rec3 rule and
  hold-last handling are Yukes-specific.
