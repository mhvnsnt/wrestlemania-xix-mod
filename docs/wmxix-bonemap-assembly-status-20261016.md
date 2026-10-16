# WMXIX Bonemap: Construction SOLVED, YMG Batch→Bone Mapping Still Open (2026-10-16)

## What was PROVEN (DOL disassembly, verified by execution)

The runtime bonemap constructor was found and fully traced by subagent 3f67d6e5:

- **Consumer**: `0x80078d6c` (file 0x5ce6c–0x5e520). `lwz r19,4(r4)` at VA
  `0x800793c4` is the ONLY bonemap load in `.text` (byte-scan verified).
  `lbzx r24,r19,r24` at `0x80079438`/`0x800794bc`. Formula:
  `runtime_bone = (s8)bonemap[file_bone_id] + 1`.
- **Loader**: `0x80080170` (file 0x64270–0x65ef4). Per entry: `bm = malloc(bone_count)`.
  - Path A (`entry_count==1`): identity `bm[i]=i`.
  - Path B: dedup by 16-byte key, `bm[i]` = first-occurrence index.
  - `stw r10,4(r4)` at `0x80081318` stores bonemap ptr into 12-byte struct (verified).
- **Implementation**: `~/workspace/agent-ops/wmxix-bonemap-work/build_bonemap.py`.
  Against `model__wrestler__000_0.ycg` (42 recs × 56B): 42-byte map, 21 distinct
  values 0–20, dense. All sanity checks pass.
- **Corrections**: bonemap is `malloc(bone_count)`, NOT 256 bytes. YCG records are
  56 bytes (4+42×56=2356 exact), not 48. Skin-kernel VAs are mid-function.
- Full trace: `~/workspace/agent-ops/wmxix-bonemap-constructor-trace-20261016.md`.

I independently verified: `stw r10,4(r4)` at 0x80081318, the unrolled fill at
0x800802f4, and both function prologues via capstone. The structural claims hold.

## What remains OPEN (blocking mesh assembly)

The YMG (`model__wrestler__000_0.ymg`) has **71 bones** (all unique names) and
**13 batches** (606 verts, 8-byte records at 0x7CA0). The YCG-derived bonemap
(42→21) does NOT directly give the YMG batch→bone mapping. Tested hypotheses
(all rendered, all failed to produce a coherent head):

| Hypothesis | Mapping | Result |
|---|---|---|
| M1 | batch idx → bonemap_42[idx]+1 → YMG bone 1–8 | Scattered garbage |
| M2 | batch idx → YMG bone (6+idx) [head bones] | Scattered garbage |
| M3 | batch idx → YMG bone idx (direct) | Scattered garbage |
| Translation-only | all batches → Bip Head world pos | Overlapping blob, not a head |
| No transform | raw v/64 | Diffuse 30-unit blob, not head-shaped |

The point cloud (no transform) is not head-shaped, indicating the batches are
not in a shared head-local space OR the vertex grouping needs per-batch bone
transforms that I have not found.

## Key structural insight

The YMG embeds its own 71-bone skeleton (unique names → any name-dedup bonemap
would be identity). The YCG's 42 records (21 unique hashes) are the ANIMATION
rig. The DOL's 42→21 bonemap is real, but it maps YCG anim-joint indices, not
YMG batch indices. The YMG batch→bone linkage (whether via draw records, Table1,
or another structure) was not located in the DOL trace.

## Next steps

1. Trace the LOADER's draw-record construction (how 8-byte YMG batch records
   become 28-byte runtime draw records, and where `file_bone_id` comes from).
2. OR: locate the YMG batch→bone table in the DOL (search for 0x7CA0 readers).
3. OR: empirical search over batch→bone assignments using geometric coherence
   (batch centroids should land near bone positions).

## Files

- `~/workspace/agent-ops/wmxix-bonemap-constructor-trace-20261016.md` (child's full trace)
- `~/workspace/agent-ops/wmxix-bonemap-work/build_bonemap.py` (proven implementation)
- `/tmp/wmxix_asm/` (render attempts: M1_bonemap.png, M2_head6.png, M3_direct.png,
  all_to_head.png, raw_notransform.png, pointcloud.png, batches_local.png)
