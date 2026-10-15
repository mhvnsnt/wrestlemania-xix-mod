#!/usr/bin/env python3
"""YANM item4: hash-function battery for the 8 unknown track hashes.

Tries ~35 hash functions x ~15 name variants against:
  - the 8 unknown hashes (target)
  - the 21 known track hashes (calibration: a (fn, variant) hitting a known
    with a plausible bone name validates the approach)
Also tests the pair-XOR structure: for each fn, checks whether L/R name
variants produce the small-XOR differences observed in real pairs.
"""
import sys, struct, zlib
sys.path.insert(0, 'tools')
from yukes_fmt import ISO, read_header, read_entries, flat_listing

UNKNOWN = [0x007FD58C, 0x0C5BF279, 0x1E7FD58C, 0x579B89D0,
           0x579B8E50, 0xA4955E6E, 0xBA955E6E, 0xECD28978]
KNOWN21 = [0x347D3654,0x7CC9B660,0x64DB300F,0x095CD669,0x099CD766,0x5B214D4E,
           0x6865B2CF,0x64D45E02,0x60F8F527,0x5B214D41,0x6865B2C0,0x7AD45E02,
           0x60F8F5D7,0xBD5B5259,0x6198F425,0x613B75B7,0x637B70F3,0xBD5B2A59,
           0x6198F4D5,0x613B7547,0x637B7003]
TARGETS = set(UNKNOWN) | set(KNOWN21)

# ---------------- hash functions (all pure python, 32-bit outputs) ----------------
def h_crc32(s): return zlib.crc32(s) & 0xFFFFFFFF
def h_crc32_bzip2(s):
    crc, poly = 0xFFFFFFFF, 0x04C11DB7
    for b in s:
        crc ^= b << 24
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & 0xFFFFFFFF if crc & 0x80000000 else (crc << 1) & 0xFFFFFFFF
    return crc ^ 0xFFFFFFFF
def h_fnv1a32(s):
    h = 0x811C9DC5
    for b in s: h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return h
def h_fnv132(s):
    h = 0x811C9DC5
    for b in s: h = ((h * 0x01000193) ^ b) & 0xFFFFFFFF
    return h
