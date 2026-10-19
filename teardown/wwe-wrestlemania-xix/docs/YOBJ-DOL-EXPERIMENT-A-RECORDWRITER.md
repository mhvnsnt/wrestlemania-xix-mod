# YOBJ DOL Experiment A — Record Writer Hunt (2026-10-15)

**Worker:** wmxix-yobj-dol-recordwriter (subagent)
**Target:** Find the function that WRITES the 16-byte runtime draw records
consumed by the vertex builder @0x80078C6C, in DOL region 0x80072000–0x80074000.
**Result:** The hypothesized "pack Table1 fields" writer was NOT found in
0x80072000–0x80074000. Instead the full runtime record pipeline was mapped:
descriptor builder **0x80087C90**, record processor **0x8008453C**, and the
vertex builder **0x80078C6C** itself. The 16-byte records live at
**[descriptor+0x14]** (heap buffer allocated by 0x80087C90); the 12-byte source
verts are at **[descriptor+0x0C]**. The precise writer of the 16-byte record
*content* into [descriptor+0x14] remains unisolated (see §5).

All addresses are DOL virtual addresses (main.dol, text @0x8001E5C0).

---

## 1. PROVEN: 0x80087C90 — mesh descriptor builder (764 bytes)

Called per-mesh from the render setup @0x80080070 (loop at 0x80080F3C,
`bl 0x80087c90` @0x80081010). Fills a **0x2DC-byte descriptor** at
`[r30+0x118] + mesh*0x2DC`.

Register args (from call site 0x80080FF8–0x80081010):
`r3=dst, r4=r30, r5=r21 (mesh-group node), r6=r24=[r21+4]+mesh*0x30,
r7=bonemap value, r8=flag byte [r30+0x17B], r9=r28`.

Descriptor fields written (0x80087C90+offset):
| offset | value | note |
|---|---|---|
| 0x00 | r4 (arg2) | |
| 0x04 | r5 (arg3 = r21) | |
| 0x08 | bit0 of [r6+4] | |
| 0x0C | r6 = **[r21+4]+mesh*0x30** | **source-verts/record header ptr** |
| 0x10 | alloc([0x20]) | heap buf A, cleared |
| 0x14 | alloc([0x20]) | heap buf B, cleared — **the 16-byte records live here** |
| 0x20 | size = round32([r6+0]*12) [+ round32(extra)] | [r6+0] = u16 count |
| 0x104 | 0 | |
| 0x105 | bit2 of [r6+4] | |
| 0x106 | 0 | |
| 0x109 | r8 (flag) | |
| 0x10C | r9 (arg7) | |
| 0x110 | r7 (**bonemap** value) | builder does `lbzx` through `[desc+0x110]`-derived base |
| 0x120 | alloc(0xA0) | |

Key: `[0x0C]` points at a **0x30-byte per-mesh header** (`[r21+4]+mesh*0x30`).

## 2. PROVEN: 0x8008453C — 16-byte record processor (1648 bytes)

Called from three sites: `0x80087E24` (inside 0x80087C90, r4=-1),
`0x8007E108` (loop in 0x8007DFDC, r4=0x10, dst=[r30+0x118]+mesh*0x2DC),
`0x80084F74` (r4=-1). Guards: `[desc+0]!=0`, `[desc+8]!=0`,
`[desc+0x104]==0`, `([r6+4] & r4)!=0`.

It reads **source** 16-byte records from:
- `r25 = [[desc+0x0C]+0x14]` (0x800845C8: `lwz r25, 0x14(r4)`, r4=[desc+0xC])
- count `r26 = [[desc+0x0C]+5]` (u8, 0x80084630)
- `r25 += 0x10` per record (0x80084AD0), loop `bne 0x80084784`

Per-record dispatch on `record[3]` (0x80084794):
- type 0 or ≥4 → skip (0x80084958)
- type 1 → 0x800847BC → skin kernel **0x800ABF8C** (single bone via bonemap)
- type 2 → 0x80084818 → skin kernel **0x800AC040** (two bones)
- type 3 → 0x800848B0 → skin kernel **0x800AC1D4** (three bones)

Bone indices are bonemap-mapped (`lbzx rX, [desc+0x110], rY`, e.g.
0x800847D8, 0x80084834) then `mulli ×0x30` (bone-matrix stride), and the
kernels (0x800ABF8C/0x800AC040/0x800AC1D4/0x800AC3E8/0x800AC4EC/0x800AC6D0)
are paired-singles vertex skinning routines. It also copies 12-byte verts
from `[[desc+0xC]+0x0C]` via `bl 0x8027730c` (0x80084698–0x800846A8,
size = `record[0xC]*12`).

**This function READS the 16-byte records; it does not write them.**

## 3. PROVEN: builder 0x80078C6C record-source identity (correction)

Re-examination of the builder's record loop (0x800792B4–0x800794A0):
- `r4` = 12-byte entry array, `addi r4, r4, 0xC` per mesh (0x80079480)
- `r8 = [r4+0]` (entry[0] = descriptor/node)
- `r19 = [r4+4]` (bonemap)
- **`r10 = [r8+0x14]`** — the 16-byte records = **[descriptor+0x14]**,
  i.e. heap buffer B allocated by 0x80087C90. `addi r10, r10, 0x10`
  per record (0x80079470).
