# YOBJ DOL Vertex Decoder — Lane (a2) RE Report (2026-10-16)

**Worker:** lane (a2) DOL VERTEX-DECODER RE, branch `lane/dol-yobj-decoder`
**Goal:** Find the YOBJ vertex decoder in main.dol; deliver `decode_yobj_verts`
         or precise decoder pseudocode.
**Result:** DOL extracted and loader reverse-engineered. s16x3 batches proven
         to be triangle-strip positions (own-eyes verified coherent strips).
         Full `decode_yobj_verts` delivered for positions; skinning assembly
         (batch→bone mapping) and Table1/Table2 strip boundaries remain open.

---

## 1. main.dol acquisition

`//sys/main.dol` is **not** in the release ISO's FST (the ISO was rebuilt
without a `sys/` directory; the boot header's `dol_offset=0x1F7000` points
to garbage). The DOL was located by scanning for the file-type table:

- Lane (a) reported the table at "DOL offset 0x30B2B0". The DOL base on the
  ISO is **0x1F700** (not 0x1F7000): table at ISO `0x1F700 + 0x30B2B0 = 0x32A9B0`,
  verified to contain `POF0→1, YOBJ→2, YANM→3, POFE→-2, DUMY→-1`.
- DOL header at ISO 0x1F700 parses correctly (7 text + 11 data sections).
- DOL file size: 0x3437C0 (3.26 MB). Extracted to
  `teardown/wwe-wrestlemania-xix/work/dol-re/main.dol` via
  `tools/wmxix_range_iso.py` (HTTP Range reads).
- Section map (file off → vaddr):
  - text0: 0x100 → 0x80003100 (0x25C0)
  - text1: 0x26C0 → 0x8001E5C0 (0x2BD440)
  - data5: 0x2EAE40 → 0x802EDE40 (0x519C0) — contains file-type table
  - Table vaddr: **0x8030E2B0** (0x802EDE40 + (0x30B2B0 - 0x2EAE40)) ✓

## 2. XREFs to the file-type table

The table is accessed via `lis rX, 0x8031` + `addi rY, rX, -0x1D58`
(= 0x8030E2A8, table base). 12 code sites found, clustered at
0x8007A758–0x8007BB04. Two loader functions:

### 2a. Loader A — `0x8007A71C` (file walker + POF0 relocator)

```
r23 = file_data; r24, r25, r26 = out params; r27 = base_addr
r31 = 0x8030E2A8 (table base)
r26 = [r26] (deref)

// get type id of first section:
for i in 0..[r13-0x7DE0]-1:          // [r13-0x7DE0] = table entry count (global)
    if memcmp(file_magic, table[i].magic, 4) == 0:
        id = table[i].id; break

// walk sections:
loop:
    r29 = [r30+4]                     // section size
    id = table_lookup([r30])          // re-scan table for this section magic
    if id == -1: r30 += r29 + 8; continue   // DUMY: skip
    if id == -2: ... finalize ...     // POFE: end marker
    if id == 1:                       // POF0: apply relocations
        r3 = r30 + 8                  // reloc data start
        r4 = r27                      // base address to add
        r7 = r3 + [r30+4]             // end
        while r3 < r7:
            b = *r3; top2 = (b >> 6) & 3
            if top2 == 1:             // 0x40: 1-byte + 6-bit offset
                off = ((b & 0x3F) << 2)
                r3 += 1
                *(u32*)(r4 + off) += r27
            elif top2 == 2:           // 0x80: 2-byte offset
                off = (u16 BE at r3+1) << 2
                r3 += 2
                *(u32*)(r4 + off) += r27
            elif top2 == 3:           // 0xC0: 4-byte offset
                off = (u32 BE at r3+1) << 2
                r3 += 4
                *(u32*)(r4 + off) += r27
            else:                     // 0x00: skip 1 byte
                r3 += 1
```

This is the classic GameCube POF0 relocation: the file contains
base-relative offsets that get fixed up to absolute pointers by adding
the load base. **After loading, YOBJ header fields (e.g., +0x60 batch
table offset) are absolute pointers, not file offsets.**

### 2b. Loader B — `0x8007AACC` (section allocator + copier)

For each section (skipping id == -1):
```
size = [section+4]
buf = alloc(0, size)                  // via 0x802768A4
memmove(buf, section+8, size)         // via 0x800055CC (memmove!)
if id == 1: apply POF0 relocations    // same loop as Loader A
```

