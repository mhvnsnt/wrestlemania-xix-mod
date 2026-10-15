#!/usr/bin/env python3
"""YANM: scan whole file for .ycg joint-hash hits; print record context."""
import sys
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32, f32
from yanm_track_probe import ycg_hashes

def scan(path, ycg_path):
    data, size = stream_file(path)
    ycghd = set(h for h in ycg_hashes(ycg_path))
    hits = []
    for i in range(0, size - 4, 4):
        v = u32(data, i)
        if v in ycghd:
            hits.append(i)
    print(f'{path}: {len(hits)} hash hits at:', [hex(h) for h in hits])
    for h in hits:
        ctx = ' '.join('%08X' % u32(data, h + k * 4) for k in range(8))
        fl = ' '.join('%.4g' % f32(data, h + k * 4) for k in range(4, 8))
        print(f'  0x{h:05X}: hash=%08X' % u32(data, h))
        print(f'           u32: {ctx}')
        print(f'           f32[4..7]: {fl}')
    return hits

if __name__ == '__main__':
    yag = sys.argv[1] if len(sys.argv) > 1 else 'ringmotion/a000_0a.yag'
    ycg = sys.argv[2] if len(sys.argv) > 2 else 'model/wrestler/000_0.ycg'
    scan(yag, ycg)
