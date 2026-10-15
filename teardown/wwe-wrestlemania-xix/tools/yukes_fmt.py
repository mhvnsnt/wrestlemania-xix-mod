#!/usr/bin/env python3
"""Yukes (WMXIX GCN) format structural probe - pure stdlib, streams from ISO.
Parses YOBJ (.ymg mesh) and YANM (.yag animation) headers: prints u32/f32
header words, finds plausible internal offsets (u32 < filesize pointing at
non-zero data), and scans the whole file for ASCII section magics.
Disk-safe: streams single files from ISO byte ranges, writes nothing."""
import struct, sys

ISO = "WWE Wrestlemania XIX (USA).iso"
sys.path.insert(0, 'tools')
from gcn_fst import read_header, read_entries, flat_listing

def stream_file(path, maxlen=None):
    with open(ISO, 'rb') as iso:
        h = read_header(iso)
        entries, name = read_entries(iso, h['fst_off'], h['fst_size'])
        listing = flat_listing(entries, name)
        for p, isdir, o, l in listing:
            if p.strip('/') == path.strip('/') and not isdir:
                iso.seek(o)
                return iso.read(l if maxlen is None else min(l, maxlen)), l
    raise SystemExit('not found: ' + path)

def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]
def f32(b, i): return struct.unpack('>f', b[i:i+4])[0]

def dump_header(data, size, words=32):
    print(f'  header u32 words (offset: hex / float):')
    for i in range(0, min(words*4, len(data)), 16):
        w = ' '.join(f'{u32(data,j):08X}' for j in range(i, min(i+16, len(data)), 4))
        fl = ' '.join(f'{f32(data,j):10.4g}' for j in range(i, min(i+16, len(data)), 4))
        print(f'  0x{i:04X}: {w}\n           {fl}')

def find_offsets(data, size, hdr_range=256):
    """u32 in first hdr_range bytes that are plausible file-internal offsets"""
    print('  plausible internal offsets (value < size, target nonzero):')
    for i in range(0, hdr_range, 4):
        v = u32(data, i)
        if 0x10 <= v < size and any(data[v:v+8]):
            print(f'    [0x{i:04X}] -> 0x{v:05X}  bytes: {data[v:v+16].hex()}')

def scan_magics(data, size):
    print('  ascii magic hits:')
    hits = []
    for i in range(size - 4):
        c = data[i:i+4]
        if all(32 <= x < 127 or x in (0, 9, 10, 13) for x in c) and all(65 <= x <= 90 or x == 0 for x in c):
            tag = c.replace(b'\x00', b'').decode()
            if len(tag) >= 3:
                hits.append((i, tag))
    seen = {}
    for i, tag in hits:
        if tag not in seen: seen[tag] = i
    for tag, i in sorted(seen.items(), key=lambda x: x[1])[:40]:
        print(f'    0x{i:06X}: {tag}')

def probe(path):
    data, size = stream_file(path)
    magic = data[:4].decode('ascii', 'replace')
    print(f'=== {path}  magic={magic!r} size={size}')
    dump_header(data, size)
    find_offsets(data, size)
    scan_magics(data, size)
    print()

if __name__ == '__main__':
    for p in sys.argv[1:]:
        probe(p)
