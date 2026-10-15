#!/usr/bin/env python3
"""YANM item4: identify the 8 unknown track hashes (finger/toe hypothesis).

Measures, across all 170 ringmotion clips:
  (1) which unknowns animate, angle ranges, static rest values
  (2) motion correlation of animated unknowns vs neighboring known tracks
  (3) hash-function battery: ~30 functions x name variants -> 8 unknowns
      (+ 21 knowns as calibration)
Writes docs/YANM-UNKNOWN8.md. Streams from ISO (disk-safe).
"""
import sys, struct, math, json, zlib
sys.path.insert(0, 'tools')
from yukes_fmt import ISO, read_header, read_entries, flat_listing, u32

with open(ISO, 'rb') as iso:
    h = read_header(iso); e, nm = read_entries(iso, h['fst_off'], h['fst_size'])
    listing = flat_listing(e, nm)
fmap = {p.strip('/'): (o, l) for p, d, o, l in listing if not d}
_iso = open(ISO, 'rb')
def read(path):
    o, l = fmap[path]
    _iso.seek(o); return _iso.read(l)

def s16(b): return struct.unpack('>h', b)[0]
def ang(v): return math.degrees(math.asin(max(-1.0, min(1.0, v / 32767.0))))

UNKNOWN = [0x007FD58C, 0x0C5BF279, 0x1E7FD58C, 0x579B89D0,
           0x579B8E50, 0xA4955E6E, 0xBA955E6E, 0xECD28978]
KNOWN21 = [0x347D3654,0x7CC9B660,0x64DB300F,0x095CD669,0x099CD766,0x5B214D4E,
           0x6865B2CF,0x64D45E02,0x60F8F527,0x5B214D41,0x6865B2C0,0x7AD45E02,
           0x60F8F5D7,0xBD5B5259,0x6198F425,0x613B75B7,0x637B70F3,0xBD5B2A59,
           0x6198F4D5,0x613B7547,0x637B7003]

def decode_single(data, ks, n):
    out = []
    for i in range(n):
        o = ks + i * 5
        out.append((ang(s16(data[o:o+2])), data[o+2], ang(s16(data[o+3:o+5]))))
    return out

def dir_records(data):
    recs = []
    for r in range(29):
        o = 0x50 + r * 32
        if o + 32 > len(data): break
        hh, a, ks, w28 = u32(data, o), u32(data, o+4), u32(data, o+8), u32(data, o+28)
        if hh == 0 and ks == 0: break
        recs.append(dict(idx=r, hash=hh, a=a, ks=ks, w28=w28))
    return recs

# ---------- (1) census: animation + static values ----------
files = sorted(p for p in fmap if p.startswith('ringmotion/') and p.endswith('.yag'))
census = {hh: {'n_anim': 0, 'clips': [], 'static_vals': []} for hh in UNKNOWN}
for path in files:
    data = read(path)
    if data[:4] != b'YANM': continue
    for rec in dir_records(data):
        hh = rec['hash']
        if hh not in census: continue
        if rec['a'] == 0:
            keys = decode_single(data, rec['ks'], rec['w28'])
            c1 = [k[0] for k in keys]; c2 = [k[2] for k in keys]
            r1, r2 = max(c1)-min(c1), max(c2)-min(c2)
            if r1 > 2 or r2 > 2:
                census[hh]['n_anim'] += 1
                census[hh]['clips'].append((path, rec['idx'], round(min(c1),1), round(max(c1),1), round(min(c2),1), round(max(c2),1), rec['w28']))
            else:
                census[hh]['static_vals'].append((round(c1[0],1), round(c2[0],1)))
        else:
            ca, cb = (rec['w28'] >> 16) & 0xFFFF, rec['w28'] & 0xFFFF
            vs = set()
            for i in range(cb):
                bo = rec['ks'] + i * 5
                vs.add((s16(data[bo:bo+2]), s16(data[bo+3:bo+5])))
            if len(vs) > 1:
                census[hh]['n_anim'] += 1
                census[hh]['clips'].append((path, rec['idx'], 'dual', len(vs), ca, cb))

print('=== (1) animation census over %d clips ===' % len(files))
for hh in UNKNOWN:
    c = census[hh]
    sv = c['static_vals'][:3]
    print(f'{hh:08X}: anim_clips={c["n_anim"]} static_ex={sv}')
    for ex in c['clips'][:6]:
        print(f'    {ex}')

# ---------- (2) correlation: animated unknown vs run neighbors ----------
def timeline(data, rec):
    keys = decode_single(data, rec['ks'], rec['w28'])
    # expand by dt to a per-tick series (ch2 only, the moving one usually)
    ticks, v = [], []
    t = 0
    for c1, dt, c2 in keys:
        for _ in range(max(1, dt)):
            ticks.append(t); v.append(c2); t += 1
    return v

def corr(a, b):
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    ma, mb = sum(a)/n, sum(b)/n
    sa = math.sqrt(sum((x-ma)**2 for x in a)); sb = math.sqrt(sum((x-mb)**2 for x in b))
    if sa == 0 or sb == 0: return float('nan')
    return sum((x-ma)*(y-mb) for x, y in zip(a, b)) / (sa*sb)

print('=== (2) correlation of animated unknowns vs neighbors ===')
for hh in UNKNOWN:
    for (path, idx, *rest) in census[hh]['clips'][:4]:
        if rest[0] == 'dual': continue
        data = read(path)
        recs = {r['idx']: r for r in dir_records(data)}
        u = timeline(data, recs[idx])
        row = []
        for j in sorted(recs):
            if recs[j]['a'] != 0: continue
            v = timeline(data, recs[j])
            row.append((j, f"{recs[j]['hash']:08X}", round(corr(u, v), 3) if not math.isnan(corr(u,v)) else 'nan'))
        print(f'{hh:08X}@{idx} in {path}:')
        print('   ', row)

with open('/tmp/unknown8_census.json', 'w') as f:
    json.dump({f'{k:08X}': v for k, v in census.items()}, f, indent=1)
print('census -> /tmp/unknown8_census.json')
