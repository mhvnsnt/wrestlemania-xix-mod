# WMXIX YMG Batch→Bone Trace — Loader Hunt & Empirical Findings (2026-10-16)

**Branch:** `lane/skinning-assembly-100-retail`  
**DOL:** `teardown/wwe-wrestlemania-xix/work/dol-re/main.dol`  
**Status:** Loader code path NOT located via static analysis. Major new structural findings documented. Coherent render NOT achieved.

---

## 1. Proven: Consumer draw-record format (refined)

Function `0x80078d6c` (file `0x5ce6c`–`0x5e520`), fully disassembled:

**Outer loop** walks 12-byte structs (`r4 += 0xc`). Per struct:
- `r8 = struct[0]` (sub-record ptr, 0x30-byte records)
- `r19 = struct[4]` = bonemap base (`lwz r19,4(r4)` at `0x800793c4` — ONLY bonemap load in .text)
- `r10 = struct[0][0x14]` = **16-byte draw-record cursor**
- `r11 = struct[0][5]` (u8) = draw-record count
- `r20 = struct[0][0xc]` = source vertex byte cursor

**16-byte draw record layout** (from `0x800793ec`–`0x80079578`):
| Offset | Field |
|---|---|
| [0] | file_bone_id_0 (single-bone path: `lbz 0(r10)`) |
| [1] | file_bone_id_1 (multi-bone) |
| [2] | file_bone_id_2 (multi-bone, if variant != 3) |
| [3] | variant: 1 = single-bone, else multi-bone (3 = 2-bone) |
| [4:8] | u32 vertex count (`r23`) |
| [8:12] | u32 weight-stream pointer (multi-bone only) |
| [0xc] | u8: source verts to skip (`r20 += rec[0xc]*12`) |
| [0xd] | u8: if nonzero, resync src cursor from `r20` |

**Bone formula:** `runtime_bone = (s8)bonemap[file_bone_id] + 1` (single); multi packs `((b2+1)<<16)|((b1+1)<<8)|(b0+1)`.

**28-byte runtime vertex** (output, `0x1c` stride):
- `[0:12]`: 6× s16 (pos XYZ + normal XYZ, copied verbatim from source)
- `[0xc:0x10]`: u32 packed bone indices
- `[0x10:0x14]`: u32 weights (0 for single-bone, from stream for multi)
- `[0x14]`: u16 entry index | `[0x16]`: u16 running vert counter | `[0x18]`: entry idx again | `[0x1a]`: counter again

**0x30-byte sub-record layout** (from constructor Loop 4 + consumer):
- `[0x4]`: flag byte (filter bits: `&0x1c==0`, `&0x03==0x03`, plus bit-6 vs `r18` mode)
- `[0x5]`: u8 draw-record count
- `[0xc]`: u32 src vertex cursor (bytes)
- `[0x14]`: ptr to 16-byte draw records

---

## 2. NEW: YCG→YMG bone correspondence via name hashes (PROVEN)

The DOL's `0x80083408` name-hash is (from disassembly `0x800834c4`–`0x800834e4`):
```
h = 0
for byte in name (NUL-terminated, NUL *excluded*):
    h = ((h >> 25) ^ ((h << 7) | byte)) & 0xFFFFFFFF   # = rol7(h) ^ byte
```

Applying this to YMG bone names and matching against YCG record hashes gives a **perfect 21/21 match** (all unique YCG hashes hit):

| YCG idx | YMG bone | YMG idx |
|---|---|---|
| 0 | Bip Head | 6 |
| 1 | Bip Neck | 5 |
| 2 | Bip R Hand | 23 |
| 3,4,5 | Bip R Forearm | 22 |
| 6,7,8 | Bip R UpperArm | 20 |
| 9 | Bip R Clavicle | 19 |
| 10 | Bip L Hand | 44 |
| 11,12,13 | Bip L Forearm | 43 |
| 14,15,16 | Bip L UpperArm | 41 |
| 17 | Bip L Clavicle | 40 |
| 18,19 | Bip Spine1 | 4 |
| 20 | Bip R Toe0 | 65 |
| 21,22 | Bip R Foot | 64 |
| 23,24,25 | Bip R Calf | 63 |
| 26,27,28 | Bip R Thigh | 61 |
| 29 | Bip L Toe0 | 70 |
| 30,31 | Bip L Foot | 69 |
| 32,33,34 | Bip L Calf | 68 |
| 35,36,37 | Bip L Thigh | 66 |
| 38,39 | Bip Spine | 3 |
| 40,41 | Bip Pelvis | 2 |

