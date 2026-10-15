# YOBJ Skinning Solution (2026-10-15)

## Problem
YOBJ vertex positions could not be decoded. 11 hypotheses tested and rejected.
Per-strip skinning transforms produced scattered geometry.

## Solution

### Key Discovery
The **skin batch descriptor `idx` field (u8) IS the bone index**.

### Mapping
- Batch descriptor: `[u8 idx][u8 c1][u16 count][u32 offset]` at skin table + i*8
- `idx` is 0-based bone index
- Maps to skeleton bone `idx + 1` (skipping null sentinel at index 0)
- Verified: batch idx 0→Bip Pelvis, 1→Bip Spine, 2→Bip Spine1, 3→Bip Neck, 4→Bip Head, 5→right_lip, etc.

### Vertex Encoding
- Vertices are **s16 triplets in bone-local space**
- Scale: divide by 64.0
- All values positive (0–~2000 raw, 0–30 after /64)

### Transform
```
world_pos = bone_world_matrix @ (vertex / 64.0)
```

Bone world matrices computed via forward kinematics:
- Local: `T(pos) @ R(euler_xyz)` where R = Rx @ Ry @ Rz
- World: `parent_world @ local`

### Verification (000_0.ymg = Triple H head)
| Batch | Bone | Verts | Dimensions | Status |
|-------|------|-------|------------|--------|
| 1 | Bip Pelvis | 72 | 28.7cm max | Coherent torso |
| 2 | Bip Spine | 65 | 27.5cm max | Coherent torso |
| 3 | Bip Spine1 | 49 | 20.3cm max | Coherent torso |
| 4 | Bip Neck | 120 | 30.0cm max | Coherent neck |
| 5 | Bip Head | 17 | 15.0cm max | Coherent head |
| 6-13 | Facial bones | 4-102 | 8-28cm | Coherent features |

All parts assemble into correct anatomical positions. Dimensions match human proportions.

### Why Previous Attempts Failed
The "per-batch bone world matrix" hypothesis was tested but rejected as SCATTERED.
Likely causes:
1. Wrong bone mapping (did not realize idx → idx+1)
2. Wrong transform order or missing the /64 scale
3. Tested on wrong file or with incorrect skeleton

### Limitations
- **Rigid skinning only**: Each batch maps to exactly one bone (100% weight). Files with blended weights (joints) need additional data.
- **Table1/Table2 payloads**: 892 (u16,0) + 1026 (u16,u16) values with unknown semantics. May contain blend weights, UVs, or second mesh.
- **Full body**: 000_0.ymg contains head/torso/facial only. Limb geometry location unknown.

### Files
- Solver: `/tmp/000_0_assembled.obj` (verified assembly)
- This doc: `teardown/wwe-wrestlemania-xix/docs/YOBJ-SKINNING-SOLUTION.md`
