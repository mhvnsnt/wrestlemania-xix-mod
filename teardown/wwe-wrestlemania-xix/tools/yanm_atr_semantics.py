#!/usr/bin/env python3
"""Item-10(2): .atr event semantic decode.

Layout (big-endian, verified on c200_0a/a002/a007/c200_1a):
  0: "DATA"  4: u32 trailer_offset (=16+16*event_count)
  8: u32 0x00000100  12: u32 event_count
  16: 16B records [u32 a][u32 b][u32 type<<24|tick][u32 param]
  trailer: 8 zero bytes + "POF0" + u32 len + bytes

Steps:
 1. Parse all 167 ringmotion .atr files; type vocabulary, per-type
    tick/a/b/param domains, pairing structure.
 2. Semantic hypotheses tested against companion .yag motion (FK poses via
    existing decode): hit events vs limb-tip speed peaks; 0x8B t=0 param vs
    clip variant suffix; 0x34 on/off pairing; trailer POF0 census.
"""
import os, sys, struct, json, math, glob
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.join(os.path.dirname(HERE), '.scratch', 'files')

def parse_atr(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'DATA', path
    toff = struct.unpack('>I', d[4:8])[0]
    ver = struct.unpack('>I', d[8:12])[0]
    n = struct.unpack('>I', d[12:16])[0]
    assert toff == 16 + 16*n, (path, toff, n)
    evs = []
    for i in range(n):
        a, b, tt, p = struct.unpack('>4I', d[16+16*i:32+16*i])
        evs.append({'a': a, 'b': b, 'type': tt >> 24, 'tick': tt & 0xFFFFFF, 'param': p})
    # trailer
    t = d[toff:toff+8]
    assert t == b'\x00'*8, (path, t.hex())
    assert d[toff+8:toff+12] == b'POF0', path
    plen = struct.unpack('>I', d[toff+12:toff+16])[0]
    pbytes = d[toff+16:toff+16+plen]
    assert len(pbytes) == plen and toff+16+plen == len(d), (path, plen, len(d))
    return {'n': n, 'ver': ver, 'evs': evs, 'plen': plen, 'pbytes': pbytes.hex()}

def main():
    files = sorted(glob.glob(os.path.join(SCR, 'ringmotion__*.atr')))
    clips = {}
    for f in files:
        name = os.path.basename(f)[len('ringmotion__'):-len('.atr')]
        try:
            clips[name] = parse_atr(f)
        except AssertionError as e:
            print('PARSE FAIL', name, e)
    print('parsed', len(clips), 'of', len(files))

    # --- type vocabulary ---
    tv = Counter()
    tick_by_type = defaultdict(list)
    a_by_type = defaultdict(Counter)
    b_by_type = defaultdict(Counter)
    p_by_type = defaultdict(Counter)
    for name, c in clips.items():
        for e in c['evs']:
            t = e['type']
            tv[t] += 1
            tick_by_type[t].append(e['tick'])
            a_by_type[t][e['a']] += 1
            b_by_type[t][e['b']] += 1
            p_by_type[t][e['param']] += 1
    print('\nTYPE VOCABULARY (type: count, tick range, top a, top b, top param)')
    for t in sorted(tv):
        tk = tick_by_type[t]
        print(f'  0x{t:02X}: n={tv[t]} ticks[{min(tk)}..{max(tk)}] '
              f'a={dict(a_by_type[t].most_common(4))} '
              f'b={dict(b_by_type[t].most_common(4))} '
              f'param={dict(p_by_type[t].most_common(5))}')

    # --- 0x8B at t=0: present in how many clips? param vs variant ---
    n8b0 = 0; par_var = Counter()
    for name, c in clips.items():
        e0 = [e for e in c['evs'] if e['type'] == 0x8B and e['tick'] == 0]
        if e0:
            n8b0 += 1
            var = name.rsplit('_', 1)[-1]  # 0a/1a/2a
            for e in e0:
                par_var[(e['param'], var)] += 1
    print(f'\n0x8B@t=0 present in {n8b0}/{len(clips)} clips')
    print('  (param, variant) contingency:', dict(par_var))

    # --- 0x34 pairing: on/off pairs at same tick? ---
    pair_ok = 0; pair_tot = 0; unpair = Counter()
    for name, c in clips.items():
        e34 = [e for e in c['evs'] if e['type'] == 0x34]
        bytick = defaultdict(list)
        for e in e34:
            bytick[e['tick']].append(e)
        for tk, evs in bytick.items():
            pair_tot += 1
            ps = sorted(e['param'] for e in evs)
            if ps == [0, 1]:
                pair_ok += 1
            else:
                unpair[tuple(ps)] += 1
    print(f'\n0x34 same-tick groups: {pair_tot}, exactly (0,1) pairs: {pair_ok}')
    print('  non-(0,1) group param patterns:', dict(unpair.most_common(8)))

    # --- per-clip event count distribution ---
    nc = Counter(c['n'] for c in clips.values())
    print('\nevents-per-clip distribution:', dict(sorted(nc.items())))

    # --- trailer POF0 census ---
    pl = Counter(c['plen'] for c in clips.values())
    print('\ntrailer POF0 length distribution:', dict(sorted(pl.items())))
    pb = Counter(c['pbytes'] for c in clips.values())
    print('trailer POF0 content (top):', {k: v for k, v in pb.most_common(6)})

    # --- per-type a/b contingency (is b an actor id? does a index something?) ---
    print('\n0x34 (a,b) contingency top:', )
    ab34 = Counter()
    for name, c in clips.items():
        for e in c['evs']:
            if e['type'] == 0x34:
                ab34[(e['a'], e['b'])] += 1
    print(' ', dict(ab34.most_common(12)))
    ab33 = Counter()
    for name, c in clips.items():
        for e in c['evs']:
            if e['type'] == 0x33:
                ab33[(e['a'], e['b'])] += 1
    print('0x33 (a,b) contingency top:', dict(ab33.most_common(12)))

    json.dump({n: {'n': c['n'], 'evs': c['evs'], 'plen': c['plen'], 'pbytes': c['pbytes']}
               for n, c in clips.items()},
              open(os.path.join(HERE, '..', 'docs', 'atr_all_events.json'), 'w'))
    print('\nwrote docs/atr_all_events.json')

if __name__ == '__main__':
    main()
