#!/usr/bin/env python3
"""YANM track census + YCG hash identification for WMXIX teardown.
1) Reads all 42 .ycg hashes; tries to identify hash function over .ymg bone names.
2) Parses YANM header section offsets; hunts for the track table; reports
   track count candidates and base-pose quats for comparison with .ycg."""
import struct, sys, json, zlib
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32, f32

def hashfns(name):
    b = name.encode('ascii', 'replace')
    out = {}
    out['crc32'] = zlib.crc32(b) & 0xFFFFFFFF
    h = 5381
    for x in b: h = ((h * 33) + x) & 0xFFFFFFFF
    out['djb2'] = h
    h = 5381
    for x in b: h = ((h * 33) ^ x) & 0xFFFFFFFF
    out['djb2x'] = h
    h = 0
    for x in b: h = (x + (h << 6) + (h << 16) - h) & 0xFFFFFFFF
    out['sdbm'] = h
    h = 0
    for x in b:
        h = ((h << 4) + x) & 0xFFFFFFFF
        g = h & 0xF0000000
        if g: h ^= (g >> 24)
        h &= ~g & 0xFFFFFFFF if False else h
    # ELF proper:
    h = 0
    for x in b:
        h = ((h << 4) + x) & 0xFFFFFFFF
        xh = h & 0xF0000000
        if xh: h ^= (xh >> 24); h ^= xh
    out['elf'] = h
    h = 2166136261
    for x in b: h = ((h ^ x) * 16777619) & 0xFFFFFFFF
    out['fnv1a32'] = h
    # YUKEs could use a custom hash; also try sum-based
    out['sum'] = sum(b) & 0xFFFFFFFF
    return out

def ycg_hashes(path):
    data, _ = stream_file(path)
    n = u32(data, 0)
    return [u32(data, 4 + r * 56) for r in range(n)]

def ycg_records(path):
    data, _ = stream_file(path)
    n = u32(data, 0)
    recs = []
    for r in range(n):
        o = 4 + r * 56
        recs.append({'hash': u32(data, o), 'pos': (f32(data, o + 16), f32(data, o + 20), f32(data, o + 24)),
                     'quat': tuple(f32(data, o + 28 + k * 4) for k in range(4))})
    return recs

def main():
    skel = json.load(open('docs/wrestler-skeleton-000.json'))
    names = [b['name'] for b in skel]
    ycg_path = 'model/wrestler/000_0.ycg'
    hashes = ycg_hashes(ycg_path)
    hs = set(hashes)
    print(f'ycg joints: {len(hashes)}, distinct hashes: {len(hs)}')
    # Try to identify hash over bone names (also try lowercase / case variants)
    variants = {}
    for n in names:
        variants[n] = n
        variants[n.lower()] = n.lower()
        variants[n.replace(' ', '_')] = n.replace(' ', '_')
    found = []
    for fn_name in ['crc32', 'djb2', 'djb2x', 'sdbm', 'elf', 'fnv1a32', 'sum']:
        for cand, _src in variants.items():
            if hashfns(cand)[fn_name] in hs:
                found.append((fn_name, cand, f'{hashfns(cand)[fn_name]:08X}'))
    print('hash matches:', found if found else 'NONE of crc32/djb2/djb2x/sdbm/elf/fnv1a32/sum')
    # duplicate hashes in ycg
    from collections import Counter
    dup = {f'{h:08X}': c for h, c in Counter(hashes).items() if c > 1}
    print('duplicate hashes:', dup)

if __name__ == '__main__':
    main()