With the 42-byte bonemap `[0,1,2,3,3,3,4,4,4,5,6,7,7,7,8,8,8,9,10,10,11,12,12,13,13,13,14,14,14,15,16,16,17,17,17,18,18,18,19,19,20,20]`, runtime bone = bonemap[YCG]+1 gives runtime 1=Bip Head … runtime 21=Bip Pelvis.

**Implication:** the YCG duplicates are per-bone *segments* (e.g., 3 forearm segments with same hash, different positions). The 21 unique = the skinned joints.

---

## 3. NEW: Batch vertex data is s16x6 (12 B/vert), not s16x3

`yobj_decode.py` and prior docs read batches as s16x3 (6 B/vert). **Wrong.** Reading the face batch as s16x3 gives alternating Z (12.3/24.3); as **s16x6 (pos.xyz + nrm.xyz, 12 B/vert)** the positions are smooth: `(216,276,786)→(200,48,787)→(192,16,791)`.

The consumer copies **6× s16** per source vert (`lha` ×6, 12-byte stride: `addi r3,r3,0xc`), confirming the source is 12 B/vert. The loader therefore feeds 12 B/vert source data (or the YMG batch data is natively 12 B/vert).

Batch table (file order, `@0x7ca0`, 8-B recs `[idx][cnt8][cnt16][doff]`; doff from base `0x80`):
`idx:count = 0:72, 1:65, 2:49, 3:120, 4:17, 5:50, 6:15, 7:23, 8:72, 9:102, 10:4, 12:13, 11:4` (note 12 before 11).

---

## 4. NEW: 13 batches ↔ 13 body-part texture names (via idx)

Texture name table `@0x10574` in order: `hhh_body, hhh_arm, hhh_hand, hhh_waists, hhh_l_leg, hhh_knee, hhh_foot, face, head_back, eye, head_top, mouth, tooth` (13). Batch `idx` (0–12) maps 1:1 in order (file-order swap of idx 11/12 = draw-order, not a mismatch).

---

## 5. NEW: 'zyx' euler order gives anatomically plausible YMG skeleton

YMG bone slot (64 B): `[0:8]=?` `[8:24]=name` `[24:28]=parent` `[28:40]=pos[3]` `[40:52]=euler[3]` `[52:64]=?`. FK with `R = Rz@Ry@Rx` ('zyx') yields plausible bone lengths: UArm→Forearm 0.47 m, Forearm→Hand 0.41 m, Thigh→Calf 0.70 m, Neck→Head 0.21 m. Other orders give garbage. Skeleton renders as recognizable (lying-down) humanoid.

---

## 6. Loader hunt — what was tried

- **0x7CA0 readers:** cannot hardcode (file-specific). Searched for `lwz *,0x60(*)` (YMG+0x60 = batch-table ptr): 1095 hits, too generic. `lwz 0x60` + `add` (offset→ptr) pattern: 0 hits.
- **YMG header multi-offset (0x10/0x14/0x5c/0x60) same-base:** 0 functions (with strict chunking); loose 0x10/0x14 search: thousands of hits.
- **String refs** to `model/wrestler/%03d_%d.ymg` (`0x802deb90`): found via `lis 0x802d` + `addi -0x1470`, but xrefs landed in bulk `bdnz` memcpy loops, not the parser. No pointer table found.
- **0x30-stride writer** (sub-record builder): only hits are stack adjusts and the constructor's own read loop.
- **Draw-record writer** (16-B records with `[3]=variant`): no distinctive write pattern located.
- **Callers of constructor `0x80080170`:** `0x8002d9b4` (entry array at `[0x110(r29)]`), `0x80045df0`, `0x8007c7d8` (global `0x802d1428`). The 0x30 sub-record list is walked from `[0(r29)]` via `[4]` chain; `r29`'s origin not traced.
- **Skin kernels:** `0x800ABF8C`/`0x800AC040`/`0x800AC1D4` are mid-function sample points; the containing functions (`0x800ABEE4`, `0x800ABFB0`, `0x800AC08C`) are small malloc/free wrappers, NOT the kernels. Actual skin math not located.

