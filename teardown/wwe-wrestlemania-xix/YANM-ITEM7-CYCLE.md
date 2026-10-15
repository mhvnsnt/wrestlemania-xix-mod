# YANM Item-7 Cycle Results — Type-B decode, POF0/byte-ramp, ISO-incident recovery

Measured 2026-10-13 (watchdog continuation cycle, attempts=30 worker; probes:
`wwe-wrestlemania-xix/tools/yanm_typeb_decode.py`, `yanm_typeb_probe.py`,
`yanm_typeb_probe2.py`, `yanm_typeb_table.py`, `yanm_item3_pof0.py`,
`yanm_item3_byteramp2.py`, `wmxix_range_iso.py`, `wmxix_extract.py`;
committed locally as 67f1904 on `watchdog/wrestling-teardown-20261013`).
**Doc written post-hoc** by watchdog (worker was timeout-interrupted before
doc-write; `/tmp/wmxix_files` extraction dir was lost to /tmp cleanup —
all figures are re-runnable via the range-ISO tool; no new measurements
are claimed here that the worker did not record).

## ITEM 1 — ECD render test: NOT STARTED
Worker timed out before the render test (FK c200 variants with matplotlib
`view_init` from ECD yaw/pitch). Carries forward to next cycle. Needs
range-ISO re-extraction first (see ISO incident below).

## ITEM 2 — Type-B record decode: RESOLVED (structure), open (semantics)

### Dir-record layout (32B, 8 words), measured over the full `.yag` universe
A Type-B record is any dir record with `a != 0` and `(w28 >> 16) == 1`:

```
[+0 hash][+4 a][+8 w8][+12 w12][+16 X][+20 Y][+24 Z][+28 w28]
```

- **w8 == a+4, always** (every record, every clip). w8 is a redundant
  duplicate of the table pointer — not a second offset.
- **w12 == 0, always.** No flags, no length in w12.
- **w28 high-16 == 0x0001** (the Type-B discriminator). w28 low-16 is
  **NOT the table length** (rejected by direct measurement).

### X/Y/Z: static orientation payload (asin-encoded)
X/Y/Z are `s32`, interpreted as `2^31 * sin(θ)` — i.e. `θ = asin(X/2^31)`.
Measured: per-clip-**variant** (not per-hash-constant), and the decoded
angles draw from a **quantized preset vocabulary** ≈ {0, ±24, ±36, ±42} deg.
They are static within a clip — an orientation snapshot, not animation.
Cross-checks against known quantities (ycg offsets, ymg offsets): no match —
X/Y/Z do not encode offsets into any known table.

### a-offset table (the [a] pointer)
- 12-byte stride hypothesis: **WEAK** (autocorrelation at lag 12 ≈ lag 4;
  no consistent 12B structure). a-table structure is NOT a simple strided array.
- a-tables carry **POF0-tagged byte curves** (see Item 3) — the table is a
  byte-curve container, not a word table.
- **0C5BF279** (the per-wrestler detail record) is Type-B: its a-table is
  **per-wrestler-or-move** (V1/V2 string variants differ), and its X/Y/Z
  varies per clip+variant. Consistent with item-4/item-5 findings:
  0C5BF279 binds a model-side detail table to a clip-side variant.

## ITEM 3 — POF0 + byte-ramp vs ID-block: characterized, mapping still OPEN

### POF0 container
`POF0` = `'POF0'` + u32 length + bytes, present in **ALL 7 wrestler `.ymg`**
(per-wrestler, **168–268B**; u8 curves ranging 0x41–0x61 with >=0x80 markers).
POF0-tagged byte curves also appear in `.yag` Type-B a-tables — the same
container format on both the model side and the animation side.

### 168B byte region = 12 × 14B segments (000_0 measured)
- Segments **1–7: flat 0x44** (7 of 12 segments identity-flat) —
  "identity LUTs" hypothesis plausible: flat segments pass through.
- Segments **0, 8–11: active** (varying curves, >=0x80 markers).
- **remap-LUT hypothesis: PLAUSIBLE but unproven** — the 12-word ID block
  (record14 w08–w19) shows **no clear relation** to segment contents
  (per-segment top-value vs ID word: no correlation; cross-wrestler
  byte-region equality does not track ID-block equality).

### Remaining opens (carry to next cycle)
- ID-block word semantics (ruled out: yag tracks, ycg hashes, bone-table
  words, file offsets, bone-name hashes; leading hypothesis: driven-element
  IDs in mesh ID space).
- Which ID words route to which active segments (0/8–11).
- Whether flat-0x44 segments are literally identity LUTs.

## ISO INCIDENT + RECOVERY (major)

The local ISO (`WWE Wrestlemania XIX (USA).iso`) was **deleted from disk**
(the 18:18 worktree symlink `wwe-wrestlemania-xix/WWE Wrestlemania XIX (USA).iso`
is now dangling; future cycles must not assume it exists). Root causes under
investigation (disk-guardian cleanup at 93%→80% is the likely actor — disk
guardian is reminded in the cycle commit).

Meanwhile the western-heart GitHub release `wmxix-iso-v1` has a **stale part**:
`wmxix-500m.part_00` is a **byte-duplicate of `part_aa`** (both open with
`GW9E78`), and the release description's `cat part_*` instruction is **WRONG**.
Correct assembly order: **part_aa + part_ab + part_ac = 1,459,978,240 B**
(MD5 c13c47a5ed24a675545c99a15e44529d).

Recovery tool committed this cycle: `wwe-wrestlemania-xix/tools/wmxix_range_iso.py` —
range-reads the ISO over HTTPS from the release with an on-disk cache, exposing
a file-like object over `seek()/read()` so all existing tools work unchanged.
Total cache = only bytes actually touched (FST + requested files), KB/MB-scale —
safe at 80% disk. `wmxix_extract.py` re-extracts the needed `.yag`/`.ymg` set
into `WMXIX_FILES` via this reader. **Release `part_00` should be deleted and
the description corrected** (carries to a future browser/cleanup task).

## ITEM 4 — CAW .gci: SKIPPED (still needs parent Dolphin browser task with KNOWN CAW values)

## STOPPED HERE (next cycle)
- (a) ECD render test: FK `c200` variants, matplotlib `view_init` from ECD
  yaw/pitch (needs range-ISO re-extraction first — see above).
- (b) ID-block → segment routing; flat-0x44 identity-LUT proof.
- (c) X/Y/Z orientation semantics: what does the static preset encode
  (rest-pose delta? bind-pose variant?) — cross-check against ymg bind poses.
- (d) base-ID generation function (from item-6, still OPEN).
- (e) CAW `.gci` via parent Dolphin browser task (KNOWN CAW values).
