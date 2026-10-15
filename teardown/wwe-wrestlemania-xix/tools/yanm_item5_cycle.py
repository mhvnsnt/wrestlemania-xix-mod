#!/usr/bin/env python3
"""YANM watchdog cycle (a)-(d): finger split, 579B thumb test, ECD/0C5B table,
hash-construction via pair-XOR. Streams from ISO; writes docs/YANM-ITEM5-CYCLE.md."""
import sys, struct, math, json
sys.path.insert(0, 'tools')
from gcn_fst import read_header, read_entries, flat_listing

ISO = 'WWE Wrestlemania XIX (USA).iso'
with open(ISO, 'rb') as iso:
    h = read_header(iso); e, nm = read_entries(iso, h['fst_off'], h['fst_size'])
    listing = flat_listing(e, nm)
fmap = {p.strip('/'): (o, l) for p, d, o, l in listing if not d}
_iso = open(ISO, 'rb')
def read(path):
    o, l = fmap[path]
    _iso.seek(o); return _iso.read(l)
def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]
def f32(b, i): return struct.unpack('>f', b[i:i+4])[0]
def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]
def ang(v): return math.degrees(math.asin(max(-1.0, min(1.0, v / 32767.0))))

def dir_records(data):
    recs = []
    for r in range(29):
        o = 0x50 + r * 32
        if o + 32 > len(data): break
        hh, a, ks, w28 = u32(data, o), u32(data, o+4), u32(data, o+8), u32(data, o+28)
        if hh == 0 and ks == 0: break
        recs.append(dict(idx=r, hash=hh, a=a, ks=ks, w28=w28))
    return recs

def decode_single(data, ks, n):
    return [(ang(s16(data, ks+i*5)), data[ks+i*5+2], ang(s16(data, ks+i*5+3))) for i in range(n)]

files = sorted(p for p in fmap if p.startswith('ringmotion/') and p.endswith('.yag'))
print('clips:', len(files))

# ============ (1) ycg side convention -> anatomical L/R ============
ycg = read('model/wrestler/000_0.ycg')
n = u32(ycg, 0)
ycgrecs = []
for r in range(n):
    o = 4 + r*56
    ycgrecs.append({'hash': u32(ycg, o), 'pos': (f32(ycg, o+16), f32(ycg, o+20), f32(ycg, o+24))})
byhash = {}
for r in ycgrecs:
    byhash.setdefault(r['hash'], []).append(r['pos'])
KNOWN_PAIRS = [(0xBD5B2A59, 0xBD5B5259, 'LEG'), (0x6198F425, 0x6198F4D5, 'ARM'),
               (0x5B214D4E, 0x5B214D41, '?'), (0x6865B2CF, 0x6865B2C0, '?'),
               (0x613B75B7, 0x613B7547, '?'), (0x637B70F3, 0x637B7003, '?')]
print('=== (1) ycg y-sign per known pair (ymg: R thigh y=+10.4, L thigh y=-10.4) ===')
for h1, h2, nm in KNOWN_PAIRS:
    y1 = [p[1] for p in byhash.get(h1, [])]
    y2 = [p[1] for p in byhash.get(h2, [])]
    x = h1 ^ h2
    print(f'{nm} {h1:08X}^{h2:08X}=0x{x:X}  y({h1:08X})={[round(v,2) for v in y1[:3]]}  y({h2:08X})={[round(v,2) for v in y2[:3]]}')

# ============ (2) full hash universe + XOR pair census ============
universe = {}
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    for rec in dir_records(data):
        universe.setdefault(rec['hash'], set()).add(path)
hs = sorted(universe)
print('=== (2) hash universe:', len(hs), 'distinct hashes ===')
pairs = []
for i in range(len(hs)):
    for j in range(i+1, len(hs)):
        x = hs[i] ^ hs[j]
        if bin(x).count('1') <= 6 and x < 0x20000000 or (x in (0x1E000000, 0x18000000, 0x1E800000)):
            pairs.append((x, hs[i], hs[j]))
pairs.sort()
print('small-XOR pairs found:', len(pairs))
for x, a, b in pairs:
    na, nb = len(universe[a]), len(universe[b])
    print(f'  {a:08X} ^ {b:08X} = 0x{x:X}  clips={na}/{nb}')

# ============ (3) finger articulation: decoupled ch1/ch2 + grip order ============
FING = (0xA4955E6E, 0xBA955E6E)
def timeline_ch(data, rec):
    keys = decode_single(data, rec['ks'], rec['w28'])
    t1, t2, out1, out2 = 0, 0, [], []
    for c1, dt, c2 in keys:
        for _ in range(max(1, dt)):
            out1.append(c1); out2.append(c2)
        t1 += max(1, dt)
    return out1, out2
print('=== (3) finger decoupled-motion search ===')
decoupled = []
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    recs = {r['hash']: r for r in dir_records(data)}
    for hh in FING:
        if hh not in recs or recs[hh]['a'] != 0: continue
        c1, c2 = timeline_ch(data, recs[hh])
        r1, r2 = max(c1)-min(c1), max(c2)-min(c2)
        if (r1 > 3) != (r2 > 3):  # exactly one channel moves
            decoupled.append((path, f'{hh:08X}', round(min(c1),1), round(max(c1),1), round(min(c2),1), round(max(c2),1)))
