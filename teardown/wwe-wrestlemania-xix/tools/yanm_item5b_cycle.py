#!/usr/bin/env python3
"""YANM watchdog cycle part 2: 579B<->finger correlation, ycg side_bit->anatomical,
root hash battery, ECD static analysis, ymg table structure. Streams from ISO."""
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

def ch_series(data, rec):
    keys = decode_single(data, rec['ks'], rec['w28'])
    c1, c2 = [], []
    for a, dt, b in keys:
        for _ in range(max(1, dt)):
            c1.append(a); c2.append(b)
    return c1, c2

files = sorted(p for p in fmap if p.startswith('ringmotion/') and p.endswith('.yag'))

# ============ (A) 579B pose vs finger grip-release per c* clip ============
print('=== (A) 579B pose vs finger animation in grapple clips ===')
rows = []
for path in files:
    if '/c' not in path: continue
    data = read(path)
    if data[:4] != b'YANM': continue
    recs = {r['hash']: r for r in dir_records(data)}
    fing_anim = []
    for hh in (0xA4955E6E, 0xBA955E6E):
        if hh in recs and recs[hh]['a'] == 0:
            c1, c2 = ch_series(data, recs[hh])
            if max(c1)-min(c1) > 3 or max(c2)-min(c2) > 3:
                fing_anim.append(f'{hh:08X}')
    t579 = []
    for hh in (0x579B89D0, 0x579B8E50):
        if hh in recs and recs[hh]['a'] == 0:
            c1, c2 = ch_series(data, recs[hh])
            t579.append((f'{hh:08X}', round(c1[0],1), round(c2[0],1)))
    if fing_anim or t579:
        rows.append((path.split('/')[-1], fing_anim, t579))
print('c* clips with finger anim and/or 579B non-default:', len(rows))
for r in rows[:40]:
    print('  ', r[0], 'fing_anim=', r[1], 't579=', r[2])

# ============ (B) ycg side_bit -> anatomical: compare ycg LEG pos vs ymg thigh ============
print('=== (B) ycg LEG record full pos vs ymg thigh pos ===')
ycg = read('model/wrestler/000_0.ycg')
n = u32(ycg, 0)
for r in range(n):
    o = 4 + r*56
    hh = u32(ycg, o)
    if hh in (0xBD5B2A59, 0xBD5B5259):
        pos = (f32(ycg, o+16), f32(ycg, o+20), f32(ycg, o+24))
        quat = tuple(round(f32(ycg, o+28+k*4), 4) for k in range(4))
        w0 = u32(ycg, o+4)
        print(f'  rec{r} hash={hh:08X} w0={w0} pos=({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f}) quat={quat} len={f32(ycg,o+44):.2f}')
print('  ymg: Bip R Thigh pos=(-0.14, 10.40, -0.00); Bip L Thigh pos=(-0.14, -10.40, -0.00)')

# ============ (C) root hash battery (side bits cleared) ============
print('=== (C) root battery ===')
SIDE_MASKS = [0x0F, 0xF0, 0x780, 0x7800, 0x1E000000, 0xA0, 0xA00]
CORE = [0x347D3654,0x7CC9B660,0x64DB300F,0x095CD669,0x099CD766,0x5B214D4E,
        0x6865B2CF,0x64D45E02,0x60F8F527,0x5B214D41,0x6865B2C0,0x7AD45E02,
        0x60F8F5D7,0xBD5B5259,0x6198F425,0x613B75B7,0x637B70F3,0xBD5B2A59,
        0x6198F4D5,0x613B7547,0x637B7003]
UNK = [0x007FD58C,0x0C5BF279,0x1E7FD58C,0x579B89D0,0x579B8E50,0xA4955E6E,0xBA955E6E,0xECD28978]
def roots(h):
    out = {h}
    for m in SIDE_MASKS:
        out.add(h & ~m)
    return out
targets = set()
for hh in CORE + UNK:
    targets |= roots(hh)
print('target roots:', len(targets))

