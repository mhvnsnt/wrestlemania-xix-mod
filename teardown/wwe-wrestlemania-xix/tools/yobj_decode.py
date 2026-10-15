#!/usr/bin/env python3
"""YOBJ (WWE WrestleMania XIX, GameCube 2003) structural decoder.

Parses everything understood about the YOBJ container and exports raw data
for analysis. DOES NOT yet produce an assemblable mesh -- the vertex position
encoding and skinning assembly remain unsolved (see YOBJ-SKINNING-DECODER-REPORT.md).

What this decodes:
- Header: bone count, skeleton/material/table offsets
- Skeleton: 71 bones (name, parent, pos, euler, length) + world matrices
- Skin batches: 13 x (count, offset) -> s16x3 runs (606 verts, 000_0.ymg)
- Table1: 58 records (u0,u1,b8,marker,variant,count) -> (u16,0) payloads
- Table2: 52 records (u0,u1,a,b,c,count) -> (u16,u16) payloads  [DISCOVERED 2026-10-15]
- Materials: 15 x 20B records + texture names

Usage:
  python3 tools/yobj_decode.py model/wrestler/000_0.ymg [--iso-range]
  Outputs: <name>_skeleton.obj, <name>_batches.obj, <name>_report.txt

Streams from ISO via tools/wmxix_range_iso.py (disk-safe).
"""
import struct, sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def u32(b,i): return struct.unpack('>I', b[i:i+4])[0]
def u16(b,i): return struct.unpack('>H', b[i:i+2])[0]
def s16(b,i): return struct.unpack('>h', b[i:i+2])[0]
def f32(b,i): return struct.unpack('>f', b[i:i+4])[0]