- `r20 = [r8+0xC]` — the 12-byte source verts = **[descriptor+0x0C]**
  = `[r21+4]+mesh*0x30` (set by 0x80087C90).

The entries are built at 0x80081204–0x80081220
(`stw r9,0(r4)` / `stw bonemap,4(r4)` / `stw r0,8(r4)`, `addi r4,r4,0xC`).

## 4. The 0x30-byte per-mesh header (runtime-built, NOT in file)

`r6 = [r21+4] + mesh*0x30`. Fields consumed:
| offset | use |
|---|---|
| 0x00 | u16 count (0x80087D18: `lhz`; sizes the [0x20] alloc as count*12) |
| 0x04 | u8 flags (ANDed with arg2 mask) |
| 0x05 | u8 = number of 16-byte source records |
| 0x0C | u32 → 12-byte vert source (copied by 0x8008453C) |
| 0x14 | 16-byte **source** records × [0x05] (read by 0x8008453C) |

A byte-exact file scan of 000_0.ymg for this header shape
(u16 count 4–200, [5] in 1–20, record[3] in 1–3) found **zero candidates** —
the headers are constructed at runtime, not mapped from the file.

## 5. PRECISE NEGATIVE RESULT — the record writer

The task hypothesized a writer in **0x80072000–0x80074000** packing file
Table1 fields (`b8→[0]`, `variant→[3]`, `count→[4]`, `u0→[8]`) into the
16-byte runtime records. **No such function exists in that region:**

- A store-cluster scan (stb@0,1,2,3 + stw@4 + stw@8 + stb@12,13 from a
  common base within 80 insns) over 0x80072000–0x80074000: **no hits**.
- `addi _,_,0x10` (record-pointer advance) in 0x80072000–0x80078000: only
  stack adjustments and the unrelated skin-record copier at
  0x800759C0/0x80075B60 (src += 0x10, dst += 0x1C).
- No `slwi ×16` / `mulli ×16` anywhere in 0x80072000–0x80078000.
- The region is C++ object setup (allocs of 0x1C/0x20/0x50/0x780/0xD0/0x13C,
  string copies, vtable calls) — no 16-byte record writes.
- The only stb@0xC→stb@0xD pair in the wider area (0x80075970→0x80075978)
  is the skin-record copier writing **0x1C-byte** records (bone quads at
  +0xC/+0x10/+0x14), not the 16-byte draw records.

The actual 16-byte records consumed by the builder live in the heap buffer
at **[descriptor+0x14]** (allocated, cleared by 0x80087C90). Their content
writer was **not isolated** in this pass. Leading hypothesis: they are
written by the skinning pipeline driven by 0x8008453C (its kernels write
to stack temps at [r1+8/0x10/0x14], advanced per record), or by an
unexamined callee of 0x80087C90/0x8007DFDC.

**Next experiment (B-prime, static):** instrument-target search for stores
into the `[desc+0x14]` buffer: find all `lwz rX, 0x14(rY)` sites where rY
is a 0x2DC-descriptor, then check the surrounding code for the 16-byte
record fill loop. **Experiment B (dynamic, decisive):** Dolphin break at
0x80078C6C, dump `[desc+0x14]` and `[desc+0x0C]`, correlate with file
offsets — the file→record and file→vert mappings fall out immediately.

## 6. Bonemap note

The 256-byte bonemap base used by the builder (`lbzx r24, r19, r24` @
0x80079338 etc.) is `r19 = [entry+4]`, set at 0x80081218 from
`[[r30+0x160]+r6]` — the identity-map table built at 0x800801F4–0x80080270
(`stbx` fill of bytes 0..r15-1, gated on `[r30+0x12C]==1`). The
file-bone-id → runtime-bone-index remap values themselves are written by
0x80087C90's `[0x110] = r7` arg path; the table-fill loop was not traced
to a file source in this pass.

## 7. Files

- NEW `tools/dol/recwriter_scan.py` — store-cluster + memset + bl-size-arg
  scanner for the 16-byte record-writer signature (used; negative result
  documented above).
- This report: `docs/YOBJ-DOL-EXPERIMENT-A-RECORDWRITER.md`.
- No binaries, no .pyc, no game files touched. Branch
  `feat/ymg-skinning-decoder`, worktree
  `~/workspace/agent-ops/worktrees/wrestling-teardown`.

## 8. Measurements (all DOL virtual addresses)

| item | address | size |
|---|---|---|
| descriptor builder | 0x80087C90 | 764 B |
| record processor | 0x8008453C | 1648 B |
| vertex builder | 0x80078C6C | ~0x3D00 B |
| descriptor | [r30+0x118]+mesh*0x2DC | 0x2DC B |
| per-mesh header | [r21+4]+mesh*0x30 | 0x30 B |
| runtime record | [desc+0x14]+rec*0x10 | 16 B |
| source record | [[desc+0xC]+0x14]+rec*0x10 | 16 B |
| 12-byte verts | [desc+0x0C] = [r21+4]+mesh*0x30 | 12 B each |
| bonemap | [entry+4] (256 B) | via `lbzx` |
| record-proc call sites | 0x80087E24, 0x8007E108, 0x80084F74 | |
| builder's only caller | 0x800812C4 (in 0x80080070) | |
| 0x80080070 callers | 0x8002D8B4, 0x80045CF0, 0x8007C6D8 | |
