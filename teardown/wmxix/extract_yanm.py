#!/usr/bin/env python3
"""YANM (.yag) ringmotion animation batch decoder -> JSON.

Decodes with current YANM knowledge (2026-10-13, YANM-FORMAT.md):
  - header (56B): payload size, sec_per_tick, params
  - 29 track records: hash, single/dual, key counts, f32 triple, w24
  - single keys (5B): (s16 ch1, u8 dt, s16 ch2); angle = asin(s16/32767) deg
  - dual A keys (4B): (s16 value, u8 flags, u8 dt), first 8 bytes stored raw
  - dual B keys: same as single
  - track hash -> anatomy via docs/ycg-group-mapping.json (21/29 known;
    8 hashes appear in NO wrestler .ycg - identity open)
  - .atr companion: DATA metadata, 16-byte records (semantics open, stored raw)

Leg tracks (BD5B2A59/BD5B5259) additionally get the half-angle decode
(hinge = 2*unwrap(atan2(c2,c1)), per yanm_to_tekken3_v2).

Streams from ISO (FST read once). Writes animations/<name>.json.
Usage: python3 extract_yanm.py [outdir]
"""
import struct, sys, os, math, json

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.expanduser('~/workspace/game-reverse-engineering/wwe-wrestlemania-xix/tools')
sys.path.insert(0, TOOLS)
from gcn_fst import read_header, read_entries, flat_listing

ISO = os.path.expanduser('~/workspace/game-reverse-engineering/wwe-wrestlemania-xix/WWE Wrestlemania XIX (USA).iso')
DOCS = os.path.expanduser('~/workspace/game-reverse-engineering/wwe-wrestlemania-xix/docs')

def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]
def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]
def f32(b, i): return struct.unpack('>f', b[i:i+4])[0]
def asin_deg(v): return round(math.degrees(math.asin(max(-1.0, min(1.0, v/32767.0)))), 2)

def load_hashmap():
    m = json.load(open(os.path.join(DOCS, 'ycg-group-mapping.json')))
    h = {}
    for g in m['groups']:
        for hh in g['hashes']:
            h[hh] = {'anatomy': g['anatomy'], 'confidence': g['confidence']}
    return h

LEG_HASHES = {'BD5B2A59', 'BD5B5259'}

class ISOReader:
    def __init__(self):
        self.f = open(ISO, 'rb')
        h = read_header(self.f)
        entries, names = read_entries(self.f, h['fst_off'], h['fst_size'])
        self.files = {p.strip('/'): (o, l) for p, isdir, o, l in flat_listing(entries, names) if not isdir}
    def read(self, path):
        o, l = self.files[path]
        self.f.seek(o)
        return self.f.read(l)

def decode_single_keys(raw):
    keys = []
    for i in range(0, len(raw), 5):
        c1 = s16(raw, i); dt = raw[i+2]; c2 = s16(raw, i+3)
        keys.append([dt, c1, c2, asin_deg(c1), asin_deg(c2)])
    return keys

def decode_dual_a(data, off, ca):
    head = data[off:off+8].hex()
    keys = []
    for i in range(ca - 2):
        o = off + 8 + i*4
        v = s16(data, o); flags = data[o+2]; dt = data[o+3]
        keys.append([dt, flags, v, asin_deg(v)])
    return head, keys

def half_angle_series(keys):
    """Leg encoding: hinge = 2*unwrap(atan2(c2, c1)). keys = [dt,c1,c2,...]."""
    angs = [2*math.degrees(math.atan2(k[2], k[1])) for k in keys]
    out = [angs[0]]
    for a in angs[1:]:
        while a - out[-1] > 180: a -= 360
        while a - out[-1] < -180: a += 360
        out.append(round(a, 2))
    return out

def decode_yag(rdr, path, hashmap):
    data = rdr.read(path)
    size = len(data)
    assert data[:4] == b'YANM', path
    hdr = {
        'payload_size': u32(data, 0x04),
        'sec_per_tick': f32(data, 0x3C),
        'params': [round(f32(data, 0x40+i*4), 6) for i in range(3)],
    }
    tracks = []
    for r in range(29):
        o = 0x50 + r*32
        h = f'{u32(data, o):08X}'
        a = u32(data, o+4); ks = u32(data, o+8)
        triple = [round(f32(data, o+16+i*4), 9) for i in range(3)]
        w24 = u32(data, o+24)
        kw = u32(data, o+28)
        hm = hashmap.get(h)
        t = {'hash': h, 'dir_off': o,
             'anatomy': hm['anatomy'] if hm else 'UNRESOLVED',
             'confidence': hm['confidence'] if hm else 'NONE'}
        if a == 0:
            keys = decode_single_keys(data[ks:ks+kw*5]) if kw else []
            t.update(kind='single', nkeys=kw,
                     keys=keys,
                     ticks=sum(k[0] for k in keys),
                     static=not keys)
            if h in LEG_HASHES and keys:
                t['half_angle_deg'] = half_angle_series(keys)
        else:
            ca, cb = kw >> 16, kw & 0xFFFF
            head, akeys = decode_dual_a(data, a, ca)
            bkeys = decode_single_keys(data[ks:ks+cb*5]) if cb else []
            t.update(kind='dual', ca=ca, cb=cb, a_head_hex=head,
                     a_keys=akeys, b_keys=bkeys,
                     a_ticks=sum(k[0] for k in akeys),
                     b_ticks=sum(k[0] for k in bkeys),
                     triple=triple, w24=w24)
        tracks.append(t)
    ticks = max([t.get('ticks', t.get('b_ticks', 0)) for t in tracks] + [0])
    return {'file': path, 'size': size, 'header': hdr,
            'n_tracks': len(tracks),
            'est_seconds': round(ticks*hdr['sec_per_tick'], 3) if hdr['sec_per_tick'] else None,
            'tracks': tracks}

def decode_atr(rdr, path):
    try:
        data = rdr.read(path)
    except KeyError:
        return None
    return {'file': path, 'size': len(data),
            'records_16b': [data[i:i+16].hex() for i in range(0, len(data), 16)]}

def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'animations')
    os.makedirs(outdir, exist_ok=True)
    hashmap = load_hashmap()
    rdr = ISOReader()
    yags = sorted(p for p in rdr.files if p.startswith('ringmotion/') and p.endswith('.yag'))
    print(f'{len(yags)} .yag files')
    n = 0
    for yp in yags:
        name = os.path.basename(yp).replace('.yag', '')
        if rdr.files[yp][1] < 0x50 + 29*32:
            # degenerate stub (e.g. c138_0a.yag: 72 bytes, wrong magic words)
            clip = {'file': yp, 'size': rdr.files[yp][1], 'stub': True,
                    'note': 'too small for 29-track directory; not a real clip'}
        else:
            try:
                clip = decode_yag(rdr, yp, hashmap)
            except Exception as e:
                print(f'  FAIL {yp}: {e}')
                continue
        clip['atr'] = decode_atr(rdr, yp.replace('.yag', '.atr'))
        with open(os.path.join(outdir, f'{name}.json'), 'w') as f:
            json.dump(clip, f, separators=(',', ':'))
        n += 1
        if n % 40 == 0:
            print(f'  {n} decoded', flush=True)
    print(f'DONE: {n} clips -> {outdir}')
    rdr.f.close()

if __name__ == '__main__':
    main()
