#!/usr/bin/env python3
"""Item-10(2) v2: .atr semantic decode.

Fixes: trailer = [u32 x][u32 y] + "POF0" + u32 len + bytes (the 8 bytes are
NOT always zero; e.g. a000=(1,20), a005=(1,15), a002=(16,0)).

Tests:
 A. (x,y) trailer semantics: correlate with n_events, last event (a,b),
    final 0x34 ON-state, 0x8B@t=0 param, clip family.
 B. 0x34 state-machine model: exactly-one-ON invariant per clip.
 C. 0x00/0x01 ordering: always first/last per clip? (section markers?)
 D. 0x8B nonzero-tick events: distribution.
 E. Phase clustering: per-type tick/max_tick histograms (impact/camera phases).
 F. 0x8B@t=0 param vs clip family (a/b/c/d) contingency.
 G. Trailer POF0 census (all 167).
"""
import os, sys, struct, json, glob
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
    x, y = struct.unpack('>2I', d[toff:toff+8])
    assert d[toff+8:toff+12] == b'POF0', (path, d[toff+8:toff+12])
    plen = struct.unpack('>I', d[toff+12:toff+16])[0]
    pbytes = d[toff+16:toff+16+plen]
    assert len(pbytes) == plen and toff+16+plen == len(d), (path, plen, len(d))
    return {'n': n, 'ver': ver, 'evs': evs, 'x': x, 'y': y,
            'plen': plen, 'pbytes': pbytes.hex()}

