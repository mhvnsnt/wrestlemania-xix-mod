#!/usr/bin/env python3
"""Item 3b: POF0 container survey.
1. ymg files: dump 64B around each POF0 (esp. non-66-word-record files).
2. yag files: dump full 0C5BF279 a-table for clips WITH vs WITHOUT the ABAG string.
"""
import os, struct, glob

FDIR = os.environ.get('WMXIX_FILES', '/tmp/wmxix_files')
def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]
def load(n):
    with open(os.path.join(FDIR, n), 'rb') as f: return f.read()
def hexdump(data, base=0, width=16):
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hexs = ' '.join(f'{c:02x}' for c in chunk)
        asc = ''.join(chr(c) if 32 <= c < 127 else '.' for c in chunk)
        print(f'  {base+i:05x}: {hexs:<{width*3}} |{asc}|')
def find_typeb(data, hh):
    for r in range(60):
        o = 0x50 + r * 32
        if o + 32 > len(data): break
        w = [u32(data, o+i*4) for i in range(8)]
        if w[0] == 0 and w[2] == 0: break
        if w[0] == hh and w[1] != 0 and (w[7] >> 16) == 1:
            return r, w
    return None, None

print('== 1. ymg POF0 neighborhoods ==')
for fn in sorted(glob.glob(os.path.join(FDIR, 'model__wrestler__*.ymg'))):
    name = os.path.basename(fn)
    data = load(name)
    i = data.find(b'POF0')
    print(f'--- {name} POF0@{i:#x} filelen={len(data)} ---')
    hexdump(data[i-16:i+64], base=i-16)

print('\n== 2. 0C5BF279 a-table: ABAG clips vs non-ABAG clips ==')
for clip in ['ringmotion__a000_0a.yag', 'viewer__motion__8502_0a.yag',
             'viewer__motion__8510_0a.yag', 'viewer__motion__8520_0a.yag',
             'viewer__motion__SAMPLE.yag']:
    data = load(clip)
    r, w = find_typeb(data, 0x0C5BF279)
    if r is None:
        print(f'{clip}: no 0C5BF279'); continue
    a = w[1]
    has_abag = data.find(b'ABAGAHGAGA', a, a+200) != -1
    print(f'--- {clip} rec{r} a={a:#x} X/Y/Z={[hex(x) for x in w[4:7]]} ABAG={has_abag} ---')
    hexdump(data[a:a+80], base=a)