def h_fnv1a64(s):
    h = 0xCBF29CE484222325
    for b in s: h = ((h ^ b) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h & 0xFFFFFFFF
def h_djb2(s):
    h = 5381
    for b in s: h = ((h * 33) + b) & 0xFFFFFFFF
    return h
def h_djb2a(s):
    h = 5381
    for b in s: h = ((h * 33) ^ b) & 0xFFFFFFFF
    return h
def h_sdbm(s):
    h = 0
    for b in s: h = (b + (h << 6) + (h << 16) - h) & 0xFFFFFFFF
    return h
def h_loselose(s):
    h = 0
    for b in s: h = (h + b) & 0xFFFFFFFF
    return h
def h_elf(s):
    h = 0
    for b in s:
        h = ((h << 4) + b) & 0xFFFFFFFF
        x = h & 0xF0000000
        if x: h ^= (x >> 24); h &= ~x & 0xFFFFFFFF
    return h & 0xFFFFFFFF
def h_jenkins(s):
    h = 0
    for b in s:
        h = (h + b) & 0xFFFFFFFF; h = (h + (h << 10)) & 0xFFFFFFFF; h ^= (h >> 6)
    h = (h + (h << 3)) & 0xFFFFFFFF; h ^= (h >> 11); h = (h + (h << 15)) & 0xFFFFFFFF
    return h
def h_dek(s):
    h = len(s)
    for b in s: h = (((h << 5) ^ (h >> 27)) ^ b) & 0xFFFFFFFF
    return h
def h_bp(s):
    h = 0
    for b in s: h = ((h << 7) ^ b) & 0xFFFFFFFF
    return h
def h_ap(s):
    h = 0xAAAAAAAA
    for i, b in enumerate(s):
        if i & 1: h ^= ((h << 7) ^ b * (h >> 3)) & 0xFFFFFFFF
        else: h ^= ((~((h << 11) + (b ^ (h >> 5)))) & 0xFFFFFFFF)
    return h & 0xFFFFFFFF
def h_js(s):
    h = 1315423911
    for b in s: h ^= ((h << 5) + b + (h >> 2)) & 0xFFFFFFFF
    return h & 0xFFFFFFFF
def h_rs(s):
    a, h = 63689, 0
    for b in s: h = (h * a + b) & 0xFFFFFFFF; a = (a * 378551) & 0xFFFFFFFF
    return h
def h_bkdr31(s):
    h = 0
    for b in s: h = (h * 31 + b) & 0xFFFFFFFF
    return h
def h_bkdr131(s):
    h = 0
    for b in s: h = (h * 131 + b) & 0xFFFFFFFF
    return h
def h_murmur2(s, seed=0):
    m, r = 0x5BD1E995, 24
    h = (seed ^ len(s)) & 0xFFFFFFFF
    n = len(s) - len(s) % 4
    for i in range(0, n, 4):
        k = struct.unpack('<I', s[i:i+4])[0]
        k = (k * m) & 0xFFFFFFFF; k ^= k >> r; k = (k * m) & 0xFFFFFFFF
        h = (h * m) & 0xFFFFFFFF; h ^= k
    tail = s[n:]
    if len(tail) >= 3: h ^= tail[2] << 16
    if len(tail) >= 2: h ^= tail[1] << 8
    if len(tail) >= 1: h ^= tail[0]; h = (h * m) & 0xFFFFFFFF
    h ^= h >> 13; h = (h * m) & 0xFFFFFFFF; h ^= h >> 15
    return h
def _mm3_fmix(h):
    h ^= h >> 16; h = (h * 0x85EBCA6B) & 0xFFFFFFFF; h ^= h >> 13
    h = (h * 0xC2B2AE35) & 0xFFFFFFFF; h ^= h >> 16
    return h
def h_murmur3(s, seed=0):
    c1, c2 = 0xCC9E2D51, 0x1B873593
    h = seed; n = len(s) - len(s) % 4
    for i in range(0, n, 4):
        k = struct.unpack('<I', s[i:i+4])[0]
        k = (k * c1) & 0xFFFFFFFF; k = ((k << 15) | (k >> 17)) & 0xFFFFFFFF; k = (k * c2) & 0xFFFFFFFF
        h ^= k; h = ((h << 13) | (h >> 19)) & 0xFFFFFFFF; h = (h * 5 + 0xE6546B64) & 0xFFFFFFFF
    k = 0
    tail = s[n:]
    if len(tail) == 3: k ^= tail[2] << 16
    if len(tail) >= 2: k ^= tail[1] << 8
    if len(tail) >= 1:
        k ^= tail[0]; k = (k * c1) & 0xFFFFFFFF; k = ((k << 15) | (k >> 17)) & 0xFFFFFFFF
        k = (k * c2) & 0xFFFFFFFF; h ^= k
    h ^= len(s); return _mm3_fmix(h)
def h_xxh32(s, seed=0):
    P1, P2, P3, P4, P5 = 0x9E3779B1, 0x85EBCA77, 0xC2B2AE3D, 0x27D4EB2F, 0x165667B1
    def rol(x, r): return ((x << r) | (x >> (32 - r))) & 0xFFFFFFFF
    n = len(s); i = 0; h = 0
    if n >= 16:
        v = [(seed + P1 + P2), (seed + P2), seed, (seed - P1)]
        while i + 16 <= n:
            for j in range(4):
                v[j] = rol((v[j] + struct.unpack('<I', s[i+j*4:i+j*4+4])[0] * P2) & 0xFFFFFFFF, 13)
                v[j] = (v[j] * P1) & 0xFFFFFFFF
            i += 16
        h = rol(v[0], 1) + rol(v[1], 7) + rol(v[2], 12) + rol(v[3], 18)
    h = (h + n) & 0xFFFFFFFF
    while i + 4 <= n:
        h = (rol((h + struct.unpack('<I', s[i:i+4])[0] * P3) & 0xFFFFFFFF, 17) * P4) & 0xFFFFFFFF; i += 4
    while i < n:
        h = (rol((h + s[i] * P5) & 0xFFFFFFFF, 11) * P1) & 0xFFFFFFFF; i += 1
    h ^= h >> 15; h = (h * P2) & 0xFFFFFFFF; h ^= h >> 13; h = (h * P3) & 0xFFFFFFFF; h ^= h >> 16
    return h
def h_adler32(s): return zlib.adler32(s) & 0xFFFFFFFF

FNS = {n: f for n, f in sorted(globals().items()) if n.startswith('h_') and callable(f)
       and n not in ('h_crc32_bzip2',)}
FNS['h_crc32_bzip2'] = h_crc32_bzip2
for _seed in (1, 0x9747B28C):
    FNS[f'h_murmur2_s{_seed:08X}'] = (lambda sd: (lambda s: h_murmur2(s, sd)))(_seed)
    FNS[f'h_murmur3_s{_seed:08X}'] = (lambda sd: (lambda s: h_murmur3(s, sd)))(_seed)

# ---------------- name candidates ----------------
with open(ISO, 'rb') as iso:
    h = read_header(iso); e, nm = read_entries(iso, h['fst_off'], h['fst_size'])
    listing = flat_listing(e, nm)
fmap = {p.strip('/'): (o, l) for p, d, o, l in listing if not d}
_iso = open(ISO, 'rb')
o, l = fmap['model/wrestler/000_0.ymg']; _iso.seek(o); ymg = _iso.read(l)
bonenames = []
for s_ in range(1, 71):
    bo = 0xF3BC + s_ * 64
    bonenames.append(ymg[bo:bo+16].split(b'\x00')[0].decode('ascii', 'replace'))

def variants(name):
    v = {name}
    v.add(name.lower()); v.add(name.upper())
    v.add(name.replace(' ', '_')); v.add(name.replace(' ', ''))
    v.add(name.replace('Bip ', '').replace('Bip', ''))
    v.add(name.replace('Bip ', '').replace(' ', '_'))
    low = name.lower().replace(' ', '_')
    v.add(low)
    # side prefix/suffix moves
    for side in ('R', 'L', 'r', 'l', 'Right', 'Left', 'RIGHT', 'LEFT'):
        core = name
        for tok in ('R ', 'L ', 'r ', 'l ', 'Bip R ', 'Bip L ', 'right_', 'left_', 'r_', 'l_'):
            if core.startswith(tok): core = core[len(tok):]; break
        v.add(side + '_' + core); v.add(side + core); v.add(core + '_' + side); v.add(core + side)
    v.add(name + '\x00')
    return {x for x in v if x}

print(f'{len(FNS)} hash functions x ~{len(bonenames)} bone names (+variants)')
nhit = 0
for fname, fn in FNS.items():
    for bn in bonenames:
        for cand in variants(bn):
            for enc in (lambda x: x.encode('ascii', 'ignore'), lambda x: x.encode('utf-16-le')):
                try: hv = fn(enc(cand))
                except Exception: continue
                if hv in TARGETS:
                    tag = 'UNKNOWN' if hv in UNKNOWN else 'known'
                    print(f'HIT {fname}("{cand}") [{enc.__name__ if hasattr(enc,"__name__") else "enc"}] = {hv:08X} ({tag})')
                    nhit += 1
print('total hits:', nhit)
