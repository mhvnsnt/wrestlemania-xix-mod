#!/usr/bin/env python3
"""Dump full a-offset tables for Type-B records + ymg record14 for comparison.

Focus: 0C5BF279 in 3 clips (a000_0a, c000_0a, c200_0a) vs ymg 000_0 record14
(12-word ID block). Tests whether the yag a-table mirrors the ymg detail table.
"""
import os, struct

FDIR = os.environ.get('WMXIX_FILES', '/tmp/wmxix_files')
def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]

def load(name):
    with open(os.path.join(FDIR, name), 'rb') as f: return f.read()

def find_typeb(data, hh):
    for r in range(60):
        o = 0x50 + r * 32
        w = [u32(data, o + i*4) for i in range(8)]
        if w[0] == 0 and w[2] == 0: break
        if w[0] == hh and w[1] != 0 and (w[7] >> 16) == 1:
            return r, w
    return None, None

def hexdump(data, base=0, width=16):
    for i in range(0, len(data), width):
        chunk = data[i:i+width]
        hexs = ' '.join(f'{c:02x}' for c in chunk)
        asc = ''.join(chr(c) if 32 <= c < 127 else '.' for c in chunk)
        print(f'  {base+i:05x}: {hexs:<{width*3}} |{asc}|')

for clip in ['ringmotion__a000_0a.yag', 'ringmotion__c000_0a.yag', 'ringmotion__c200_0a.yag']:
    data = load(clip)
    r, w = find_typeb(data, 0x0C5BF279)
    if r is None:
        print(f'{clip}: no 0C5BF279'); continue
    a = w[1]
    print(f'=== {clip} rec{r} a={a:#x} X/Y/Z={[hex(x) for x in w[4:7]]} w28={w[7]:#x} ===')
    # table length unknown; dump 192 bytes
    hexdump(data[a:a+192], base=a)

print('\n=== ymg 000_0 record14 (66 words) ===')
ymg = load('model__wrestler__000_0.ymg')
hdrs = [o for o in range(0, len(ymg)-8, 4) if u32(ymg, o) == o and u32(ymg, o+4) == 0]
for hi, o in enumerate(hdrs):
    end = hdrs[hi+1] if hi+1 < len(hdrs) else len(ymg)
    if (end-o)//4 == 66:
        w = [u32(ymg, o+k*4) for k in range(66)]
        print(f'record14 at {o:#x}:')
        for k in range(0, 24):
            print(f'  w{k:02d}: {w[k]:08X}')
        byts = b''.join(struct.pack('>I', x) for x in w[24:])
        print(f'  byte region ({len(byts)}B):')
        hexdump(byts, base=o+24*4)
        break
