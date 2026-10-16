# WMXIX Runtime Bonemap Constructor — Static Trace (2026-10-16)

**DOL:** `/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/work/dol-re/main.dol`
(3,422,144 bytes). `.text` t1: file `0x26c0` → VA `0x8001e5c0`, size `0x2bd440`.
VA = `0x8001e5c0 + (fileoff − 0x26c0)`. Disassembled with capstone 5.0.7
(PPC32 BE). All claims below were verified by running code, not by pattern-guessing.

---

## 1. Key addresses (VA / file offset)

| What | VA | File offset |
|---|---|---|
| Bonemap consumer function start | `0x80078d6c` | `0x5ce6c` |
| Bonemap consumer function end (blr) | `0x8007a420` | `0x5e520` |
| `lwz r19, 4(r4)` — bonemap pointer load (ONLY ONE in .text, raw byte-scan verified) | `0x800793c4` | `0x5d4c4` |
| `lbzx r24, r19, r24` — bonemap index #1 | `0x80079438` | `0x5d538` |
| `lbzx r24, r19, r24` / `lbzx r8, r19, r8` — bonemap index #2 | `0x800794bc` / `0x800794c0` | `0x5d5bc` / `0x5d5c0` |
| Sole caller `bl 0x80078d6c` (raw byte-scan: exactly 1 hit in .text) | `0x800813c4` | `0x654c4` |
| **Bonemap constructor/loader function start** | `0x80080170` | `0x64270` |
| Bonemap constructor/loader function end (blr) | `0x80081df4` | `0x65ef4` |
| `stw r10, 4(r4)` — writes bonemap ptr into 12-byte runtime struct word+4 | `0x80081318` | `0x65418` |
| Path A identity fill loop (`stbx r3, r4, r3`, unrolled ×8) | `0x800802f4`–`0x80080398` | `0x643f4`–`0x64498` |
| Path B dedup loop (memcmp search + `stbx r15, r3, r17`) | `0x800805b8`–`0x800807bc` | `0x646b8`–`0x648bc` |
| Bone-name-hash helper `bl 0x80083408` | `0x80083408` | `0x67508` |
| Skin-kernel sample points (prior work) — **confirmed mid-function, not entries**: `0x800ABF8C` ∈ func `0x800ABEE4`, `0x800AC040` ∈ func `0x800ABFB0`, `0x800AC1D4` ∈ func `0x800AC08C` | — | — |
| YCG path format strings in DOL | — | `0x2dbbdd` (`model/wrestler/%03d_0.ycg`), `0x2dbb45` |

Callers of the loader `0x80080170` (raw byte-scan, 3 hits): `0x8002d9b4`, `0x80045df0`
(`bl` with `r5=0`), `0x8007c7d8` (arg2 = global `0x802e1428`).

---

## 2. What the consumer function does (0x80078d6c)

`0x80078d6c(r3=arg1, r4=arg2, r5=arg3)` — mesh skin/draw-record builder.
- `r31` = frame pointer; `8(r31)`/`0xc(r31)` = saved arg1/arg2; `r21` = arg3 (entry count).
- Outer loop (`0x800793ac`–`0x8007959c`) walks `r4` over an array of **12-byte runtime
  structs** (`addi r4, r4, 0xc`), `r7` = 0..arg3−1.
- Per struct: `r8 = struct[0]`; **`r19 = struct[4]` = bonemap base** (`0x800793c4`);
  `r10 = struct[0][0x14]` = draw-record cursor; records are 28 (`0x1c`) bytes.
- Single-bone path (`0x80079430`): `r24 = file_bone_id = lbz 0(r10)`;
  `r24 = bonemap[r24]` (`lbzx`); `extsb`; **`r24 += 1`** → runtime bone index.
- Multi-bone path (`0x800794b0`): same for bytes 0/1(/2), packed
  `((b2+1)<<16)|((b1+1)<<8)|(b0+1)`.
- The `+1` reserves runtime index 0 = "no bone". `extsb` means a stored byte
  ≥ 0x80 would sign-extend negative — stored values are small (see §4).

So: **runtime_bone = (s8)bonemap[file_bone_id] + 1**.

---

## 3. The constructor (0x80080170) — bonemap build algorithm

`0x80080170(r3=arg1/model, r4=arg2/entry-array, r5=arg3)`:

1. `entry_count = arg2[4]` → stored at `0x12c(arg1)`.
2. `table = malloc(entry_count * 4)` → `0x160(arg1)` — array of per-entry bonemap pointers.
3. **Path A — `entry_count == 1`** (`0x80080220`: `cmpwi r0,1 / bne PathB`):
   - `n = bone_count = entry[8]`; `data = entry[0xc]` (side call `0x80083408` builds name hashes).
   - `bm = malloc(n)`; `table[0] = bm`.
   - **Identity fill** (`0x800802f4`, unrolled ×8 + tail): `for i in 0..n-1: bm[i] = (u8)i`.
4. **Path B — `entry_count != 1`**:
   - Loop 1 (`0x800803b0`): per entry `e`: `bm_e = malloc(entry[e][8])` (or NULL if 0);
     `table[e] = bm_e`; accumulate `total_bones`.
   - `uniq = malloc(total_bones * 64)`; `nuniq = 0` (r26).
   - Loop 2/3 (`0x80080528`/`0x800805b8`): per entry `e`, per bone `i` in
     `0..entry[e][8]-1` (records at `entry[e][0xc]`, **0x40-byte stride**):
     - Linear search `s` in `0..nuniq-1`: `memcmp(uniq + s*0x40, bone_i, 0x10)` via
       `bl 0x802a6098` (`0x800805d4`); break on 0.
     - **`bm_e[i] = s`** (`stbx r15, r3, r17` @ `0x800805fc`) — match index, or
       `nuniq` if no match.
     - If no match: copy the 64-byte bone record into `uniq[nuniq]` (with a
       `[0x10]` fixup: if `bone[0x10] != -1`, resolve `bone[bone[0x10]]`'s 16-byte
       key against the unique table and store the hit index at `uniq[nuniq][0x10]`,
       else `-1`); `nuniq++`.
     - If match and `bone[0x30]` bit 30 (`0x40000000`) clear: refresh
       `uniq[s]` with the current record's 64 bytes, preserving `uniq[s][0x10]`.
   - Call `0x80083408(arg1, uniq, nuniq)` — builds bone-name hash table
     (hash = `rol7(h) ^ byte` over NUL-terminated names); then `free(uniq)`.