def lin_hashes(name_bytes):
    b = name_bytes
    out = {}
    out['sum8'] = sum(b) & 0xFFFFFFFF
    out['sum32be'] = sum(struct.unpack('>%dI' % (len(b)//4), b[:len(b)//4*4])) & 0xFFFFFFFF if len(b) >= 4 else 0
    x = 0
    for c in b: x = (x + c) & 0xFFFFFFFF
    out['add'] = x
    x = 0
    for c in b: x ^= c
    out['xor8'] = x
    for poly, nm in ((31, 'p31'), (33, 'p33'), (131, 'p131'), (65599, 'p65599')):
        x = 0
        for c in b: x = (x * poly + c) & 0xFFFFFFFF
        out[nm] = x
        x = 0
        for c in b: x = (x * poly ^ c) & 0xFFFFFFFF
        out[nm+'x'] = x
    x = 0xFFFFFFFF
    for c in b: x = ((x >> 8) ^ (c * 2654435761)) & 0xFFFFFFFF
    out['mix'] = x
    return out

names = []
skel = json.load(open('docs/wrestler-skeleton-000.json'))
for b in skel:
    names.append(b['name'])
extra = ['Finger0','Finger1','Finger2','Finger3','Finger4','Finger01','Finger11','Thumb',
         'finger','thumb','toe','hand','Bip Finger','R Finger','L Finger']
names += extra
variants = set()
for nm in names:
    for v in (nm, nm.lower(), nm.upper(), nm.replace(' ', '_'), nm.replace(' ', ''),
              nm.replace('Bip ', '').replace('Bip', ''), 'Bip' + nm):
        variants.add(v)
        variants.add(v + '\x00')
hits = []
for v in variants:
    for enc in ('ascii', 'utf-16-le'):
        try: bb = v.encode(enc)
        except Exception: continue
        for fn, hv in lin_hashes(bb).items():
            if hv in targets:
                hits.append((v, enc, fn, f'{hv:08X}'))
print('root battery hits:', len(hits))
for hh_ in hits[:20]: print('  HIT', hh_)

# ============ (D) ECD static-value analysis ============
print('=== (D) ECD28978 static values by clip letter ===')
from collections import Counter, defaultdict
ec = defaultdict(list)
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    recs = {r['hash']: r for r in dir_records(data)}
    if 0xECD28978 not in recs or recs[0xECD28978]['a'] != 0: continue
    c1, c2 = ch_series(data, recs[0xECD28978])
    letter = path.split('/')[-1][0]
    ec[letter].append((round(c1[0],1), round(c2[0],1), round(max(c1)-min(c1),1)))
for L in sorted(ec):
    c = Counter((a, b) for a, b, r in ec[L])
    anim = sum(1 for a, b, r in ec[L] if r > 3)
    print(f'  letter {L}: n={len(ec[L])} animated={anim} top_static={c.most_common(4)}')
# is ECD in any ycg?
found = [hh for hh in (0xECD28978, 0x0C5BF279) if hh in [u32(ycg, 4+r*56) for r in range(n)]]
print('  ECD/0C5B in 000_0.ycg hashes:', [f'{x:08X}' for x in found])
# is 40911198 a yag track anywhere?
u = set()
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    for r in dir_records(data): u.add(r['hash'])
print('  40911198 in yag universe:', 0x40911198 in u, '| ECD28978 clips:', sum(1 for p in files if True))

# ============ (E) ymg table structure: wide dump + entry scan ============
print('=== (E) ymg table wide dump (000_0 @0x10c00-0x10f00) ===')
ymg = read('model/wrestler/000_0.ymg')
for base in (0x10c00, 0x10d40, 0x10e80):
    print(f'  @{base:#x}:')
    for row in range(0, 0xc0, 0x10):
        o = base + row
        print('   ', ' '.join(f'{u32(ymg, o+k):08X}' for k in range(0, 16, 4)))
# scan whole ymg for all 8 unknown hashes + roots
print('  full-ymg scan for unknown hashes:')
allh = [0x007FD58C,0x0C5BF279,0x1E7FD58C,0x579B89D0,0x579B8E50,0xA4955E6E,0xBA955E6E,0xECD28978,0x40911198]
for target in allh:
    hits = [i for i in range(0, len(ymg)-4, 4) if u32(ymg, i) == target]
    if hits: print(f'    {target:08X}: {[hex(x) for x in hits]}')
print('done')
