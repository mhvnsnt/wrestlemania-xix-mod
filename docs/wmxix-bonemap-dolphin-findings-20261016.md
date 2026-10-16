# WMXIX Bonemap Investigation — Findings (2026-10-16)

## Critical Finding: GitHub Release Has Corrupt Asset

**Release `wmxix-iso-v1` (mhvnsnt/western-heart) asset `wmxix-500m.part_aa` (ID 638070444) is a byte-identical duplicate of `wmxix-500m.part_00`.**

- Verified: `cmp` confirms identical files; MD5 `e92c5227df7d62fd37ec82660d9a92e2` for both
- Fresh download from asset ID 638070444 produces the same duplicate content
- **The canonical store is corrupt** — ISO cannot be reassembled until owner re-uploads correct part_aa
- Local bad copy deleted per NO-DISK-STAGING (524MB freed)

## DOL Disassembly: Bonemap Mechanism Fully Documented

From `work/main.dol` (stripped .text section), found exact bonemap access:

**Bonemap loads (2 hits):**
- File offset `0x5d438`: `lbzx r24, r19, r24` (Path 1: single bone)
- File offset `0x5d4bc`: `lbzx r24, r19, r24` (Path 2: multi-bone)

**Bonemap pointer source:**
- `0x5d3c4`: `lwz r19, 4(r4)` — r19 (bonemap base) loaded from runtime struct at r4+4
- r4 comes from `lwz r4, 0xc(r31)` — field in context struct
- **The bonemap is runtime-constructed**, not a static DOL table

**Draw record format (16 bytes), from disassembly:**
```
[0]: file bone ID 0 (byte)
[1]: file bone ID 1 (byte)
[2]: file bone ID 2 (byte)
[3]: variant (1 = single bone, else multi-bone)
[4:8]: vertex count (u32)
[8:12]: weight stream pointer (u32, multi-bone only)
[0xC]: u8 (multiplied by 0xC)
[0xD]: u8 (if non-zero, triggers setup)
```

**Bone encoding:**
- Path 1 (variant==1): `bone = bonemap[rec[0]] + 1` (signed byte, then +1)
- Path 2 (variant!=1): `bone = ((bonemap[rec[2]]+1)<<16 if variant!=3) | ((bonemap[rec[1]]+1)<<8) | (bonemap[rec[0]]+1)`

**Runtime vertex format (28 bytes / 0x1C):**
- [0:12]: 6× s16 (position XYZ + normal XYZ, scaled 1/64)
- [0xC:0x10]: bone_u32 (packed bone indices)
- [0x10:0x14]: weights (0 for single-bone, from stream for multi)
- [0x14:0x1C]: 4× s16 (batch indices/counters)

## YCG File Analysis

`model__wrestler__000_0.ycg` (2,356 bytes):
- **NOT the bonemap** — contains 42 bone definition records (48 bytes each)
- Each record: 4-byte ID/hash + 32 bytes float data (bounding volumes/positions) + indices
- No 256-byte bonemap candidate found in YCG or any YMG file (strict search: ≥240/256 values in -1..69 range, ≥30 unique values)

## YMG Batch Structure (confirmed)

`000_0.ymg`:
- Batch table at file offset `0x7ca0` (pointer at 0x60)
- 13 valid batches (idx 0-12, note 12 before 11)
- 8-byte entries: `[0]=idx, [1]=c1, [2:4]=count, [4:8]=doff`
- Vertices: s16x3 BE, scale 1/64, at doff

## Why Dolphin Was Not Used

1. Dolphin not installed on VM; apt broken
2. Booting to a gameplay match headless (to hit skin kernel breakpoint) requires GUI menu navigation — infeasible without display
3. GDB stub approach would work but needs working Dolphin + game boot first
4. **Static analysis proved more productive** — bonemap mechanism fully documented without runtime

## Path Forward

1. **OWNER ACTION REQUIRED**: Re-upload correct `wmxix-500m.part_aa` to release `wmxix-iso-v1` (current asset is duplicate of part_00)
2. Once ISO is reassemblable: extract full filesystem, search for bonemap in additional files (may be in .atr, .yag, or other model metadata)
3. Alternative: The bonemap may be constructed by the model loader from YMG/YCG data — trace the loader function that builds the r4 runtime struct
4. If runtime dump is truly needed: run Dolphin with GUI on owner's machine or Colab, break at skin kernel, dump 256 bytes at r19

## Files Referenced
- DOL disassembly: `/tmp/wmxix-bonemap/` (ephemeral)
- YCG analysis: `.scratch/files/model__wrestler__000_0.ycg`
- Prior solver: `~/workspace/wmxix-skinning-solve/`
- This report: `~/workspace/agent-ops/wmxix-bonemap-dolphin-findings-20261016.md`

## Addendum 2026-10-16 ~12:10 EDT (attempt 6, subagent 027fce66)

### Corrected bonemap access addresses
Attempt-5 cited file offsets 0x5d438/0x5d4bc — off by 0x100. Verified via capstone scan of main.dol .text:
- `lwz r19, 4(r4)` occurs EXACTLY ONCE: VA **0x800793c4** (file 0x5d4c4). r4 = runtime model struct; +4 = bonemap base.
- `lbzx r24, r19, r24` (bonemap[file_bone] load): VA **0x80079438** (file 0x5d538) and VA **0x800794bc** (file 0x5d5bc).
- DOL section map: .text t1 file 0x26c0 -> VA 0x8001e5c0 (size 0x2bd440). VA = 0x8001e5c0 + (fileoff - 0x26c0).
- Skin kernel VAs from prior work map to: 0x800ABF8C -> file 0x9008c; 0x800AC040 -> file 0x90140; 0x800AC1D4 -> file 0x902d4.

### Dolphin headless feasibility (measured, not guessed)
- CPU: 2 cores, AVX2/SSE4.2 (JIT-capable). RAM: 7GB total / ~2GB available (tight). Disk: 12.4GB free (enough for transient 1.46GB ISO + extraction). Xvfb + Mesa present.
- apt: `dolphin-emu` not locatable (no universe/PPA); not installed. An AppImage could theoretically run under Xvfb.
- HARD BLOCKER even with a working ISO + Dolphin: **dolphin-emu-nogui exposes no scriptable breakpoint / memory-dump interface**. Breaking at 0x800ABF8C and dumping 256 bytes of RAM requires the Qt GUI debugger (Memory view + breakpoints) driven by a human, or a custom Dolphin build with a GDB-stub/dump hook. Headless "break and dump" is not a thing stock Dolphin can do.
- Realistic runtime-dump paths: (a) owner's GUI machine: boot ISO in Dolphin-Qt, debugger breakpoint at 0x800ABF8C, dump 256B at r19 (bonemap) + r4 struct; (b) patch the DOL's loader to copy the bonemap somewhere observable — needs the loader traced first anyway.
- CONCLUSION: static trace of the loader that builds the r4 struct (child subagent dispatched 2026-10-16 ~12:10 EDT) is the tractable path; Dolphin runtime dump is the fallback and needs a GUI machine + the full ISO.

### ISO status
- GitHub release wmxix-iso-v1 part_aa (ID 638070444) UNCHANGED (updatedAt 2026-10-13T19:51:28Z) = still the corrupt duplicate of part_00. Fresh re-download in progress to confirm with current evidence before reassembly is attempted.
