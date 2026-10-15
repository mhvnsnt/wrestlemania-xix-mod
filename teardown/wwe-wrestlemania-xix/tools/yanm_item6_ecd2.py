#!/usr/bin/env python3
"""YANM item-6 ECD probe part 2: mirror variants, slot-entity clips, ECD~thumb
correlation, ECD-less clips, letter-8 clips. Streams from ISO."""
import sys, struct, math, os
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

def dir_records(data):
    recs = []
    for r in range(60):
        o = 0x50 + r * 32
        if o + 32 > len(data): break
        hh, a, ks, w28 = u32(data, o), u32(data, o+4), u32(data, o+8), u32(data, o+28)
        if hh == 0 and ks == 0: break
        recs.append(dict(idx=r, hash=hh, a=a, ks=ks, w28=w28))
    return recs

def ecd_pose(data, recs):
    if 0xECD28978 not in recs: return None
    er = recs[0xECD28978]
    v1 = s16(data, er['ks']); v2 = s16(data, er['ks']+3)
    return (round(ang(v1),1), round(ang(v2),1))

files = sorted(p for p in fmap if p.endswith('.yag'))

# ---- A. slot-entity clips (all 7) ----
SLOT_IDS = {0x8102,0x9202,0x9302,0x9D02,0x9E02,0xD402,0xD502}
print('== slot-entity clips ==')
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    recs = {r['hash']: r for r in dir_records(data)}
    slots = [f'{hh:08X}' for hh in recs if hh in SLOT_IDS]
    if slots:
        print('  ', path, 'slots=', slots, 'ECD=', ecd_pose(data, recs),
              'has0C5B=', 0x0C5BF279 in recs, 'ntracks=', len(recs))

# ---- B. variant pairs: same stem, different variant suffix ----
print('\n== variant pairs (same move, _0a vs _1a/_0b/_2a) ==')
by_stem = defaultdict(list)
for path in files:
    name = path.split('/')[-1]
    stem = name[:-6]  # strip _XY.yag
    by_stem[stem].append(path)
for stem, ps in sorted(by_stem.items()):
    if len(ps) > 1:
        for p in sorted(ps):
            data = read(p)
            if data[:4] != b'YANM': continue
            recs = {r['hash']: r for r in dir_records(data)}
            print('  ', p.split('/')[-1], 'ECD=', ecd_pose(data, recs))

# ---- C. ECD-less clips ----
print('\n== clips WITHOUT ECD track ==')
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    recs = {r['hash']: r for r in dir_records(data)}
    if 0xECD28978 not in recs:
        print('  ', path, 'ntracks=', len(recs), 'has0C5B=', 0x0C5BF279 in recs)

# ---- D. letter-8 clips: which dir, what are they ----
print('\n== letter-8 clips ==')
c8 = [p for p in files if p.split('/')[-1][0] == '8']
print('  n=', len(c8), 'dirs=', Counter(os.path.dirname(p) for p in c8))
for p in c8[:8]: print('   ', p)

# ---- E. ECD ch2 vs thumb ch2 continuous correlation ----
print('\n== ECD ch2 vs thumb ch2 (same-side thumb 579B8E50 / 579B89D0) ==')
xs, ys = [], []
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    recs = {r['hash']: r for r in dir_records(data)}
    if 0xECD28978 not in recs or recs[0xECD28978]['a'] != 0: continue
    er = recs[0xECD28978]
    e2 = ang(s16(data, er['ks']+3))
    for hh in (0x579B89D0, 0x579B8E50):
        if hh in recs and recs[hh]['a'] == 0:
            t2 = ang(s16(data, recs[hh]['ks']+3))
            xs.append(e2); ys.append(t2)
n = len(xs)
mx, my = sum(xs)/n, sum(ys)/n
cov = sum((x-mx)*(y-my) for x, y in zip(xs, ys))/n
sx = (sum((x-mx)**2 for x in xs)/n)**0.5
sy = (sum((y-my)**2 for y in ys)/n)**0.5
print(f'  n={n} pearson r(ECDch2, thumbch2) = {cov/(sx*sy):.3f}')
# also ch1 vs thumb ch1
xs1 = []
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    recs = {r['hash']: r for r in dir_records(data)}
    if 0xECD28978 not in recs or recs[0xECD28978]['a'] != 0: continue
    er = recs[0xECD28978]
    e1 = ang(s16(data, er['ks']))
    for hh in (0x579B89D0, 0x579B8E50):
        if hh in recs and recs[hh]['a'] == 0:
            t1 = ang(s16(data, recs[hh]['ks']))
            xs1.append((e1, t1))
n = len(xs1)
mx, my = sum(x for x,y in xs1)/n, sum(y for x,y in xs1)/n
cov = sum((x-mx)*(y-my) for x, y in xs1)/n
sx = (sum((x-mx)**2 for x,y in xs1)/n)**0.5
sy = (sum((y-my)**2 for x,y in xs1)/n)**0.5
print(f'  n={n} pearson r(ECDch1, thumbch1) = {cov/(sx*sy):.3f}')

# ---- F. ECD vs 0C5B pose correlation (both static selectors) ----
print('\n== ECD pose vs 0C5B pose ==')
pairs = []
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    recs = {r['hash']: r for r in dir_records(data)}
    if 0xECD28978 in recs and 0x0C5BF279 in recs and recs[0xECD28978]['a'] == 0:
        er = recs[0xECD28978]; zr = recs[0x0C5BF279]
        e1 = ang(s16(data, er['ks'])); e2 = ang(s16(data, er['ks']+3))
        z1 = ang(s16(data, zr['ks'])); z2 = ang(s16(data, zr['ks']+3))
        pairs.append((e1, e2, z1, z2))
print('  n=', len(pairs), '0C5B distinct poses=', len(Counter((round(a,1),round(b,1)) for a,b,c,d in pairs)))
def corr(xs, ys):
    n = len(xs); mx, my = sum(xs)/n, sum(ys)/n
    cov = sum((x-mx)*(y-my) for x, y in zip(xs, ys))/n
    sx = (sum((x-mx)**2 for x in xs)/n)**0.5; sy = (sum((y-my)**2 for y in ys)/n)**0.5
    return cov/(sx*sy) if sx and sy else 0.0
print('  r(ECDch1,0C5Bch1)=%.3f r(ECDch2,0C5Bch2)=%.3f' % (
    corr([a for a,b,c,d in pairs],[c for a,b,c,d in pairs]),
    corr([b for a,b,c,d in pairs],[d for a,b,c,d in pairs])))
print('  0C5B top poses:', Counter((round(c,1),round(d,1)) for a,b,c,d in pairs).most_common(6))
print('done')
