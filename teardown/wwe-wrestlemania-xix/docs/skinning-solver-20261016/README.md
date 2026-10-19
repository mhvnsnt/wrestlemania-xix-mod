# WMXIX Skinning Solver — Analysis Tools (2026-10-16)

Subagent investigation into YOBJ batch→bone mapping for WWE WrestleMania XIX (GameCube).

## Key Findings

### 1. Vertex decode CONFIRMED
- Format: s16x3 big-endian, scale 1/64 (`verts_float = s16 / 64.0`)
- Little-endian produces garbage; big-endian is correct
- First 2 "verts" of each batch are header data (y=0 pattern), NOT vertices

### 2. Batches are HEAD-REGION parts
- 13 batches, 606 verts total, all cluster in head region when mapped to head bones
- Render `head_test.png` shows geometry in head area (messy due to strip issues)
- The SOLUTION doc's claim (idx→bone idx+1) is WRONG — produces garbage (see `solution_mapping.png`)

### 3. Strip boundaries UNKNOWN (blocker)
- Each batch contains MULTIPLE triangle strips concatenated
- Simple distance-threshold splitting fails (longest coherent run only 12 verts)
- The DOL report's claim ("verts 35-62 form coherent ribbon") does NOT reproduce
- The 58-record table (16B records at file 0x5AE0) likely defines strips, but semantics undecoded
- Payload is (u16,0) pairs with values 0-4096; 74.6% exceed 606 (not vertex indices)

### 4. Batch→bone mapping UNKNOWN (blocker)
- DOL uses 256-byte bonemap: `runtime_bone = bonemap[file_bone_id]`
- Skin kernels at 0x800ABF8C (1 bone), 0x800AC040 (2 bones), 0x800AC1D4 (3 bones)
- Bone matrix stride 0x30 (48 bytes = 3x4 floats)
- Bonemap not located in file or DOL

### 5. ISO unavailable (blocks Dolphin)
- Split parts in ~/workspace/wmxix-iso/ are PARTIAL downloads (1.25GB of 1.98GB)
- Cannot reassemble, cannot run Dolphin for FIFO capture

## Files
- `decode.py` — YOBJ batch decoder (s16x3 BE /64, skips 2-vert header)
- `batches.pkl` — Decoded batches + FK bone matrices + skeleton
- `*.png` — Renders proving the above findings

## Path Forward
1. Complete ISO download (`~/workspace/wmxix-iso/dl.sh`), reassemble, extract YCG (may contain bonemap)
2. Run Dolphin, break at 0x800ABF8C, dump bonemap + 16-byte records
3. Decode 58-record table semantics for strip boundaries
4. Trace DOL r7 (bonemap arg) to file source
