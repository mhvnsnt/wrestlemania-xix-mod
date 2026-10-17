# WMXIX Axis Permutation Discovery (2026-10-17)

## Finding
The YMG file stores bone transform coordinates in **Y-Z-X order**, not X-Y-Z.

### Evidence
Raw bone 0 ("Bip") transform at file offset 0xf414:
- +0x00: -102.695 → JSON pos[1] (Y)
- +0x04: 0.0 → JSON pos[2] (Z)  
- +0x08: -0.0 → JSON pos[0] (X)
- +0x0c: 1.5708 → JSON euler[1] (Y)
- +0x10: 0.0 → JSON euler[2] (Z)
- +0x14: ~0.0 → JSON euler[0] (X)

File order: [Y, Z, X] — JSON (and all prior code) reads as [X, Y, Z].

### Impact
All prior FK computations used permuted axes. The correct world mapping
found by brute-force testing all 6 permutations:

**Permutation (1,0,2)**: worldX=JSON[1], worldY=JSON[0], worldZ=JSON[2]
- Produces VERTICAL skeleton: height=2.491m, head above pelvis above foot
- All other permutations give horizontal (0m height) or wrong results

### Implied File Convention
- file[Y] → world[Y] (via JSON[0])
- file[Z] → world[X] (via JSON[1])  
- file[X] → world[Z] (via JSON[2])

Or equivalently: world = [fileZ, fileY, fileX]

### Status
Skeleton is now vertical, but batch→bone assembly still broken (57m bbox).
The verts may use a different convention or scale. DOL disassembly needed
for ground truth on the vertex transform.