def main():
    files = sorted(glob.glob(os.path.join(SCR, 'ringmotion__*.atr')))
    clips = {}
    for f in files:
        name = os.path.basename(f)[len('ringmotion__'):-len('.atr')]
        clips[name] = parse_atr(f)
    print('parsed', len(clips))

    # A. trailer (x,y) census
    xy = Counter((c['x'], c['y']) for c in clips.values())
    print('\nA. trailer (x,y) top:', dict(xy.most_common(10)), '... distinct:', len(xy))
    # correlate: last event (a,b)?
    m_last = sum(1 for c in clips.values()
                 if c['evs'] and (c['x'], c['y']) == (c['evs'][-1]['a'], c['evs'][-1]['b']))
    m_first = sum(1 for c in clips.values()
                  if c['evs'] and (c['x'], c['y']) == (c['evs'][0]['a'], c['evs'][0]['b']))
    print(f'   (x,y)==last event (a,b): {m_last}/{len(clips)}; ==first: {m_first}/{len(clips)}')
    # final 0x34 ON-state: last param=1 0x34 event's (a,b)
    m_on = 0; tot_on = 0
    for c in clips.values():
        ons = [e for e in c['evs'] if e['type'] == 0x34 and e['param'] == 1]
        if ons:
            tot_on += 1
            if (c['x'], c['y']) == (ons[-1]['a'], ons[-1]['b']):
                m_on += 1
    print(f'   (x,y)==final 0x34 ON (a,b): {m_on}/{tot_on}')
    # vs 0x8B@t=0 (a,b)?
    m_8b = 0; tot_8b = 0
    for c in clips.values():
        e0 = [e for e in c['evs'] if e['type'] == 0x8B and e['tick'] == 0]
        if e0:
            tot_8b += 1
            if (c['x'], c['y']) == (e0[0]['a'], e0[0]['b']):
                m_8b += 1
    print(f'   (x,y)==0x8B@t=0 (a,b): {m_8b}/{tot_8b}')
    # (x,y) vs n_events
    xyn = defaultdict(Counter)
    for c in clips.values():
        xyn[(c['x'], c['y'])][c['n']] += 1
    print('   (x,y)=(0,0) n_events:', dict(sorted(xyn[(0,0)].items())))

    # B. 0x34 state machine: exactly-one-ON per (b-bank)?
    # per clip: simulate ON set per b; count violations (2+ ON in same bank)
    viol = 0; tot34 = 0; maxon = Counter()
    for name, c in clips.items():
        on = defaultdict(set)
        for e in sorted(c['evs'], key=lambda e: (e['tick'])):
            if e['type'] != 0x34:
                continue
            tot34 += 1
            if e['param'] == 1:
                on[e['b']].add(e['a'])
            elif e['param'] == 0:
                on[e['b']].discard(e['a'])
            for b, s in on.items():
                maxon[len(s)] += 1
                if len(s) > 1:
                    viol += 1
    print(f'\nB. 0x34 state machine: {tot34} events, max-ON distribution {dict(sorted(maxon.items()))}, '
          f'multi-ON violations: {viol}')

    # C. 0x00/0x01 ordering
    first00 = sum(1 for c in clips.values() if c['evs'] and c['evs'][0]['type'] == 0x00)
    last01 = sum(1 for c in clips.values() if c['evs'] and c['evs'][-1]['type'] == 0x01)
    has00 = sum(1 for c in clips.values() if any(e['type'] == 0x00 for e in c['evs']))
    has01 = sum(1 for c in clips.values() if any(e['type'] == 0x01 for e in c['evs']))
    # tick-sorted?
    unsorted = sum(1 for c in clips.values()
                   if [e['tick'] for e in c['evs']] != sorted(e['tick'] for e in c['evs']))
    print(f'\nC. clips with any 0x00: {has00}, any 0x01: {has01}; '
          f'0x00 is first event: {first00}; 0x01 is last: {last01}; '
          f'tick-unsorted clips: {unsorted}')
    # where do 0x00/0x01 sit in tick order? (rank)
    r00 = Counter(); r01 = Counter()
    for c in clips.values():
        evs = c['evs']
        for i, e in enumerate(evs):
            if e['type'] == 0x00:
                r00['first' if i == 0 else ('last' if i == len(evs)-1 else 'mid')] += 1
            if e['type'] == 0x01:
                r01['first' if i == 0 else ('last' if i == len(evs)-1 else 'mid')] += 1
    print('   0x00 position:', dict(r00), ' 0x01 position:', dict(r01))

    # D. 0x8B nonzero-tick events
    e8bnz = [(n, e) for n, c in clips.items() for e in c['evs']
             if e['type'] == 0x8B and e['tick'] != 0]
    print(f'\nD. 0x8B nonzero-tick: {len(e8bnz)} events')
    for n, e in e8bnz[:12]:
        print(f'   {n}: tick={e["tick"]} a={e["a"]} b={e["b"]} param={e["param"]}')

    # E. phase clustering per type
    print('\nE. phase histograms (tick/max_tick, 10 bins) for top types:')
    for t in (0x33, 0x34, 0x88, 0x89, 0x8B, 0x32):
        bins = [0]*10
        for c in clips.values():
            mx = max((e['tick'] for e in c['evs']), default=0)
            if mx == 0:
                continue
            for e in c['evs']:
                if e['type'] == t:
                    bins[min(9, int(10*e['tick']/mx))] += 1
        print(f'   0x{t:02X}: {bins}')

    # F. 0x8B@t=0 param vs clip family
    fam = Counter()
    for n, c in clips.items():
        e0 = [e for e in c['evs'] if e['type'] == 0x8B and e['tick'] == 0]
        p = e0[0]['param'] if e0 else None
        fam[(n[0], p)] += 1
    print('\nF. 0x8B@t=0 (family, param):', dict(sorted(fam.items())))

    # G. trailer POF0 census
    pl = Counter(c['plen'] for c in clips.values())
    pb = Counter(c['pbytes'] for c in clips.values())
    print('\nG. trailer POF0 len:', dict(pl), 'content:', dict(pb.most_common(4)))

    # type-pair co-occurrence: which types appear together per clip
    co = Counter()
    for c in clips.values():
        ts = tuple(sorted(set(e['type'] for e in c['evs'])))
        co[ts] += 1
    print('\nper-clip type sets (top):', dict(co.most_common(10)))

if __name__ == '__main__':
    main()
