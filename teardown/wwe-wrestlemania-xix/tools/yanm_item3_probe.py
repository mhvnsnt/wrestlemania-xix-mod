#!/usr/bin/env python3
"""YANM item 3: 0C5BF279 9-param-word decode + 40911198 clip role.
Streams from ISO. Run from wwe-wrestlemania-xix/ dir."""
import sys, struct
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32
from gcn_fst import read_header, read_entries, flat_listing

ISO = 'WWE Wrestlemania XIX (USA).iso'
with open(ISO, 'rb') as iso:
    h = read_header(iso); e, nm = read_entries(iso, h['fst_off'], h['fst_size'])
    listing = flat_listing(e, nm)
fmap = {p.strip('/').lstrip('/'): (o, l) for p, d, o, l in listing if not d}
_iso = open(ISO, 'rb')
def read(path):
    o, l = fmap[path]
    _iso.seek(o); return _iso.read(l)
def f32(b, i): return struct.unpack('>f', b[i:i+4])[0]
def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]

def dir_records(data):
    recs = []
    for r in range(29):
        o = 0x50 + r * 32
        if o + 32 > len(data): break
        hh, a, ks, w28 = u32(data, o), u32(data, o+4), u32(data, o+8), u32(data, o+28)
        if hh == 0 and ks == 0: break
        recs.append(dict(idx=r, hash=hh, a=a, ks=ks, w28=w28))
    return recs

# ============ (1) 40911198 / 0C5BF279 / ECD28978 across ALL yag clips ============
print('=== (1) track presence across all 215 yag clips ===')
from collections import Counter
use = Counter(); clip_of = {}
files = sorted(p for p in fmap if p.endswith('.yag'))
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    for r in dir_records(data):
        hh = r['hash']
        if hh in (0x40911198, 0x0C5BF279, 0xECD28978):
            use[hh] += 1
            clip_of.setdefault(hh, []).append(path)
for hh in (0x40911198, 0x0C5BF279, 0xECD28978):
    print(f'  {hh:08X}: {use[hh]} clips')
    for c in clip_of.get(hh, [])[:15]:
        print('     ', c)
    if len(clip_of.get(hh, [])) > 15: print('     ... +', len(clip_of[hh]) - 15)

# ============ (2) wrestler ymg table parse ============
print()
print('=== (2) ymg detail-track table per wrestler ===')
wrestlers = sorted(p for p in fmap if p.startswith('model/wrestler/') and p.endswith('.ymg'))

def parse_records(data):
    """Find record headers (u32 at o == o), parse entries + hash + params."""
    recs = []
    # candidate headers: word equals its own offset
    hdrs = []
    for o in range(0, len(data) - 8, 4):
        if u32(data, o) == o and u32(data, o+4) == 0:
            hdrs.append(o)
    for hi, o in enumerate(hdrs):
        end = hdrs[hi+1] if hi+1 < len(hdrs) else len(data)
        words = [u32(data, o+k) for k in range(0, end-o, 4)]
        # words[0]=self, words[1]=0, then entries: groups of 5 starting where?
        recs.append(dict(off=o, words=words))
    return recs

table = {}
for wp in wrestlers[:12]:
    data = read(wp)
    recs = parse_records(data)
    rows = []
    for r in recs:
        w = r['words']
        # find hash slot: first word > 0x1000 that is followed by 9 non-padding words
        # entries are 5-word groups; scan for known-hash pattern
        info = dict(off=hex(r['off']), nwords=len(w))
        # look for a hash-like word (not small, not padding)
        cands = []
        for i, ww in enumerate(w):
            if 0x1000 < ww < 0xFFFFFFFF and ww not in (0xE4E4E4E4,):
                cands.append((i, ww))
        info['cands'] = [(i, f'{ww:08X}') for i, ww in cands[:6]]
        rows.append(info)
    table[wp] = rows

# print compact: which wrestlers have which hash in a record
for wp in wrestlers[:12]:
    data = read(wp)
    recs = parse_records(data)
    print(' ', wp.split('/')[-1], 'records:', len(recs))
    for r in recs:
        w = r['words']
        # hash = first word in record (after header) that appears in yag universe or is 00010000
        hs = [f'{ww:08X}' for ww in w[2:14] if ww in (0x0C5BF279, 0x40911198, 0xECD28978, 0x10000)]
        print('    @%s nwords=%d hashslot=%s' % (hex(r['off']), len(w), hs))
print('done')
