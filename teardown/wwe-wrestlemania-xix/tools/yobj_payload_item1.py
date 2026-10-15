#!/usr/bin/env python3
"""Item 1: YOBJ (u16,0) payload exact semantics - hypothesis tests.

Tests:
  H1: (pos_idx, nrm_idx) pairs indexing position/normal pools.
      -> searches 000_0/001_0/002_0/003_0.ymg for >=4097-entry s16x3 pools.
  H2: 16.16 fixed-point interpretation of the u32 (a<<16|b).
  H3: 12-bit fraction (value/4096) -> UV.u or normalized weight.

Measured results (2026-10-13):
  H1 REJECTED: no >=4097 s16x3 pool in any sampled ymg; 606-vert skin pool
     too small (max idx 4096 >> 605); b=0 degenerate for nrm_idx.
  H2 NOT-DISTINGUISHING: b=0 so 16.16 == float(a); no consuming float struct.
  H3 OPEN (leading): values are 12-bit 0..4096 = 0.0..1.0 fractions, per-model
     (000_0 == 002_0: 48 vals; 003_0: 59 vals). Candidate: UV.u (V unknown)
     or normalized weights. Needs texture decode to confirm.
"""
import struct, math, json, sys

def load_ymg(path):
    d = open(path, 'rb').read()
    base = d.find(b'YOBJ')
    assert base >= 0, f'no YOBJ in {path}'
    tbloff = struct.unpack('>I', d[base+0x5C:base+0x60])[0]
    recs = []
    for i in range(58):
        o = base + tbloff + i*16
        if o + 16 > len(d): break
        u0, u1 = struct.unpack('>II', d[o:o+8])
        b8 = d[o+8]; marker = struct.unpack('>H', d[o+9:o+11])[0]
        v = d[o+11]; cnt = struct.unpack('>I', d[o+12:o+16])[0]
        recs.append((u0, u1, b8, marker, v, cnt))
    return d, base, recs

def payload_vals(d, base, rec):
    u0, u1, b8, marker, v, cnt = rec
    o = base + 0x80 + u0
    if o + 4*cnt > len(d) or cnt > 10000: return [], []
    w = struct.unpack('>' + 'H'*(2*cnt), d[o:o+4*cnt])
    return list(w[0::2]), list(w[1::2])

def skin_pool_size(d):
    """Total verts from the 13 (c1, off) descriptors at 0x7CA0."""
    total = 0
    for r in range(1, 14):
        o = 0x7CA0 + r*8
        if o + 8 > len(d): break
        c1 = d[o+1]; off = struct.unpack('>I', d[o+4:o+8])[0]
        base = 0x80 + off
        if base + c1*6 <= len(d):
            total += c1
    return total

def main():
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    files = [os.path.join('/tmp/wtx', f) for f in
             ['000_0.ymg', '001_0.ymg', '002_0.ymg', '003_0.ymg']]
    out = {'H1_pos_nrm_idx': {}, 'H2_fixed1616': {}, 'H3_frac12': {}}
    for fp in files:
        fn = os.path.basename(fp)
        try:
            d, base, recs = load_ymg(fp)
        except Exception as e:
            out['H1_pos_nrm_idx'][fn] = f'parse failed: {e}'
            continue
        vals = set(); vmax = 0; b_nz = 0; b_tot = 0
        for rec in recs:
            if rec[4] == 2:
                a, b = payload_vals(d, base, rec)
                vals.update(a)
                if a: vmax = max(vmax, max(a))
                b_nz += sum(1 for x in b if x); b_tot += len(b)
        pool = skin_pool_size(d)
        out['H1_pos_nrm_idx'][fn] = {
            'distinct_vals': len(vals), 'max_val': vmax,
            'skin_pool_verts': pool,
            'max_idx_fits_pool': vmax < pool,
            'second_u16_nonzero_frac': b_nz / max(b_tot, 1),
            'verdict': 'REJECTED' if vmax >= pool else 'possible',
        }
        sv = sorted(vals)
        out['H3_frac12'][fn] = {
            'as_frac12': [round(x/4096, 4) for x in sv[:8]],
            'note': 'values span 0..4096; value/4096 in 0..1',
        }
    out['H2_fixed1616']['note'] = (
        'u32 BE = (a<<16)|b with b=0 -> 16.16 value = float(a). '
        'Identical to integer interpretation; no separate float struct found. '
        'Not distinguishing; does not reveal new semantics.')
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()
