#!/usr/bin/env python3
"""YANM item-6 (cycle): ECD28978 identity probes.
Streams from ISO. Measured only.
Probes:
 1. raw s16 values per channel (enum? angle?); distinct value sets ch1 vs ch2;
    9x9-grid independence test (chi-square + co-occurrence matrix density).
 2. ECD pose by clip category (letter a/b/c/d, ringmotion vs viewer).
 3. ECD vs 0C5BF279 presence (clips lacking it).
 4. ECD vs finger/thumb animation contingency (same-side table like 579B).
 5. ECD vs slot-entity tracks ((slot<<8)|0x02) presence -> second performer?
 6. ECD vs per-clip duals (CD9640DA/FE9A7A50 variants).
"""
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
    for r in range(40):
        o = 0x50 + r * 32
        if o + 32 > len(data): break
        hh, a, ks, w28 = u32(data, o), u32(data, o+4), u32(data, o+8), u32(data, o+28)
        if hh == 0 and ks == 0: break
        recs.append(dict(idx=r, hash=hh, a=a, ks=ks, w28=w28))
    return recs

def static_pose(data, rec):
    v1 = s16(data, rec['ks']); v2 = s16(data, rec['ks']+3)
    return v1, v2, round(ang(v1), 1), round(ang(v2), 1)

files = sorted(p for p in fmap if p.endswith('.yag'))
print('yag clips:', len(files))

rows = []  # (path, letter, dir, ecd_raw1, ecd_raw2, ecd_a1, ecd_a2, ecd_anim_range,
           #  has_0c5b, fing_anim, thumb_nondef, slot_entities, perclip_duals)
SLOT_IDS = {0x8102, 0x9202, 0x9302, 0x9D02, 0x9E02, 0xD402, 0xD502}
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    recs = {r['hash']: r for r in dir_records(data)}
    name = path.split('/')[-1]
    d = os.path.dirname(path)
    if 0xECD28978 not in recs:
        rows.append((path, name[0], d, None, None, None, None, None, False, [], False, [], []))
        continue
    er = recs[0xECD28978]
    c1, c2 = [], []
    for i in range(er['w28']):
        o = er['ks'] + i * 5
        c1.append(s16(data, o)); c2.append(s16(data, o+3))
    e_range = max(max(c1)-min(c1), max(c2)-min(c2))
    r1, r2 = c1[0], c2[0]
    fa = []
    for hh in (0xA4955E6E, 0xBA955E6E):
        if hh in recs and recs[hh]['a'] == 0:
            s1 = [s16(data, recs[hh]['ks']+i*5) for i in range(recs[hh]['w28'])]
            s2 = [s16(data, recs[hh]['ks']+i*5+3) for i in range(recs[hh]['w28'])]
            if max(s1)-min(s1) > 1000 or max(s2)-min(s2) > 1000:
                fa.append(f'{hh:08X}')
    tn = False
    for hh in (0x579B89D0, 0x579B8E50):
        if hh in recs and recs[hh]['a'] == 0:
            p = static_pose(data, recs[hh])
            if abs(p[2]) > 3 and abs(p[3]-80) > 3 or abs(p[2]) > 3 and abs(p[3]) > 3:
                tn = True
    slots = [f'{hh:08X}' for hh in recs if hh in SLOT_IDS]
    du = [f'{hh:08X}' for hh in recs
          if (hh & 0xFFFFFF00) in (0xCD964000, 0xFE9A7A00) and hh not in (0xCD9642DA, 0xCD9648DA, 0xFE9A7A50, 0xFE9A7AF0)]
    rows.append((path, name[0], d, r1, r2, round(ang(r1),1), round(ang(r2),1),
                 e_range, 0x0C5BF279 in recs, fa, tn, slots, du))

have = [r for r in rows if r[3] is not None]
print('clips with ECD track:', len(have), '/', len(rows))
print('ECD animated within clip (range>1000 raw):', sum(1 for r in have if r[7] > 1000))

