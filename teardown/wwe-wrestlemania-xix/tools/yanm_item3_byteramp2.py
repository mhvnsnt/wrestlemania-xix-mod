#!/usr/bin/env python3
"""Item 3: byte-ramp vs ID-block elements. Tests the remap-LUT hypothesis.

1. Extract record14 (66-word) byte region + 12-word ID block for each wrestler.
2. Segment 168B into 12x14B; characterize each segment (dominant value, outliers).
3. Test: does segment k relate to ID-block word k?
4. Cross-wrestler: same ID block -> same bytes? (000_0 vs 047_0 known identical)
5. POF0/string search across ymg + yag files.
"""
import os, struct, glob
from collections import Counter

FDIR = os.environ.get('WMXIX_FILES', '/tmp/wmxix_files')
def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]
def load(n):
    with open(os.path.join(FDIR, n), 'rb') as f: return f.read()

def record14(data):
    hdrs = [o for o in range(0, len(data)-8, 4) if u32(data, o) == o and u32(data, o+4) == 0]
    for hi, o in enumerate(hdrs):
        end = hdrs[hi+1] if hi+1 < len(hdrs) else len(data)
        if (end-o)//4 == 66:
            return o, [u32(data, o+k*4) for k in range(66)]
    return None, None

print('== 1. record14 per wrestler: ID block + byte region ==')
regions = {}
for fn in sorted(glob.glob(os.path.join(FDIR, 'model__wrestler__*.ymg'))):
    name = os.path.basename(fn)
    data = load(name)
    o, w = record14(data)
    if w is None:
        print(f'{name}: no 66-word record14'); continue
    idblock = w[7:20]  # w07=0C5BF279, w08..w19 = 12 ID words
    assert w[7] == 0x0C5BF279, f'{name} w07={w[7]:08X}'
    byts = b''.join(struct.pack('>I', x) for x in w[24:])
    regions[name] = (idblock, byts)
    print(f'{name}: idblock[0]={idblock[0]:08X} idblock[11]={idblock[11]:08X} '
          f'bytes={len(byts)} distinct={len(set(byts))}')

print('\n== 2. 168B = 12 x 14B segmentation (000_0) ==')
idblock, byts = regions['model__wrestler__000_0.ymg']
for k in range(12):
    seg = byts[k*14:(k+1)*14]
    c = Counter(seg)
    top = c.most_common(3)
    outliers = sorted(v for v in set(seg) if v not in (top[0][0],))
    print(f'seg{k:02d} id={idblock[k]:08X} dom={top[0][0]:#04x}x{top[0][1]} '
          f'top3={[(hex(v),n) for v,n in top]} outliers={[hex(v) for v in outliers]}')

print('\n== 3. cross-wrestler byte-region comparison ==')
names = sorted(regions)
for i, n1 in enumerate(names):
    for n2 in names[i+1:]:
        same = regions[n1][1] == regions[n2][1]
        same_id = regions[n1][0] == regions[n2][0]
        print(f'{n1.split("__")[-1]} vs {n2.split("__")[-1]}: bytes_same={same} idblock_same={same_id}')

print('\n== 4. POF0 + 37-char string search ==')
needle = b'ABAGAHGAGAH'
for fn in sorted(glob.glob(os.path.join(FDIR, '*'))):
    name = os.path.basename(fn)
    data = load(name)
    pofs = []
    i = data.find(b'POF0')
    while i != -1:
        pofs.append(i); i = data.find(b'POF0', i+1)
    s = data.find(needle)
    if pofs or s != -1:
        print(f'{name}: POF0@{[hex(x) for x in pofs]} ABAG*@{hex(s) if s!=-1 else None}')