print('clips with exactly one finger channel moving:', len(decoupled))
for d in decoupled[:15]: print('   ', d)

# grip-order on c000_0a track10
path = 'ringmotion/c000_0a.yag'
if path in fmap:
    data = read(path)
    recs = {r['hash']: r for r in dir_records(data)}
    for hh in FING:
        if hh in recs and recs[hh]['a'] == 0:
            c1, c2 = timeline_ch(data, recs[hh])
            print(f'--- grip-order {path} track {hh:08X} (n={len(c1)} ticks) ---')
            # find release onset: first tick where either channel moves >1deg from held value
            h1, h2 = sum(c1[:50])/50, sum(c2[:50])/50
            on1 = next((i for i in range(len(c1)) if abs(c1[i]-h1) > 1.0), None)
            on2 = next((i for i in range(len(c2)) if abs(c2[i]-h2) > 1.0), None)
            print(f'  held ch1={h1:.1f} ch2={h2:.1f}; release onset ch1@{on1} ch2@{on2}')
            # re-curl region: last 60 ticks, which channel moves?
            e1 = max(c1[-60:])-min(c1[-60:]); e2 = max(c2[-60:])-min(c2[-60:])
            print(f'  tail60 range ch1={e1:.1f} ch2={e2:.1f}')
            print(f'  ch1 head: {[round(v,1) for v in c1[:6]]} ... tail: {[round(v,1) for v in c1[-6:]]}')
            print(f'  ch2 head: {[round(v,1) for v in c2[:6]]} ... tail: {[round(v,1) for v in c2[-6:]]}')

# ============ (4) 579B thumb test ============
T579 = (0x579B89D0, 0x579B8E50)
print('=== (4) 579B values in c* (grapple) clips vs rest ===')
grip_vals, rest_vals, variants = [], [], []
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    recs = {r['hash']: r for r in dir_records(data)}
    for hh in T579:
        if hh not in recs or recs[hh]['a'] != 0: continue
        c1, c2 = timeline_ch(data, recs[hh])
        r1, r2 = max(c1)-min(c1), max(c2)-min(c2)
        isgrip = '/c' in path
        (grip_vals if isgrip else rest_vals).append((round(c1[0],1), round(c2[0],1)))
        if r1 > 3 or r2 > 3:
            variants.append((path, f'{hh:08X}', round(min(c1),1), round(max(c1),1), round(min(c2),1), round(max(c2),1)))
from collections import Counter
print('grip clips 579B static (ch1,ch2) histogram:', Counter(grip_vals).most_common(5))
print('rest clips 579B static (ch1,ch2) histogram:', Counter(rest_vals).most_common(5))
print('animated 579B clips:', len(variants))
for v in variants[:10]: print('   ', v)

# ============ (5) ECD/0C5B: ymg per-wrestler table ============
print('=== (5) ymg table around 0C5BF279 ===')
for wp in ['model/wrestler/000_0.ymg', 'model/wrestler/001_0.ymg', 'model/wrestler/002_0.ymg']:
    try: ymg = read(wp)
    except KeyError: print(wp, 'MISSING'); continue
    hits = []
    for i in range(0, len(ymg)-4, 4):
        v = u32(ymg, i)
        if v in (0x0C5BF279, 0x40911198, 0xECD28978):
            hits.append((i, v))
    print(f'{wp}: size={len(ymg)} hits={[(hex(i), "%08X"%v) for i,v in hits]}')
    for off, v in hits[:2]:
        words = [u32(ymg, off+k*4) for k in range(-6, 10)]
        print(f'  ctx @{off:#x}:', ' '.join(f'{w:08X}' for w in words))

# ============ (6) ECD correlation with center tracks ============
print('=== (6) ECD28978 correlation vs center singles ===')
def corr(a, b):
    n = min(len(a), len(b)); a, b = a[:n], b[:n]
    ma, mb = sum(a)/n, sum(b)/n
    sa = math.sqrt(sum((x-ma)**2 for x in a)); sb = math.sqrt(sum((x-mb)**2 for x in b))
    if sa == 0 or sb == 0: return float('nan')
    return sum((x-ma)*(y-mb) for x, y in zip(a, b))/(sa*sb)
shown = 0
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    recs = {r['hash']: r for r in dir_records(data)}
    if 0xECD28978 not in recs or recs[0xECD28978]['a'] != 0: continue
    ec1, ec2 = timeline_ch(data, recs[0xECD28978])
    if max(ec1)-min(ec1) < 3 and max(ec2)-min(ec2) < 3: continue
    row = []
    for hh2, r2 in sorted(recs.items(), key=lambda kv: kv[1]['idx']):
        if r2['a'] != 0 or hh2 == 0xECD28978: continue
        o1, o2 = timeline_ch(data, r2)
        c = corr(ec1, o1)
        if not math.isnan(c) and abs(c) > 0.7:
            row.append((r2['idx'], f'{hh2:08X}', round(c,2)))
    if row and shown < 5:
        print(f'  {path}: ECD-ch1 |corr|>0.7 with {row}')
        shown += 1
print('done')
