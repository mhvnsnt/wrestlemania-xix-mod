#!/usr/bin/env python3
"""YANM item-6 (cycle 3): ECD identity via the semantic showcase clips.

viewer/motion/FACE.yag / HAND.yag / FIGHTING.yag / SAMPLE.yag are the only
semantically-named clips in the 215-clip universe. If ECD28978 is a face-bone
driver, FACE.yag is where it must show distinctive behavior.

Probes:
 1. ECD static pose + intra-clip animation range in the 4 semantic clips.
 2. Which tracks are animated (raw range > 1000) in FACE.yag vs HAND.yag:
    tracks animated ONLY in FACE are face-driver candidates; check ECD's
    relation to them.
 3. ECD pose census over viewer/motion/85xx_0a clips (per-wrestler showcase).
 4. Global: clips sharing FACE's ECD pose (0,79.9) - what are they?
Measured only, streams from ISO.
"""
import sys, struct, math
from collections import Counter, defaultdict
sys.path.insert(0, 'tools')
from gcn_fst import read_header, read_entries, flat_listing

ISO = 'WWE Wrestlemania XIX (USA).iso'
iso = open(ISO, 'rb')
h = read_header(iso); e, nm = read_entries(iso, h['fst_off'], h['fst_size'])
fmap = {p.strip('/'): (o, l) for p, d, o, l in flat_listing(e, nm) if not d}
_iso = open(ISO, 'rb')
def read(path):
    o, l = fmap[path]; _iso.seek(o); return _iso.read(l)
def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]
def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]
def ang(v): return math.degrees(math.asin(max(-1.0, min(1.0, v / 32767.0))))
ECD = 0xECD28978

def dir_records(data):
    recs = []
    for r in range(60):
        o = 0x50 + r * 32
        if o + 32 > len(data): break
        hh, a, ks, w28 = u32(data, o), u32(data, o+4), u32(data, o+8), u32(data, o+28)
        if hh == 0 and ks == 0: break
        recs.append(dict(idx=r, hash=hh, a=a, ks=ks, w28=w28))
    return recs

def track_range(data, rec):
    c1 = [s16(data, rec['ks']+i*5) for i in range(rec['w28'])]
    c2 = [s16(data, rec['ks']+i*5+3) for i in range(rec['w28'])]
    return max(c1)-min(c1), max(c2)-min(c2), c1[0], c2[0]

print('== 1. semantic clips: ECD pose + intra-clip range ==')
sem = {}
for p in ['viewer/motion/FACE.yag', 'viewer/motion/HAND.yag',
          'viewer/motion/FIGHTING.yag', 'viewer/motion/SAMPLE.yag',
          'viewer/a.yag', 'viewer/b.yag', 'viewer/c.yag']:
    data = read(p)
    recs = {r['hash']: r for r in dir_records(data)}
    if ECD not in recs:
        print(f'{p}: NO ECD'); continue
    r1, r2, v1, v2 = track_range(data, recs[ECD])
    sem[p] = (v1, v2, r1, r2)
    print(f'{p}: ECD static=({ang(v1):.1f},{ang(v2):.1f}) intra-range=({r1},{r2})')

print('\n== 2. animated tracks (range>1000, a==0 only) in FACE vs HAND ==')
anim = {}
altfmt = {}
for p in ['viewer/motion/FACE.yag', 'viewer/motion/HAND.yag']:
    data = read(p); recs = dir_records(data)
    a = []; alt = []
    for r in recs:
        if r['a'] != 0:
            alt.append(r['hash']); continue
        r1, r2, _, _ = track_range(data, r)
        if r1 > 1000 or r2 > 1000:
            a.append((r['hash'], r1, r2))
    anim[p] = {hh for hh, _, _ in a}
    altfmt[p] = set(alt)
    print(f'{p}: {len(a)} animated a==0 tracks, {len(alt)} alt-format tracks')
    for hh, r1, r2 in sorted(a): print(f'   anim {hh:08X} range=({r1},{r2})')
face_only = anim['viewer/motion/FACE.yag'] - anim['viewer/motion/HAND.yag']
hand_only = anim['viewer/motion/HAND.yag'] - anim['viewer/motion/FACE.yag']
print(f'FACE-only animated ({len(face_only)}):', sorted(f'{x:08X}' for x in face_only))
print(f'HAND-only animated ({len(hand_only)}):', sorted(f'{x:08X}' for x in hand_only))
print('alt-format identical in both:', altfmt['viewer/motion/FACE.yag'] == altfmt['viewer/motion/HAND.yag'],
      f'({len(altfmt["viewer/motion/FACE.yag"])} tracks)')
# which a==0 tracks exist in FACE but not HAND at all (different track sets)?
facer = set(); handr = set()
for p, s in [('viewer/motion/FACE.yag', facer), ('viewer/motion/HAND.yag', handr)]:
    data = read(p)
    for r in dir_records(data):
        if r['a'] == 0: s.add(r['hash'])
print('a==0 in FACE not HAND:', sorted(f'{x:08X}' for x in facer - handr))
print('a==0 in HAND not FACE:', sorted(f'{x:08X}' for x in handr - facer))

print('\n== 3. ECD in viewer/motion/85xx showcase clips ==')
poses = []
for p in sorted(fmap):
    if '/viewer/motion/85' in p and p.endswith('.yag'):
        data = read(p); recs = {r['hash']: r for r in dir_records(data)}
        if ECD in recs:
            _, _, v1, v2 = track_range(data, recs[ECD])
            poses.append((p.split('/')[-1], round(ang(v1),1), round(ang(v2),1)))
print(f'n={len(poses)} distinct poses={len(set((a,b) for _,a,b in poses))}')
for name, a1, a2 in poses: print(f'   {name}: ({a1},{a2})')

print('\n== 4. global: clips with ECD ~ (0,79.9) like FACE ==')
n = 0; names = []
for p in sorted(fmap):
    if not p.endswith('.yag'): continue
    data = read(p)
    if data[:4] != b'YANM': continue
    recs = {r['hash']: r for r in dir_records(data)}
    if ECD in recs:
        _, _, v1, v2 = track_range(data, recs[ECD])
        if abs(ang(v1)) < 1.5 and abs(ang(v2)-79.9) < 1.5:
            n += 1; names.append(p)
print(f'count={n}')
for p in names: print('  ', p)
