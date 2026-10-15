#!/usr/bin/env python3
"""YANM TODO (2): track -> joint mapping via track directory (ends @0x3E8) + frame counts.
For each of 3 representative clips (a/b/c groups), decodes all 29 track records:
hash, kind (single/dual), stream offsets, key counts, dt-sum (ticks), seconds
(via header [0x3C] sec/tick); joins track hashes to ycg group anatomy
(docs/ycg-group-mapping.json) and the 70-bone ymg skeleton. Verifies all key
stream offsets lie at/after the directory end. Writes
docs/yanm-track-joint-map.json."""
import struct, sys, json, math
import numpy as np
sys.path.insert(0, 'tools')
from yukes_fmt import ISO, read_header, read_entries, flat_listing, u32, f32

def s16(b): return struct.unpack('>h', b)[0]

with open(ISO, 'rb') as iso:
    h = read_header(iso); e, nm = read_entries(iso, h['fst_off'], h['fst_size'])
    listing = flat_listing(e, nm)
fmap = {p.strip('/'): (o, l) for p, d, o, l in listing if not d}
_iso = open(ISO, 'rb')
def read(path):
    o, l = fmap[path.strip('/')]
    _iso.seek(o); return _iso.read(l)

mapping = json.load(open('docs/ycg-group-mapping.json'))
# hash -> group info
hash2group = {}
for g in mapping['groups']:
    for hh in g['hashes']:
        hash2group[hh] = g

def decode_track(data, rec):
    """rec: dict from directory. Returns decoded info incl. dt-sum."""
    o, size = rec['off'], len(data)
    hh = u32(data, o); a = u32(data, o+4); ks = u32(data, o+8)
    trip = tuple(f32(data, o+12+i*4) for i in range(3))
    w24 = u32(data, o+24); w28 = u32(data, o+28)
    info = dict(hash='%08X' % hh, dir_off=o, a=a, keyoff=ks, triple=trip, w24=w24)
    if a == 0:  # single: 5B keys, count = w28
        n = w28
        raw = data[ks:ks+n*5]
        dts = [raw[i*5+2] for i in range(n)]
        info.update(kind='single', nkeys=n, dt_sum=sum(dts), stream_len=n*5)
    else:  # dual: A 4B keys, B 5B keys; ca|cb = w28 hi|lo
        ca, cb = (w28 >> 16) & 0xFFFF, w28 & 0xFFFF
        # A stream: 8B header + (ca-2) 4B keys when ca>=2; ca==1 => 1 bare 4B key
        if ca >= 2:
            a_head = data[a:a+8]
            akeys = [(s16(data[a+8+i*4:a+8+i*4+2]), data[a+8+i*4+2], data[a+8+i*4+3])
                     for i in range(ca-2)]
            a_dt = sum(k[2] for k in akeys); a_len = 8 + (ca-2)*4
        else:
            a_head = None
            akeys = [(s16(data[a:a+2]), data[a+2], data[a+3])]
            a_dt = akeys[0][2]; a_len = 4
        bkeys = [(s16(data[ks+i*5:ks+i*5+2]), data[ks+i*5+2], s16(data[ks+i*5+3:ks+i*5+5]))
                 for i in range(cb)]
        b_dt = sum(k[1] for k in bkeys)
        info.update(kind='dual', ca=ca, cb=cb, a_head=a_head.hex() if a_head else None,
                    a_dt_sum=a_dt, b_dt_sum=b_dt, a_stream_len=a_len, b_stream_len=cb*5)
    return info

def parse_dir(data):
    recs = []
    for r in range(29):
        o = 0x50 + r*32
        hh = u32(data, o); ks = u32(data, o+8)
        if hh == 0 and ks == 0: break  # terminator
        recs.append(dict(off=o))
    return recs

CLIPS = ['ringmotion/a000_0a.yag', 'ringmotion/b000_0a.yag', 'ringmotion/c000_0a.yag']
result = {'clips': {}, 'dir_end': '0x3F0 (0x50 + 29*32)', 'hash_index': {}}
all_hashes = {}
for clip in CLIPS:
    data = read(clip)
    assert data[:4] == b'YANM', clip
    sec_tick = f32(data, 0x3C)
    recs = parse_dir(data)
    assert len(recs) == 29, (clip, len(recs))
    tracks = []
    for rec in recs:
        t = decode_track(data, rec)
        gh = hash2group.get(t['hash'])
        t['anatomy'] = gh['anatomy'] if gh else None
        t['confidence'] = gh['confidence'] if gh else None
        t['ycg_group_records'] = gh['records'] if gh else None
        # frame counts
        if t['kind'] == 'single':
            t['ticks'] = t['dt_sum']; t['seconds'] = round(t['dt_sum']*sec_tick, 3)
            t['static'] = t['nkeys'] == 1
        else:
            t['ticks'] = t['b_dt_sum']; t['seconds'] = round(t['b_dt_sum']*sec_tick, 3)
            t['static'] = False
        # verify streams live at/after directory end
        t['streams_after_dir'] = t['keyoff'] >= 0x3F0 and (t['kind']=='single' or t['a'] >= 0x3F0)
        tracks.append(t)
        all_hashes.setdefault(t['hash'], t['anatomy'])
    result['clips'][clip] = dict(sec_per_tick=sec_tick, n_tracks=len(tracks), tracks=tracks)
    print(f'== {clip}: sec/tick={sec_tick:.6f}, {len(tracks)} tracks')
    for t in tracks:
        anat = t['anatomy'] or ('STATIC-UNKNOWN' if t.get('static') else 'UNKNOWN-HASH')
        if t['kind'] == 'single':
            print(f"  {t['hash']} single n={t['nkeys']:3d} ticks={t['ticks']:4d} ({t['seconds']:6.2f}s) ks>={t['keyoff']:05X} ok={t['streams_after_dir']} :: {anat}")
        else:
            print(f"  {t['hash']} DUAL   ca={t['ca']:3d} cb={t['cb']:3d} a_dt={t['a_dt_sum']:4d} b_dt={t['b_dt_sum']:4d} ({t['seconds']:6.2f}s) :: {anat}")

print()
print('== hash/anatomy index across clips (%d unique hashes) ==' % len(all_hashes))
unk = [hh for hh, a in all_hashes.items() if a is None]
print('unknown hashes:', sorted(unk))
for hh in sorted(all_hashes):
    print(f'  {hh}: {all_hashes[hh]}')

json.dump(result, open('docs/yanm-track-joint-map.json', 'w'), indent=1)
print('\nwrote docs/yanm-track-joint-map.json')
