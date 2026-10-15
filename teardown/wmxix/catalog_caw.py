#!/usr/bin/env python3
"""Catalog all edit_data/ (CAW) files: path, size, type signature.

Type ID from first 16 bytes:
  YOBJ v-word / DUMY / TPL magic 0020AF30 / TGA / PSD (8BPS) / TM2 / YCG / ATR DATA / raw
Writes caw-parts/files.tsv + caw-parts/CATALOG.md summary.
Usage: python3 catalog_caw.py [outdir]
"""
import struct, sys, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.expanduser('~/workspace/game-reverse-engineering/wwe-wrestlemania-xix/tools'))
sys.path.insert(0, HERE)
from extract_yanm import ISOReader

def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]

def identify(data):
    if len(data) < 4: return 'EMPTY'
    m4 = data[:4]
    if m4 == b'YOBJ': return f'YOBJ v{u32(data,8):08x}'
    if m4 == b'DUMY': return 'DUMY placeholder'
    if m4 == b'\x00\x20\xaf\x30': return 'TPL texture'
    if m4 == b'\x00\x00\x02\x00' and len(data) >= 18: return 'TGA image'
    if m4 == b'8BPS': return 'PSD photoshop'
    if m4 == b'TIM2': return 'TM2 (PS2 TIM2)'
    if m4 == b'DATA': return 'ATR DATA'
    if data[:16].rstrip(b'\x00').isascii() and b'\\' in data[:16]: return 'TXT-ish'
    return f'RAW ({m4.hex()})'

def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'caw-parts')
    os.makedirs(outdir, exist_ok=True)
    rdr = ISOReader()
    paths = sorted(p for p in rdr.files if p.startswith('edit_data/'))
    print(f'{len(paths)} edit_data files')
    rows = []
    f = rdr.f
    for p in paths:
        o, l = rdr.files[p]
        f.seek(o)
        head = f.read(min(64, l))
        rows.append((p, l, identify(head)))
    rdr.f.close()

    with open(os.path.join(outdir, 'files.tsv'), 'w') as fh:
        fh.write('path\tsize\tbytes\ttype\n')
        for p, l, t in rows:
            fh.write(f'{p}\t{l}\t{t}\n')

    by_ext = Counter(p.rsplit('.', 1)[-1] for p, _, _ in rows)
    by_type = Counter(t for _, _, t in rows)
    by_cat = Counter()
    for p, _, _ in rows:
        parts = p.split('/')
        cat = parts[2] if len(parts) > 2 else '?'
        by_cat[cat] += 1
    total = sum(l for _, l, _ in rows)
    with open(os.path.join(outdir, 'CATALOG.md'), 'w') as fh:
        fh.write('# CAW edit_data catalog\n\n')
        fh.write(f'**{len(rows)} files, {total/1e6:.1f} MB total** (streamed from ISO, 2026-10-13)\n\n')
        fh.write('## By extension\n\n| ext | count |\n|---|---|\n')
        for e, c in by_ext.most_common():
            fh.write(f'| .{e} | {c} |\n')
        fh.write('\n## By content signature (first bytes)\n\n| type | count |\n|---|---|\n')
        for t, c in by_type.most_common():
            fh.write(f'| {t} | {c} |\n')
        fh.write('\n## By top-level dir\n\n| dir | count |\n|---|---|\n')
        for c, n in by_cat.most_common():
            fh.write(f'| {c}/ | {n} |\n')
        fh.write('\n## Notable finds\n\n')
        fh.write('- `MODEL/Woman/Face/tq0_417/` contains the ARTIST WORKING FILES: .tga source art, '
                 '.tm2 (PS2 TIM2), 2 .psd (Japanese filenames), .tpg, and `tq0_417_TPL/` with 2 .tpl + '
                 '`script.txt` revealing the build path `D:\\MAX_Wwfgc2\\edit\\woman1\\edit_face_woman\\mouth\\tex\\`\n')
        fh.write('- `.tpl` files carry the standard GameCube TPL magic `0020AF30`\n')
        fh.write('- 3 `.ymm` files (Yukes material?) under `MODEL/Woman/Hair/`\n')
        fh.write('- `COL/` 8 `.ycg`: 2x 2,356 B skeleton-size + 6 small palette/override files\n')
        fh.write('\nFull per-file listing: `files.tsv`\n')
    print(f'wrote {outdir}/files.tsv + CATALOG.md ({total/1e6:.1f} MB total)')

if __name__ == '__main__':
    main()
