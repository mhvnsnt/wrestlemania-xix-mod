# YOBJ 16-byte batch table — per-field semantics (MEASURED 2026-10-13)

Sample: `model/wrestler/000_0.ymg` (69,176 B). Tool: `tools/yobj_batch_semantics.py`.
Table at header `[0x5C]` (0x5AE0), **58 records × 16 bytes**.

## Record layout (measured)

| bytes | field | semantics (measured) |
|---|---|---|
| 0–3 | u0 | byte offset, base **file 0x80**, to this record's payload |
| 4–7 | u1 | 0, 1, or `0x80000000\|X` (secondary; semantics OPEN) |
| 8 | b8 | id in `0x03–0x46` (3–70); NOT bone index (see below) |
| 9–10 | marker | u16: v=1 → `0xFFFF`; v=2 → `(b8-1)<<8 \| 0xFF` (51/52 records) |
| 11 | variant | 1 or 2 (v=1: marker=ffff, 6 records; v=2: 52 records) |
| 12–15 | count | u32; **count = number of 4-byte payload units** (see below) |

## Measured facts

1. **Group-header pattern**: records 1–7 share `u0=0x61C0`; their counts
   (44,14,14,8,4,38,6) sum to **128 = record 0's count** (rec0: u0=0,u1=0,
   b8=0x06,v=1,count=128). Record 0 is the group header for the 0x61C0
   payload group. All other records (8–57) have unique u0.
2. **count = 4-byte units**: `u0[i+1] − u0[i] = count[i]×4` for 40/58 records
   (all of 41–57, 37–39, 33–34, 31, 27–28, 25, 21, 18–19, 16, 12, 9).
   18 records deviate (8,10,11,13–15,17,20,22–24,26,29–30,32,35–36,40,44) —
   overlapping or gapped payloads, or a second format. Count sum = 892.
3. **Payload is (u16, 0) pairs**: second u16 is 0 for ~100% of units
   (b2zero=1.00 on 56/58 records). Values are coordinate-scale 0–4096,
   clustered (not uniform): bucket 0–255:144, 2048–2303:163, 3072–3327:109.
   Repetition is strip-like, e.g. records 45–56 concat:
   `[2048,3723,2048,3150,1820,2048,3723,3150,1820,2048,…]` (4 values cycling).
4. **b8 is NOT a bone index**: records 1–7 (same u0 group) have
   b8 = 06,40,45,46,36,44,22. As 1-based bones: 6=Head, 64=R Foot, … —
   a foot bone in the head group is incoherent. b8 likely a **material or
   part id** (range 3–70). Elbow part (1 record): b8=0x20.
5. **marker_hi = b8−1** (v=2, 51/52 records; exceptions: (15,13ff),
   (2A,28ff), (3E,02ff), (1E,41ff), (39,33ff), (27,30ff), (43,02ff)).
   Suggests marker = (material_idx, 0xFF flags); v=1 (marker=ffff) = default.
6. **u1**: 0 (49 records), 1 (recs 15,23), or `0x80000000|X`
   (recs 1,2,9,12,16,24,37; X=0x10000,0x72C00,0x38000,0x47F00,0x87F00,
   0xD8000,0x178000 — all > filesize except 0x10000, so NOT file offsets).
7. **Payload is NOT an index buffer into any located pool**:
   - Hypothesis "indices into s16x3 pool at [0x80,0x6240)": REJECTED —
     pool as s16x3 is unsmooth garbage (median dist 10439), indexed verts
     scattered (median 12006).
   - Hypothesis "4096-vert s16x3 pool at [0x240,0x6240)": REJECTED —
     no base in [0x80,0x240] yields in-range smooth data.
   - Hypothesis "(x,y) 2D verts": REJECTED — 2D plot is a scribble, not
     coherent patches.
   - Max value 4096 needs a 4097-vert pool; none located in the 69 KB file.

## Material-table linkage — OPEN

Material table @0x10704: 20-byte records, ~20 nonzero
(`[u16 a][u16 idx_off][RGBA×4]`; mat1 = `0001 0830 b2b2b2ff…`).
If marker_hi = material index (0-based), materials 2–69 would be needed —
but only ~20 material records exist. Either the material table is larger
than parsed, or marker is not a material index. **OPEN.**

## Full model assembly — status

- The **13 skin batches** (@0x7CA0, 8B recs, 606 s16x3 verts) → 58 heuristic
  strips → 383 tris is the WORKING assembly (`tools/yobj_strips.py`,
  eye-verified). This is the committed `batch→vertex→triangle` path.
- The 58-record table's role: per-batch **draw descriptors** (payload offset,
  unit count, material/part id). Its payload is a separate attribute stream
  (coordinate-scale (u16,0) pairs, 892 units total) whose exact semantics
  (2nd UV set? morph deltas? compressed positions?) is **OPEN**.
- The 58-record count (58) matches the 58 heuristic strips, but record
  counts do NOT match strip vertex counts (6/58 positional match), so the
  table is not a 1:1 strip list for the skin-batch mesh. It may describe a
  second mesh or a different attribute layer.

## Open

- Payload (u16,0) exact semantics; u1 semantics; b8 exact meaning;
  material-table linkage; which mesh the 58 records draw.
