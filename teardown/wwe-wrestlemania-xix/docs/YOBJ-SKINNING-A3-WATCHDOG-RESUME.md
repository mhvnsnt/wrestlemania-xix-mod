# Lane (a3) SKINNING ASSEMBLY — Watchdog Resume (2026-10-16 09:25 EDT)

**Checkpoint:** `~/workspace/agent-ops/checkpoints/wmxix-100-retail-skinning-a3.json`
(attempts 0→1, status stays `blocked`)

Continues from `YOBJ-SKINNING-A3-REPORT.md` (batch→bone unresolved) and the two
lane-(a) resume reports. This run tested the remaining cheap leads; the block
is NOT cleared.

## 1. File-family census — candidate (c) CLOSED

`docs/WMXIX-FILE-LISTING.txt`: **zero** `//model/` YMGs outside `model/wrestler/`.
The only other YMG family is `//bg/` (background geometry). So limbs are not
in a different file family. Remaining limb candidates: (a) batch gap data in a
different encoding, (b) Table1 16-byte records' `(u16,0)` payloads.

## 2. Euler-order sweep — orientation is not the (sole) problem

Hypothesis: batch→bone mapping is right but bone world ROTATION is wrong
(wrong euler order), which would explain "correct positions, jumbled parts".
Tested all 6 euler orders (xyz, xzy, yxz, yzx, zxy, zyx) for the parent-chain
FK, mapping b0→JSON[b0], render `/tmp/wmxix_euler_test.png`. **No order yields
a recognizable humanoid.** Orientation alone does not explain the failure.

## 3. Centroid analysis

Under b0→JSON[b0], batch centroids sit 8–21 units from their bone positions —
consistent with parts authored in the positive octant (origin at min-corner),
NOT centered on the bone. Note for next run: centroid→bone distance is
rotation-invariant, so it cannot discriminate between candidate mappings;
only own-eyes shape checks can.

## 4. DOL "bone00"–"bone11" palette hypothesis — INCONCLUSIVE

The 12 DOL bone-name strings (order 05,04,03,08,07,06,09,11,10,02,01,00) could
be a per-batch bone palette: batch idx → YMG slot {0:5,1:4,2:3,3:8,4:7,5:6,
6:9,7:11,8:10,9:2,10:1,12:0}. Tested numerically — but the only cheap metric
(centroid distance) is rotation-invariant (see §3), so the test was vacuous.
Red flag: idx12 → slot 0 (null). Needs a visual test, not a numeric one.

## 5. Batch table re-read (big-endian)

`000_0.ymg`: Table1 ptr @0x5C = 0x5AE0, batch table @0x60 = 0x7CA0.
13 records; record 0 is empty (idx=0,c1=0,count=0,off=0); records 1–12 carry
idx 0,1,2,3,4,5,6,7,8,9,10,12 with counts
72,65,49,120,17,50,15,23,72,102,4,13 (602 verts total).
`get_batches` additionally surfaces a 4-vert b0=11 batch — parse discrepancy
to reconcile (possible 14th record or decoder artifact).

## Status

Block STANDS: batch→bone mapping unresolved after these additional tests.
Next: visual (not numeric) test of the §4 palette hypothesis; DOL
batch-consumer search via lwz+mask patterns (YOBJ+0x60 reader); Table1
payload-as-geometry decode.
