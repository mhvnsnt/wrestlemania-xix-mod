import struct, json, math
import numpy as np

# Load skeleton and FK
skel = json.load(open('/home/hatch/workspace/wmxix-mod-testbed/teardown/wwe-wrestlemania-xix/docs/wrestler-skeleton-000.json'))

def euler_to_mat(rx, ry, rz):
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    Rx = np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    Ry = np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    Rz = np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    return Rx @ Ry @ Rz

bone_world = {}
def compute_world(i):
    if i in bone_world: return bone_world[i]
    b = skel[i]
    R = euler_to_mat(*b['euler_xyz'])
    local = np.eye(4); local[:3,:3] = R; local[:3,3] = np.array(b['pos'])
    w = local if b['parent'] < 0 else compute_world(b['parent']) @ local
    bone_world[i] = w
    return w

for i in range(len(skel)): compute_world(i)

# Load batches
with open('/home/hatch/workspace/wmxix-mod-testbed/teardown/wmxix/wrestlers/000/000_0.ymg', 'rb') as f:
    data = f.read()

bt = struct.unpack('>I', data[0x60:0x64])[0]
batches = []
for i in range(20):
    o = bt + i*8
    r = data[o:o+8]
    idx, c1, count, doff = r[0], r[1], struct.unpack('>H', r[2:4])[0], struct.unpack('>I', r[4:8])[0]
    if count == 0: continue
    if doff == 0 or doff + count*6 > len(data): break
    verts = []
    for v in range(count):
        x, y, z = struct.unpack('>3h', data[doff+v*6:doff+v*6+6])
        verts.append((x/64.0, y/64.0, z/64.0))
    batches.append(dict(idx=idx, count=count, verts=np.array(verts)))

import pickle
with open('/home/hatch/workspace/wmxix-skinning-solve/batches.pkl', 'wb') as f:
    pickle.dump((batches, bone_world, skel), f)
print(f"Decoded {len(batches)} batches")