# ---- 1. raw values + distinct sets ----
c1v = Counter(r[3] for r in have); c2v = Counter(r[4] for r in have)
print('\n== ch1 distinct raw values:', len(c1v))
for v, n in c1v.most_common(15): print(f'   raw={v:6d} ang={ang(v):7.2f} n={n}')
print('== ch2 distinct raw values:', len(c2v))
for v, n in c2v.most_common(15): print(f'   raw={v:6d} ang={ang(v):7.2f} n={n}')
joint = Counter((r[3], r[4]) for r in have)
print('joint distinct (raw1,raw2):', len(joint))
print('product bound:', len(c1v)*len(c2v), '| coverage:', round(len(joint)/(len(c1v)*len(c2v)), 3))
# independence: expected count under independence vs observed, chi-square
tot = len(have)
chi2 = 0.0
for v1 in c1v:
    for v2 in c2v:
        e = c1v[v1]*c2v[v2]/tot
        o = joint.get((v1, v2), 0)
        chi2 += (o-e)**2/e if e else 0
dof = (len(c1v)-1)*(len(c2v)-1)
print(f'chi-square independence: {chi2:.1f} dof={dof} (indep. => ~dof)')

# ---- 2. by clip category ----
print('\n== ECD pose by clip letter (static poses only) ==')
by = defaultdict(list)
for r in have:
    by[r[1]].append((r[5], r[6]))
for L in sorted(by):
    c = Counter(by[L])
    print(f'  letter {L}: n={len(by[L])} distinct={len(c)} top={c.most_common(5)}')
print('== by dir ==')
byd = defaultdict(list)
for r in have:
    byd[r[2]].append((r[5], r[6]))
for d in sorted(byd):
    c = Counter(byd[d])
    print(f'  {d}: n={len(byd[d])} distinct={len(c)} top={c.most_common(5)}')

# ---- 3. ECD vs 0C5BF279 presence ----
print('\n== ECD vs 0C5BF279 presence ==')
no0c = [r for r in rows if not r[8]]
print('clips lacking 0C5BF279:', len(no0c))
c = Counter((r[5], r[6]) for r in no0c if r[3] is not None)
print('  their ECD poses:', c.most_common(10))
print('  lacking-0C5B by letter:', Counter(r[1] for r in no0c))
yes0c = [r for r in have if r[8]]
print('  with-0C5B ECD distinct poses:', len(Counter((r[5], r[6]) for r in yes0c)))

# ---- 4. ECD vs finger/thumb anim contingency ----
print('\n== ECD vs finger anim ==')
def ecd_nondef(r): return abs(r[5]) > 3 or abs(r[6]-80) > 3 and abs(r[6]) > 3
# use: ECD pose != (0,0) and != (0,80)-rest? define non-rest = not (0,0)
def ecd_rest(r): return abs(r[5]) < 3 and abs(r[6]) < 3
fa_yes = [r for r in have if r[9]]; fa_no = [r for r in have if not r[9]]
print('  finger anim clips: n=%d, ECD non-(0,0): %d/%d' % (
    len(fa_yes), sum(1 for r in fa_yes if not ecd_rest(r)), len(fa_yes)))
print('  finger static clips: n=%d, ECD non-(0,0): %d/%d' % (
    len(fa_no), sum(1 for r in fa_no if not ecd_rest(r)), len(fa_no)))
print('== ECD pose when fingers animate (top) ==')
print('  ', Counter((r[5], r[6]) for r in fa_yes).most_common(10))
print('== thumb non-default vs ECD ==')
tn_yes = [r for r in have if r[10]]; tn_no = [r for r in have if not r[10]]
print('  thumb nondef n=%d ECD top=%s' % (len(tn_yes), Counter((r[5],r[6]) for r in tn_yes).most_common(5)))
print('  thumb default  n=%d ECD top=%s' % (len(tn_no), Counter((r[5],r[6]) for r in tn_no).most_common(5)))

# ---- 5. slot entities ----
print('\n== ECD vs slot-entity tracks ==')
slotrows = [r for r in have if r[11]]
print('clips with slot entities:', len(slotrows))
for r in slotrows:
    print('  ', r[0].split('/')[-1], 'slots=', r[11], 'ECD=', (r[5], r[6]))

# ---- 6. per-clip duals ----
print('\n== per-clip dual variants present ==')
from collections import Counter as C2
print(C2(tuple(r[12]) for r in have).most_common(8))
# ECD pose for clips carrying FE9A7A50/FE9A7AF0 vs CD964x
def has(r, pre):
    return any(x.startswith(pre) for x in r[12] + [f'{hh:08X}' for hh in []])
print('done')
