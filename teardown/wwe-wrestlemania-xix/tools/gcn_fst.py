#!/usr/bin/env python3
"""GameCube ISO FileSystem Table (FST) reader - pure stdlib, no tools needed.
Reads the GCN disc header at 0x0 (0x420=FST offset, 0x424=FST size), parses
the 12-byte FST entries, and can list/extract files."""
import struct, sys, os

def read_header(iso):
    iso.seek(0)
    hdr = iso.read(0x440)
    magic, = struct.unpack('>I', hdr[0x1C:0x20])
    assert magic == 0xC2339F3D, f'bad disc magic {magic:08X} (not GameCube/Wii)'
    game_id = hdr[0:6].decode('ascii', 'replace')
    title = hdr[0x20:0x20+64].split(b'\x00')[0].decode('ascii', 'replace')
    fst_off, fst_size = struct.unpack('>II', hdr[0x424:0x42C])
    return {'game_id': game_id, 'title': title, 'fst_off': fst_off, 'fst_size': fst_size}

def read_entries(iso, fst_off, fst_size):
    iso.seek(fst_off)
    raw = iso.read(fst_size)
    n, = struct.unpack('>I', raw[8:12])
    entries = []
    for i in range(n):
        e = raw[i*12:(i+1)*12]
        flags = e[0]
        name_off = int.from_bytes(e[1:4], 'big')
        off_or_parent = int.from_bytes(e[4:8], 'big')
        len_or_next = int.from_bytes(e[8:12], 'big')
        entries.append((flags == 1, name_off, off_or_parent, len_or_next))
    strtab = raw[n*12:]
    def name(no):
        return strtab[no:].split(b'\x00')[0].decode('ascii', 'replace')
    return entries, name

def walk(entries, name, idx=0, prefix=''):
    isdir, no, offp, lenn = entries[idx]
    if idx == 0:
        for i in range(1, offp):  # root children: entries 1..next-1 (approx via parent links)
            pass
    return None

def flat_listing(entries, name):
    # depth-first layout: children of dir i live in [i+1, next)
    n = len(entries)
    out = []
    def rec(i, prefix):
        isdir, no, offp, lenn = entries[i]
        p = prefix + '/' + name(no) if i else '/'
        out.append((p, isdir, offp, lenn))
        if isdir:
            j = i + 1
            while j < lenn:
                j = rec(j, p)
        return lenn if isdir else i + 1
    rec(0, '')
    return out

def main():
    iso_path = sys.argv[1]
    cmd = sys.argv[2] if len(sys.argv) > 2 else 'list'
    with open(iso_path, 'rb') as iso:
        h = read_header(iso)
        print(f"game_id={h['game_id']} title={h['title']} fst_off=0x{h['fst_off']:X} fst_size={h['fst_size']}")
        entries, name = read_entries(iso, h['fst_off'], h['fst_size'])
        listing = flat_listing(entries, name)
        nfiles = sum(1 for p, d, o, l in listing if not d)
        total = sum(l for p, d, o, l in listing if not d)
        print(f'entries={len(entries)} files={nfiles} total_bytes={total}')
        if cmd == 'list':
            for p, isdir, o, l in listing:
                if not isdir:
                    print(f'{l:>10} 0x{o:08X} {p}')
        elif cmd == 'get':
            want = sys.argv[3].strip('/')
            for p, isdir, o, l in listing:
                if p.strip('/') == want and not isdir:
                    iso.seek(o)
                    data = iso.read(l)
                    sys.stdout.buffer.write(data)
                    print(f'\n# got {len(data)} bytes from 0x{o:X}', file=sys.stderr)
                    return
            print('not found: ' + want, file=sys.stderr); sys.exit(1)
        elif cmd == 'extract':
            dest = sys.argv[3]
            for p, isdir, o, l in listing:
                if isdir:
                    os.makedirs(dest + p, exist_ok=True)
                else:
                    dp = dest + p
                    os.makedirs(os.path.dirname(dp), exist_ok=True)
                    iso.seek(o)
                    with open(dp, 'wb') as f:
                        f.write(iso.read(l))
            print('extracted to', dest)

if __name__ == '__main__':
    main()