**Capstone gotcha (for future):** capstone 5.0.7 *stops* (not skips) on paired-single (`psq_st`) unless `md.skipdata = True`.

---

## 7. Key hypothesis (UNPROVEN): file_bone_id = YMG bone index

Arguments:
- YMG has 71 unique-named bones → Path-B dedup gives 71-byte identity bonemap; `file_bone_id` ∈ [0,70] indexes it directly.
- Facial/detail bones (lips, teeth, eyes: YMG 7–18) exist ONLY in YMG, not YCG. Head batches (`face`, `eye`, `mouth`, `tooth`) need them for correct skinning → the draw records must address YMG bones, not the 21 YCG joints.
- The proven 42-byte YCG bonemap is real but may serve a different entry/model type (3 constructor call sites).

Against:
- No DOL code found that builds the 71-byte map or the draw records from YMG batches.
- Empirical renders with hypothesized body-part→bone mapping (head parts→Bip Head etc.) using 'zyx' matrices + s16x6 verts did NOT yield a coherent mesh (clusters form near bones but don't assemble).

## 8. What's needed next

1. **Locate the YMG loader**: trace from DVD/file-load of `model/wrestler/%03d_%d.ymg` (not via string xrefs — try breakpoint-style: find the function that calls the file-read helper `0x802baf08` with a ymg path, or search for the batch-table 8-byte record *read* pattern `lbz 1(rX)` + `lwz 4(rX)` + `addi rX,8` in YMG-context functions).
2. **OR runtime dump**: Dolphin + GUI on owner's machine, break at `0x800793c4` (`lwz r19,4(r4)`), dump `r19` (bonemap, 71 vs 42 bytes tells YMG vs YCG) and the draw records at `r10`.
3. **OR empirical brute-force**: using 'zyx' matrices + s16x6 verts (both now known-good), grid-search batch→YMG-bone assignments with a silhouette/coherence score; the facial bones (7–18) must be in the candidate set for head batches.

## 9. Lead: Table1.b8 as bone index (unexplored)

Table1 records have `b8` in 3–70 (valid YMG bone range). Rec 0 (`cnt=128`) appears to be a group header for recs 1–7 (counts 44+14+14+8+4+38+6=128, shared `u0=0x61c0`). If `b8` is a bone index, Table1 groups split into per-bone draw records. BUT: Table1's 892 payload units ≠ 606 batch verts, and its payloads index the `0x80` vertex pool (23 KB region), not the batch pool — Table1 is likely a *separate* mesh system, not the batch→draw path. Worth verifying before discarding.

## Files (this lane)

- `teardown/wwe-wrestlemania-xix/work/dol-analysis/` — scripts (`dol.py` harness, `s_*.py` searches, `fk_test*.py`, `body_*.py`, `skel_test.py`, `align_test.py`, `head_only.py`) and renders (`skeleton_orders.png`, `main21.png`, `body_zyx.png`, `head_only.png`, `align_test.png`, `raw_s16x6.png`, `body_transonly.png`, `body_s16x6.png`).
- Disassembly dumps: `func_80081ec4.txt`, `callers.txt`, `skin1.txt` (+ `constructor.txt`, `consumer.txt` in earlier `/tmp`, since wiped — see scripts to regenerate).

## Raw YMG/YCG paths (not in repo)

- `/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/wwe-wrestlemania-xix/.scratch/files/model__wrestler__000_0.ymg`
- `.../model__wrestler__000_0.ycg`