5. Loop 4 (`0x800811e0`–`0x80081350`): build the 12-byte runtime structs:
   `struct[0] = record_ptr`; **`struct[4] = table[e]`** (`0x80081318` — the store
   that fills the word the consumer later loads at `0x800793c4`); `struct[8] = r0`.
6. Call the consumer: `0x80078d6c([0x110(r16)], stack_buf, r19_struct_count)`.

### Pseudocode (exact)

```
# per entry e with bone_count N_e, bone records B_e[0..N_e-1] (64 bytes each):
bonemap_e = bytearray(N_e)
if entry_count == 1:                      # Path A
    for i in range(N_e): bonemap_e[i] = i
else:                                     # Path B
    uniq = []                             # list of 16-byte keys, first-occurrence order
    for i in range(N_e):
        key = B_e[i][0:16]
        s = next((s for s,k in enumerate(uniq) if k == key), None)
        if s is None:
            s = len(uniq); uniq.append(key)
        bonemap_e[i] = s
table[e] = bonemap_e                      # struct[4] points here
# consumer: runtime = int8(bonemap_e[file_id]) + 1
```

**Size correction:** the bonemap is `malloc(bone_count)` bytes — **not** 256 bytes.
It is *indexed* by a byte (`lbzx`), so file bone IDs must be `< bone_count`;
the "256-byte" figure in older notes conflated the index width with the buffer size.

---

## 4. Python implementation

`~/workspace/agent-ops/wmxix-bonemap-work/build_bonemap.py` —
`build_bonemap(ycg_bytes) -> bytes` implements the Path-B dedup exactly
(first-occurrence order, 16-byte key). Run against the real YCG:

- Input: `model__wrestler__000_0.ycg` (2,356 bytes).
- Output: **42 bytes**, values dense `0..20` → **21 distinct small values**,
  duplicates map to first occurrence:
  `[0,1,2,3,3,3,4,4,4,5,6,7,7,7,8,8,8,9,10,10,11,12,12,13,13,13,14,14,14,15,16,16,17,17,17,18,18,18,19,19,20,20]`
- Sanity checks pass (length == bone count, dense 0..N−1, no crashes).

---

## 5. YCG file structure (corrected)

Prior notes said "42 records × 48 bytes". **Wrong.** Verified:
`4 + 42*56 = 2356 = file size` exactly. Layout:

- `[0:4]` u32be bone count (42). (Bytes `[4:8]` previously read as a "magic"
  `0x099cd766` are actually **record 0's name hash** — there is no magic.)
- 42 × **56-byte** records: `[+0]` u32 name_hash, `[+4]` u32 field (values 0–5),
  `[+8]`/`[+12]` zero, `[+16:+56]` 40 bytes of transform floats.

Smoking gun for the dedup: only **21 unique name hashes** in 42 records
(e.g. `0x7ad45e02` ×3 at indices 3,4,5 with identical first 16 bytes but
different transforms). The loader's Path-B dedup exists precisely to merge these.

---

## 6. What remains uncertain (honest boundary)

1. **Path A vs Path B for YCG loads.** Which path a wrestler load takes depends on
   `entry_count = arg2[4]` (runtime value; one call site passes a global
   `0x802e1428`, another passes `[0x34(r26)]` with arg3=0). Path A yields identity
   (`bonemap[i]=i`); Path B yields the dedup. The duplicate hashes in the YCG
   prove the dedup is exercised somewhere, so Path B is the meaningful
   interpretation for skinned wrestler models — but the branch itself was not
   observed at runtime.
2. **YCG → 64-byte runtime record expansion.** The loader dedups 64-byte records
   (0x40 stride, 16-byte key at [0:16]); the exact code expanding the 56-byte YCG
   records into these was not located. `build_bonemap` uses `ycg_record[0:16]`
   as the key, inferred from the duplicate structure — if the runtime key layout
   differs, only the key slice needs to change; the dedup skeleton is exact.
3. **`0x800054e4` (memset) / `0x800055cc` (memcpy) / `0x802768a4` (malloc) /
   `0x802769a0` (free)** are identified by call signature
   (`dst,val,len` / `dst,src,len` / `heap,size`), not by disassembling them
   (they live outside the mapped .text t1).
4. Semantics of YCG record `[+4]` (0–5), bone record `[0x10]` (−1 or index) and
   `[0x30]` bit 30 are documented structurally only.
5. The 12-byte runtime structs' `[0]`/`[8]` fields and the `0x80083408` name-hash
   table's downstream use (animation retargeting?) were not traced further —
   out of scope for the bonemap.

## 7. Files

- Findings (this doc): `/home/hatch/workspace/agent-ops/wmxix-bonemap-constructor-trace-20261016.md`
- Implementation: `/home/hatch/workspace/agent-ops/wmxix-bonemap-work/build_bonemap.py`
- Analysis scripts/disasms: `/home/hatch/workspace/agent-ops/wmxix-bonemap-work/`
  (`analyze.py`, `func_80078d6c.txt`, `caller_80080170.txt`, `func_80083408.txt`)
