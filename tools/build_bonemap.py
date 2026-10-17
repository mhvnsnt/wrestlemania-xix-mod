#!/usr/bin/env python3
"""
build_bonemap(ycg_bytes) -> bytes

Replicates the WMXIX runtime bonemap construction (main.dol, loader 0x80080170).

DISASSEMBLY PROVENANCE
----------------------
- Consumer: 0x80078d6c (file 0x5ce6c-0x5e520) reads bonemap via
  `lwz r19, 4(r4)` @ VA 0x800793c4, indexes via `lbzx r24, r19, r24`
  @ VA 0x80079438 / 0x800794bc. Single caller: `bl 0x80078d6c` @ 0x800813c4.
- Constructor: 0x80080170 (file 0x64270-0x65df8). Builds, per model entry,
  a bonemap buffer of malloc(entry_bone_count) bytes and stores its pointer
  into the entry's 12-byte runtime struct at word +4
  (`stw r10, 4(r4)` @ VA 0x80081318, r10 = bonemap-ptr table[entry]).

ALGORITHM (Path B -- the dedup path, loader 0x80080170, VA 0x800805b8-0x800807bc)
--------------------------------------------------------------------------------
For each entry, for each bone i (0-based, 0x40-byte stride records):
    key = bone_record[i][0:16]
    search accumulated unique table (64-byte slots) with memcmp(key, 16);
    bonemap[i] = index of first record with equal key (new bones append,
                 so this is first-occurrence order).
Path A (entry_count == 1, VA 0x800802f4-0x80080398) is the fast path:
    bonemap[i] = i (identity fill via unrolled stbx loop).

YCG MAPPING (verified against model__wrestler__000_0.ycg, 2356 bytes)
---------------------------------------------------------------------
File = u32be bone_count (42) followed by 42 x 56-byte records
(4 + 42*56 == 2356 EXACTLY; the "48-byte record" note in older docs is wrong).
Record layout: [+0] u32 name_hash, [+4] u32 field, [+8/+12] zero,
[+16:+56] 40 bytes transform floats.
The 16-byte dedup key = record[0:16]. This YCG has 21 unique keys out of
42 records (duplicate name hashes, e.g. 0x7ad45e02 x3), which is exactly
what the loader's dedup loop exists to merge.

CAVEAT: the loader dedups the 64-byte RUNTIME bone records; the static
mapping runtime_record[0:16] == ycg_record[0:16] is inferred from the
duplicate-hash structure, not proven instruction-by-instruction. The YCG
-> 64B record expansion code was not located. If the runtime key differs,
only the key extraction (first 16 bytes below) needs to change; the
dedup skeleton is exact per the disassembly.
"""
import struct


def parse_ycg(ycg_bytes):
    """Return (count, [records]) for a .ycg file."""
    if len(ycg_bytes) < 4:
        raise ValueError("too short for YCG header")
    count = struct.unpack(">I", ycg_bytes[0:4])[0]
    rec_size = 56
    recs = []
    off = 4
    for _ in range(count):
        recs.append(ycg_bytes[off:off + rec_size])
        off += rec_size
    if len(recs) != count or any(len(r) != rec_size for r in recs):
        raise ValueError(
            f"truncated YCG: count={count}, got {len(recs)} full records")
    return count, recs


def dedup_bonemap(keys):
    """
    Exact replicate of the loader's Path-B dedup loop
    (0x80080170 @ 0x800805b8-0x800807bc):
      unique = []
      for i, key in enumerate(keys):
          try: bonemap[i] = unique.index(key)   # memcmp 16B linear search
          except ValueError: unique.append(key); bonemap[i] = len(unique)-1
    """
    unique = []
    index_of = {}
    out = bytearray(len(keys))
    for i, key in enumerate(keys):
        j = index_of.get(key)
        if j is None:
            j = len(unique)
            unique.append(key)
            index_of[key] = j
        out[i] = j
    return bytes(out), len(unique)


def build_bonemap(ycg_bytes):
    """
    Build the runtime bonemap for a wrestler .ycg file.

    Returns bytes of length bone_count; bonemap[file_bone_id] = runtime
    bone index (deduped, first-occurrence order). The skin kernel then uses
    runtime = bonemap[file_bone_id] + 1 (index 0 reserved = no-bone).
    """
    count, recs = parse_ycg(ycg_bytes)
    keys = [r[0:16] for r in recs]  # 16-byte dedup key per loader memcmp
    bonemap, _unique_count = dedup_bonemap(keys)
    return bonemap


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else (
        "/home/hatch/workspace/agent-ops/worktrees/wrestling-teardown/"
        "wwe-wrestlemania-xix/.scratch/files/model__wrestler__000_0.ycg")
    data = open(path, "rb").read()
    bm = build_bonemap(data)
    count = struct.unpack(">I", data[:4])[0]
    print(f"YCG: {path}")
    print(f"bone_count={count}, bonemap_len={len(bm)}")
    print(f"unique runtime bones: {len(set(bm))}")
    print(f"bonemap bytes: {bm.hex()}")
    print(f"bonemap list: {list(bm)}")
    # sanity checks
    assert len(bm) == count, "length must equal bone count"
    assert set(bm) == set(range(len(set(bm)))), "must be dense 0..N-1"
    assert max(bm) < count, "values must be < bone count"
    print("sanity checks passed: dense 0..N-1, no crashes, "
          f"{len(set(bm))} distinct small values")
