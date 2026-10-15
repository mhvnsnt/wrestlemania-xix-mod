#!/usr/bin/env python3
"""YANM directory census: tracks, hashes, key counts, dt sums per file."""
import sys, struct
sys.path.insert(0, 'tools')
from yukes_fmt import stream_file, u32
from yanm_track_probe import ycg_hashes

def census(yag_path, ycg_hashes_set):
    data, size = stream_file(yag_path)
    assert data[:4] == b'YANM', yag_path
    tracks = []
    for i in range(0x50, size, 0x20):
        if i + 32 > size: break
        h = u32(data, i); a = u32(data, i + 4); ko = u32(data, i + 8)
        w3 = u32(data, i + 12); w7 = u32(data, i + 28)
        if h == 0 and ko == 0: break
        if ko == 0 or ko >= size: continue
        if a:  # dual track
            ca, cb = (w7 >> 16) & 0xFFFF, w7 & 0xFFFF
            tracks.append((h, 'dual', a, ca, ko, cb))
        else:
            tracks.append((h, 'single', None, None, ko, w7))
    # dt sums for single tracks: find stream end = next keyoff (or EOF)
    keyoffs = sorted(t[4] for t in tracks)
    out = []
    for (h, kind, ao, ca, ko, cb) in tracks:
        if kind == 'single':
            idx = keyoffs.index(ko)
            end = keyoffs[idx + 1] if idx + 1 < len(keyoffs) else size
            n = cb
            # stream length sanity: (end-ko) should be ~ n*5 padded to 4
            dt_sum = sum(data[ko + i * 5 + 2] for i in range(n) if ko + i * 5 + 2 < end)
            out.append((h, kind, n, dt_sum, end - ko))
        else:
            out.append((h, kind, ca, cb, None))
    matched = sum(1 for t in tracks if ('%08X' % t[0]) in ycg_hashes_set)
    return tracks, out, matched

if __name__ == '__main__':
    ycghs = set('%08X' % h for h in ycg_hashes('model/wrestler/000_0.ycg'))
    for yag in sys.argv[1:]:
        tracks, out, matched = census(yag, ycghs)
        print(f'=== {yag}: {len(tracks)} tracks, {matched} hash-matched to 000_0.ycg')
        for t in out[:30]:
            print('   hash=%08X %s keys=%s dt_sum=%s len=%s' % t)
