#!/usr/bin/env python3
"""Build the ISO file map over RangeISO and extract named files to a local dir.

Usage: python3 tools/wmxix_extract.py <outdir> [path1 path2 ...]
If no paths given, prints a summary of the file listing instead.
"""
import sys, os
sys.path.insert(0, 'tools')
from wmxix_range_iso import RangeISO
from gcn_fst import read_header, read_entries, flat_listing

def build_fmap():
    iso = RangeISO()
    h = read_header(iso)
    e, nm = read_entries(iso, h['fst_off'], h['fst_size'])
    fmap = {p.strip('/'): (o, l) for p, d, o, l in flat_listing(e, nm) if not d}
    return iso, fmap

def main():
    iso, fmap = build_fmap()
    if len(sys.argv) < 3:
        yags = [p for p in fmap if p.endswith('.yag')]
        ymgs = [p for p in fmap if p.endswith('.ymg')]
        ycgs = [p for p in fmap if p.endswith('.ycg')]
        print(f'total files={len(fmap)} yag={len(yags)} ymg={len(ymgs)} ycg={len(ycgs)}')
        iso.close()
        return
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    for p in sys.argv[2:]:
        if p not in fmap:
            print(f'MISSING: {p}'); continue
        o, l = fmap[p]
        iso.seek(o)
        data = iso.read(l)
        assert len(data) == l, f'short: {p}'
        fn = os.path.join(outdir, p.replace('/', '__'))
        with open(fn, 'wb') as f: f.write(data)
        print(f'ok {p} {l}B -> {fn}')
    iso.close()

if __name__ == '__main__':
    main()