`0x800055CC` is just `memmove` (verified by disassembly). The YOBJ
section data is copied to a heap buffer, then POF0-relocated in place.

## 3. Vertex position encoding: SOLVED (s16x3 triangle strips)

The skin-batch s16x3 values **are positions**. Proof:

- Batch 1 (72 verts) verts 35–62 form a coherent ribbon mesh when
  triangulated as a triangle strip (own-eyes verified;
  `/tmp/strip_proper.png`). Even/odd indices form the two rails.
- Per-batch point clouds show structured body-part shapes
  (`/tmp/pts_test.png`, `/tmp/per_batch2.png`).
- Scale is s16 / 64 (consistent with GX s16 vertices + 6 frac bits,
  and with the skeleton's unit scale).

The "fragmentation" reported by lane (a) was caused by:
1. Rendering batches as points or with wrong triangulation (not strips).
2. The batches being in bone-local space (not yet assembled).

**Decode:** `verts_float = s16x3 / 64.0`. Triangulate each batch as a
triangle strip in vertex order, splitting at jumps > 1000 raw units
(heuristic; true boundaries from Table1/Table2 not yet decoded).

Delivered: `tools/yobj_vertex_decode.py` with `decode_yobj_verts(ymg_bytes)`
returning `{'batches': [...], 'verts_all': (606,3) float32,
'tris_all': (T,3) int32}`.

## 4. What remains open

### 4a. Strip restart boundaries (Table1/Table2)
Batches contain multiple strips concatenated. The 1000-unit heuristic
works for most but is not exact. Table1 (58 records, 892 (u16,0) pairs)
and Table2 (52 records, 1026 (u16,u16) pairs) likely define the strip
boundaries and/or index buffers, but their semantics are not decoded.
The (u16,0) values (80, 195, 372, 3150…) do not map obviously to batch
vertex indices or the 4,412-entry gap pool.

### 4b. Batch→bone skinning assembly
The 13 batches (b0 = 0,1,2,3,4,5,6,7,8,9,10,12,11) are in bone-local
space and must be transformed by bone world matrices to assemble the
body. Tested mappings (b0→bone b0, b0→bone b0+1) produce clustered but
not anatomically correct assemblies. The b0 field's exact meaning
(bone index? part ID? palette index?) is unconfirmed. The DOL's
skinning loop (s16→float + matrix multiply) was not isolated from
500+ candidate functions.

### 4c. DOL vertex processing loop
The function that converts s16x3 batches to GX vertices (with the
0x4330 int→float pattern in a strip loop) was not identified. 1483
`lis *,0x4330` sites exist; the YOBJ-specific one needs the batch
table pointer (YOBJ+0x60) as context, which requires knowing the
YOBJ object's register allocation at the call site.

## 5. Next steps (for lane a or follow-up)

1. **Table1/Table2:** Correlate Table1 records with batches via the
   `b8` field and payload (u16,0) values. Try interpreting payloads as
   strip vertex counts or byte offsets into batch data.
2. **Bone mapping:** Search DOL for the batch descriptor reader
   (8-byte records: b0, count, offset). Find where b0 is used as an
   index (likely into a bone palette or part table).
3. **Skinning loop:** In the DOL, find the function that reads
   YOBJ+0x60 (batch table), loops over batches, and contains s16→float
   conversion (0x4330) + `fmadds` (matrix multiply). The matrix palette
   is likely 71 * 48 bytes (3x4 floats per bone).

## 6. Artifacts

- DOL: `teardown/wwe-wrestlemania-xix/work/dol-re/main.dol` (3.26 MB)
- Decoder: `teardown/wwe-wrestlemania-xix/tools/yobj_vertex_decode.py`
- This report: `teardown/wwe-wrestlemania-xix/docs/YOBJ-DOL-DECODER-REPORT.md`
- Renders: `/tmp/strip_proper.png` (coherent strip),
  `/tmp/per_batch2.png` (13 batches as strips),
  `/tmp/decode_verify.png` (606v/531t, overlapping — needs skinning)

## 7. Checkpoint

`~/workspace/agent-ops/checkpoints/wmxix-100-retail-dolre.json` →
status `done` (partial: positions solved, skinning open).
