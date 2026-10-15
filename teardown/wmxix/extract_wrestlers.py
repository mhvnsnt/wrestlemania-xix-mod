#!/usr/bin/env python3
"""WMXIX wrestler YOBJ -> OBJ extractor (all slots 000-110).

Uses the validated path (2026-10-13):
  - 8-byte skin-batch records [bone u8][count u8][00][count u8][u32 offset rel 0x80]
  - the batch table = the LONGEST run (>=3) of consecutive 8-aligned candidates
    where byte2/byte4/byte5==0, 3<=count<=255, offset+count*6 inside file
  - s16x3 vertices dequantized /64
  - triangles = implicit strips split at jump boundaries (threshold max(400, 4*median step))

Streams from ISO via tools/yukes_fmt.py. Disk-safe: only OBJs + manifest hit disk.

Usage:
  python3 extract_wrestlers.py <slotspec> <outdir>
  slotspec: "000-036" or "000,001,110" or "all"
Writes: <outdir>/wrestlers/<slot>/<slot>_<variant>.obj + EXTRACTION-MANIFEST.txt

Usage from repo root: python3 teardown/wmxix/extract_wrestlers.py all teardown/wmxix
"""
import struct, sys, os, math, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, 'tools')
if not os.path.isdir(TOOLS):
    # also allow running from the wwe-wrestlemania-xix lane
    TOOLS = os.path.expanduser('~/workspace/game-reverse-engineering/wwe-wrestlemania-xix/tools')
sys.path.insert(0, TOOLS)
import yukes_fmt
yukes_fmt.ISO = os.path.expanduser('~/workspace/game-reverse-engineering/wwe-wrestlemania-xix/WWE Wrestlemania XIX (USA).iso')
from yukes_fmt import stream_file
from gcn_fst import read_header, read_entries, flat_listing

def s16(b, i): return struct.unpack('>h', b[i:i+2])[0]
def u32(b, i): return struct.unpack('>I', b[i:i+4])[0]

def dist(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)

def find_batch_table(data, alignments=(0,)):
    """Longest run (>=3) of 8-byte batch records.
    Record: [u8 bone][u8 count][00][u8 count][u16 0][u16 offset-rel-0x80].
    byte1==byte3 (count duplicated) is the false-positive killer (2026-10-13)."""
    size = len(data)
    best = None
    for align in alignments:
        cands = []
        o = 0x80 + align
        while o < size - 8:
            if (data[o+2] == 0 and data[o+4] == 0 and data[o+5] == 0
                    and data[o+1] == data[o+3]):
                c1 = data[o+1]
                if 3 <= c1 <= 255:
                    off = u32(data, o+4)
                    if 0x80 + off + c1*6 <= size:
                        cands.append(o)
            o += 8
        runs, cur = [], []
        for o in cands:
            if cur and o == cur[-1] + 8:
                cur.append(o)
            else:
                if len(cur) >= 3: runs.append(cur)
                cur = [o]
        if len(cur) >= 3: runs.append(cur)
        if runs:
            cand = max(runs, key=len)
            if best is None or len(cand) > len(best):
                best = cand
    return best

def extract_pools(data):
    """Fallback: contiguous smooth s16x3 regions as vertex pools.
    Used when no batch table exists (YOBJ sub-variants v1/v2, named-bone v4 files).
    Returns list of raw-vert lists."""
    size = len(data)
    wins = []
    o = 0x80
    while o < size - 72:
        pts = [(s16(data, o+i*6), s16(data, o+i*6+2), s16(data, o+i*6+4))
               for i in range(12)]
        ds = sorted(dist(pts[i], pts[i+1]) for i in range(11))
        if ds[5] < 400:
            wins.append(o)
        o += 24
    pools, s, e = [], None, None
    for o in wins:
        if s is None:
            s = e = o
        elif o <= e + 72:
            e = o
        else:
            if e + 72 - s >= 120: pools.append((s, e + 72))
            s = e = o
    if s is not None and e + 72 - s >= 120: pools.append((s, e + 72))
    out = []
    for s, e in pools:
        n = (e - s) // 6
        pts = [(s16(data, s+i*6), s16(data, s+i*6+2), s16(data, s+i*6+4))
               for i in range(n)]
        if len(set(pts)) >= 10:  # drop degenerate (zero-run) pools
            out.append(pts)
    return out