class Yobj:
    def __init__(self, data):
        self.d = data
        assert data[:4] == b'YOBJ', 'not YOBJ'
        self.parse_header()
        self.parse_skeleton()
        self.parse_batches()
        self.parse_table1()
        self.parse_table2()
        self.parse_materials()

    def parse_header(self):
        d = self.d
        self.bone_count = u32(d, 0x10)
        self.skel_off = u32(d, 0x14)
        self.mat_count = u32(d, 0x18)
        self.mat_tab = u32(d, 0x1C)
        self.texnames_off = u32(d, 0x24)
        self.gctc_off = u32(d, 0x38)
        self.base = u32(d, 0x54)
        self.table1_off = u32(d, 0x5C)
        self.skin_off = u32(d, 0x60)
        self.ver_a, self.ver_b = u16(d, 0x08), u16(d, 0x0A)

    def parse_skeleton(self):
        d, n = self.d, self.bone_count
        # Header [0x14] points to the skeleton section; bone slots start 8 bytes
        # later (section has an 8-byte prologue). Verify by 'null' name.
        base = self.skel_off
        if d[base:base+4] != b'null':
            base += 8
        assert d[base:base+4] == b'null', f'bone0 not at {base:#x}'
        self.bones = []
        for s in range(n):
            o = base + s*64
            name = d[o:o+16].split(b'\x00')[0].decode('ascii','replace')
            p = u32(d, o+16)
            parent = -1 if p == 0xFFFFFFFF else p-1
            pos = [f32(d,o+20+i*4) for i in range(3)]
            eul = [f32(d,o+32+i*4) for i in range(3)]
            length = f32(d,o+44)
            self.bones.append(dict(name=name, parent=parent, pos=pos, eul=eul, length=length))
        # world matrices (euler XYZ order: R = Rx @ Ry @ Rz)
        import numpy as np
        self._np = np
        world = [None]*n
        def Rx(a):
            c,s = math.cos(a), math.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
        def Ry(a):
            c,s = math.cos(a), math.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
        def Rz(a):
            c,s = math.cos(a), math.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])
        def gw(s):
            if world[s] is None:
                b = self.bones[s]
                M = np.eye(4)
                M[:3,:3] = Rx(b['eul'][0]) @ Ry(b['eul'][1]) @ Rz(b['eul'][2])
                M[:3,3] = b['pos']
                world[s] = M if b['parent'] < 0 else gw(b['parent']) @ M
            return world[s]
        for s in range(n): gw(s)
        self.world_mats = world

    def parse_batches(self):
        d = self.d
        self.batches = []
        o = self.skin_off
        # record 0 is header (all zeros); records 1..N are batches
        idx = 0
        while o + 8 <= len(d):
            c1 = d[o+1]; off = u32(d, o+4)
            # stop at garbage (offset beyond file)
            if self.base + off >= len(d) and c1 != 0:
                break
            if c1 == 0 and off == 0:
                o += 8; idx += 1; continue
            base = self.base + off
            verts = [(s16(d,base+i*6), s16(d,base+i*6+2), s16(d,base+i*6+4))
                     for i in range(c1)]
            self.batches.append(dict(index=idx, count=c1, offset=off, verts=verts))
            o += 8; idx += 1
            if idx > 32: break

    def parse_table1(self):
        d = self.d
        self.table1 = []
        o = self.table1_off
        while o + 16 <= len(d):
            v = d[o+11]; cnt = u32(d,o+12)
            if d[o] == 0 and v in (1,2) and cnt < 20000:
                u0, u1 = u32(d,o), u32(d,o+4)
                b8, mk = d[o+8], u16(d,o+9)
                pb = self.base + u0
                payload = [(u16(d,pb+i*4), u16(d,pb+i*4+2)) for i in range(cnt)]
                self.table1.append(dict(u0=u0, u1=u1, b8=b8, marker=mk,
                                        variant=v, count=cnt, payload=payload))
                o += 16
            else:
                break

    def parse_table2(self):
        # 16B records (u0,u1,a,b,c,count) following table1; payload is (u16,u16)
        d = self.d
        self.table2 = []
        o = self.table1_off + len(self.table1)*16
        while o + 16 <= self.skin_off:
            u0, u1 = u32(d,o), u32(d,o+4)
            a,b,c, cnt = u16(d,o+8), u16(d,o+10), u16(d,o+12), u16(d,o+14)
            # stop at (u16,0) payload data (not table records)
            if u16(d,o+2)==0 and u16(d,o+6)==0 and u16(d,o+10)==0 and u16(d,o+14)==0:
                break
            if u0 >= 0x10000 or cnt >= 200:
                break
            pb = self.base + u0
            payload = [(u16(d,pb+i*4), u16(d,pb+i*4+2)) for i in range(cnt)]
            self.table2.append(dict(u0=u0, u1=u1, a=a, b=b, c=c, count=cnt,
                                    payload=payload))
            o += 16

    def parse_materials(self):
        d = self.d
        self.materials = []
        for m in range(self.mat_count):
            o = self.mat_tab + m*20
            rec = d[o:o+20]
            # [u16 a][u16 b][u16 one][u16 idx_off][RGBA x3]
            a,b,one,idx_off = u16(d,o), u16(d,o+2), u16(d,o+4), u16(d,o+6)
            colors = [tuple(rec[8+i*4:12+i*4]) for i in range(3)]
            self.materials.append(dict(a=a,b=b,one=one,idx_off=idx_off,colors=colors))
        # texture names (null-terminated strings)
        import re
        region = d[self.texnames_off:self.mat_tab]
        self.texnames = [m.group(0).decode('ascii')
                         for m in re.finditer(b'[ -~]{3,}', region)]

    def write_skeleton_obj(self, path):
        np = self._np
        with open(path, 'w') as f:
            joints = []
            for s,b in enumerate(self.bones):
                j = self.world_mats[s][:3,3]
                joints.append(j)
                f.write(f'v {j[0]:.3f} {j[1]:.3f} {j[2]:.3f}  # {b["name"]}\n')
            for s,b in enumerate(self.bones):
                if b['parent'] >= 0:
                    f.write(f'l {b["parent"]+1} {s+1}\n')

    def write_batches_obj(self, path, scale=1.0/64):
        # Raw batch verts (UNPOSED -- do not represent the assembled mesh)
        with open(path, 'w') as f:
            f.write('# YOBJ skin batches: RAW s16/64, NOT assembled (see report)\n')
            vi = 1
            for b in self.batches:
                f.write(f'# batch {b["index"]}: {b["count"]} verts @0x{b["offset"]:X}\n')
                for x,y,z in b['verts']:
                    f.write(f'v {x*scale:.4f} {y*scale:.4f} {z*scale:.4f}\n')
                vi += b['count']

    def report(self):
        L = []
        L.append(f'YOBJ: {len(self.d)} bytes, ver=({self.ver_a},{self.ver_b})')
        L.append(f'bones={self.bone_count} @0x{self.skel_off:X}, '
                 f'materials={self.mat_count} @0x{self.mat_tab:X}')
        L.append(f'table1={len(self.table1)} recs @0x{self.table1_off:X}, '
                 f'table2={len(self.table2)} recs, '
                 f'skin_batches={len(self.batches)} @0x{self.skin_off:X}')
        L.append(f'total batch verts={sum(b["count"] for b in self.batches)}, '
                 f'table1 payload units={sum(r["count"] for r in self.table1)}, '
                 f'table2 payload units={sum(r["count"] for r in self.table2)}')
        L.append(f'texture names ({len(self.texnames)}): {self.texnames[:14]}')
        return '\n'.join(L)


def load(path):
    if path.endswith('.ymg') and os.path.exists(path):
        return Yobj(open(path,'rb').read())
    # stream from ISO
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from wmxix_range_iso import RangeISO
    from gcn_fst import read_header, read_entries, flat_listing
    iso = RangeISO()
    h = read_header(iso)
    entries, name = read_entries(iso, h['fst_off'], h['fst_size'])
    for p, isdir, o, l in flat_listing(entries, name):
        if p.strip('/') == path.strip('/') and not isdir:
            iso.seek(o); data = iso.read(l); iso.close()
            # DUMY wrapper?
            if data[:4] == b'DUMY':
                data = data[0x18:]
            return Yobj(data)
    raise SystemExit('not found: ' + path)

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else 'model/wrestler/000_0.ymg'
    y = load(src)
    outdir = sys.argv[2] if len(sys.argv) > 2 else '/tmp'
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    print(y.report())
    y.write_skeleton_obj(f'{outdir}/{base}_skeleton.obj')
    y.write_batches_obj(f'{outdir}/{base}_batches.obj')
    with open(f'{outdir}/{base}_report.txt','w') as f:
        f.write(y.report() + '\n')
    print(f'wrote {outdir}/{base}_{{skeleton,batches}}.obj')

if __name__ == '__main__':
    main()