def pool_median_dist(data, base, count):
    """Median consecutive s16x3 distance (strip-like pools ~<800)."""
    if count < 3: return float('inf')
    pts = [(s16(data, base+i*6), s16(data, base+i*6+2), s16(data, base+i*6+4))
           for i in range(count)]
    ds = sorted(dist(pts[i], pts[i+1]) for i in range(len(pts)-1))
    return ds[len(ds)//2]

def extract_batches(data):
    """Returns (batches, stats): include ALL records in the table run —
    same as the validated 000_0 pipeline; smoothness is reported, not filtered."""
    run = find_batch_table(data)
    if run is None:
        return None
    batches, stats = [], []
    for o in run:
        c1 = data[o+1]
        base = 0x80 + u32(data, o+4)
        raw = [(s16(data, base+i*6), s16(data, base+i*6+2), s16(data, base+i*6+4))
               for i in range(c1)]
        batches.append(raw)
        stats.append(pool_median_dist(data, base, c1))
    return batches, stats

def split_strips(raw):
    n = len(raw)
    if n < 3: return []
    ds = sorted(dist(raw[i], raw[i+1]) for i in range(n-1))
    TH = max(400, ds[len(ds)//2] * 4)
    bnd = [i for i in range(n-1) if dist(raw[i], raw[i+1]) > TH]
    strips, start = [], 0
    for i in bnd + [n-1]:
        run = list(range(start, i+1))
        if len(run) >= 3:
            strips.append(run)
        start = i + 1
    return strips

def write_obj(path, batches, scale=1.0/64, header=None):
    nv = 0; nt = 0
    with open(path, 'w') as f:
        for h in (header or []):
            f.write(h + '\n')
        bi = 1
        for raw in batches:
            strips = split_strips(raw)
            for x, y, z in raw:
                f.write(f'v {x*scale:.4f} {y*scale:.4f} {z*scale:.4f}\n')
            for s in strips:
                for i in range(len(s)-2):
                    f.write(f'f {bi+s[i]} {bi+s[i+1]} {bi+s[i+2]}\n')
                    nt += 1
            bi += len(raw); nv += len(raw)
    return nv, nt

def iso_ymg_files():
    iso = os.path.expanduser('~/workspace/game-reverse-engineering/wwe-wrestlemania-xix/WWE Wrestlemania XIX (USA).iso')
    with open(iso, 'rb') as f:
        h = read_header(f)
        entries, names = read_entries(f, h['fst_off'], h['fst_size'])
        listing = flat_listing(entries, names)
    return sorted(p.lstrip('/') for p, isdir, o, l in listing
                  if p.startswith('//model/wrestler/') and p.endswith('.ymg') and not isdir)

def main():
    spec = sys.argv[1] if len(sys.argv) > 1 else 'all'
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'wrestlers')
    if spec == 'all':
        slots = [f'{i:03d}' for i in range(111)]
    elif '-' in spec:
        a, b = spec.split('-')
        slots = [f'{i:03d}' for i in range(int(a), int(b)+1)]
    else:
        slots = [s.strip() for s in spec.split(',')]

    files = iso_ymg_files()
    byslot = {}
    for p in files:
        base = os.path.basename(p)
        slot, var = base.replace('.ymg', '').split('_')
        byslot.setdefault(slot, []).append((var, p))

    manifest = []
    total_nv = total_nt = total_files = 0
    for slot in slots:
        variants = sorted(byslot.get(slot, []))
        if not variants:
            manifest.append(f'{slot}: NO YMG FILES')
            continue
        # dedupe byte-identical variants within slot
        uniq = {}
        for var, p in variants:
            data, size = stream_file(p)
            hsh = hashlib.sha256(data).hexdigest()[:16]
            uniq.setdefault(hsh, []).append((var, p, data, size))
        sdir = os.path.join(outdir, 'wrestlers', slot)
        os.makedirs(sdir, exist_ok=True)
        note = []
        for hsh, grp in uniq.items():
            var, p, data, size = grp[0]
            dupes = [v for v, _, _, _ in grp[1:]]
            batches_stats = extract_batches(data)
            if batches_stats is None:
                if data[:4] == b'DUMY':
                    manifest.append(f'{slot} var{var}: DUMY placeholder file ({size} B) - no mesh')
                    continue
                # retry batch-table scan at all 8 alignments (sub-variant layouts)
                run = find_batch_table(data, alignments=range(8))
                if run is not None:
                    batches = []
                    for o in run:
                        c1 = data[o+1]; base = 0x80 + u32(data, o+4)
                        batches.append([(s16(data, base+i*6), s16(data, base+i*6+2),
                                         s16(data, base+i*6+4)) for i in range(c1)])
                    batches_stats = (batches, [pool_median_dist(data, 0x80+u32(data,o+4), data[o+1]) for o in run])
            if batches_stats is None:
                pools = extract_pools(data)
                if not pools:
                    manifest.append(f'{slot} var{var}: NO BATCH TABLE, pool-scan empty ({size} B)')
                    continue
                opath = os.path.join(sdir, f'{slot}_{var}_pools.obj')
                nv, nt = write_obj(opath, pools,
                                  header=[f'# WMXIX model/wrestler/{slot}_{var}.ymg -> strip OBJ (s16/64)',
                                          f'# POOL-SCAN FALLBACK: no batch table located; {len(pools)} smooth pools'])
                total_nv += nv; total_nt += nt; total_files += 1
                note.append(f'{slot} var{var}: POOL-SCAN fallback, {len(pools)} pools, {nv} verts, {nt} tris'
                            + (f' [identical: {",".join(dupes)}]' if dupes else ''))
                continue
            batches, stats = batches_stats
            opath = os.path.join(sdir, f'{slot}_{var}.obj')
            nv, nt = write_obj(opath, batches,
                              header=[f'# WMXIX model/wrestler/{slot}_{var}.ymg -> strip OBJ (s16/64)',
                                      f'# {len(batches)} batches'])
            total_nv += nv; total_nt += nt; total_files += 1
            rough = sum(1 for m in stats if m > 800)
            s = f'{slot} var{var}: {len(batches)} batches, {nv} verts, {nt} tris'
            if rough: s += f' [note: {rough} batch(es) med-dist>800 (separator/degen candidates)]'
            if dupes: s += f' [identical: {",".join(dupes)}]'
            note.append(s)
        manifest.extend(note)
        print(f'slot {slot}: {len(uniq)} unique variant(s) done', flush=True)

    mp = os.path.join(outdir, 'wrestlers', 'EXTRACTION-MANIFEST.txt')
    with open(mp, 'a') as f:
        f.write('\n'.join(manifest) + '\n')
    print(f'\nBATCH TOTAL: {total_files} OBJs, {total_nv} verts, {total_nt} tris')

if __name__ == '__main__':
    main()
