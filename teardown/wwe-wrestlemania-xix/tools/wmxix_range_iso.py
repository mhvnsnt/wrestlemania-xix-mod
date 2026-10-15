#!/usr/bin/env python3
"""Range-read the WMXIX ISO from the GitHub release without downloading it.

Release mhvnsnt/western-heart tag wmxix-iso-v1 holds the ISO split as
  wmxix-500m.part_aa (524288000 B) + part_ab (524288000) + part_ac (411402240)
= 1,459,978,240 B total (documented MD5 c13c47a5ed24a675545c99a15e44529d).
NOTE: part_00 is a STALE DUPLICATE of part_aa (also starts with GW9E78) and
must NOT be concatenated; the release description's `cat part_*` glob is WRONG.

This module exposes a file-like object over HTTP Range requests with an
on-disk cache, so all existing tools that do iso.seek()/iso.read() work
unchanged. Total cache = only the bytes actually touched (FST + requested
files), KB/MB-scale — safe at 94% disk.
"""
import os, sys, subprocess, json, requests

REPO = 'mhvnsnt/western-heart'
TAG = 'wmxix-iso-v1'
# asset id -> size; cat order aa, ab, ac
PARTS = [
    (638070444, 524288000),
    (638083987, 524288000),
    (637990517, 411402240),
]
CACHE_DIR = os.environ.get('WMXIX_CACHE', '/tmp/wmxix_cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def _asset_url(asset_id):
    out = subprocess.run(['gh', 'api',
                          f'repos/{REPO}/releases/assets/{asset_id}',
                          '--jq', '.browser_download_url'],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()

class RangeISO:
    def __init__(self):
        self.sess = requests.Session()
        self.urls = [_asset_url(aid) for aid, _ in PARTS]
        # cumulative ISO offsets of part starts
        self.starts = []
        acc = 0
        for _, sz in PARTS:
            self.starts.append(acc); acc += sz
        self.total = acc
        self.pos = 0
        self.cache_path = os.path.join(CACHE_DIR, 'iso_cache.bin')
        self.cache_len = os.path.getsize(self.cache_path) if os.path.exists(self.cache_path) else 0
        self.fh = open(self.cache_path, 'ab+')
        # cached spans: list of [start, end) sorted, non-overlapping
        self.spans = []
        idx_path = self.cache_path + '.idx'
        if os.path.exists(idx_path):
            with open(idx_path) as f:
                self.spans = json.load(f)
        self.idx_path = idx_path

    def _save_idx(self):
        with open(self.idx_path, 'w') as f:
            json.dump(self.spans, f)

    def _part_for(self, off):
        for i in range(len(PARTS) - 1, -1, -1):
            if off >= self.starts[i]:
                return i, off - self.starts[i]
        raise ValueError(off)

    def _fetch(self, start, end):
        """Fetch ISO [start, end), splitting across parts. Appends to cache."""
        while start < end:
            pi, poff = self._part_for(start)
            pend = min(end, self.starts[pi] + PARTS[pi][1])
            url = self.urls[pi]
            r = self.sess.get(url, headers={'Range': f'bytes={poff}-{poff + (pend - start) - 1}',
                                            'Accept': 'application/octet-stream'},
                              timeout=120)
            r.raise_for_status()
            data = r.content
            assert len(data) == pend - start, f'short read {len(data)} vs {pend - start}'
            self.fh.seek(0, 2)
            cstart = self.fh.tell()
            self.fh.write(data)
            self.fh.flush()
            self._add_span(cstart, cstart + len(data), start)
            start = pend
        self._save_idx()

    def _add_span(self, cstart, cend, iso_start):
        # record mapping iso_start -> cache offset cstart, length cend-cstart
        self.spans.append([iso_start, iso_start + (cend - cstart), cstart])
        self.spans.sort()

    def _ensure(self, start, end):
        # find gaps in [start,end) and fetch them
        cur = start
        for s, e, _ in self.spans:
            if e <= cur: continue
            if s > cur:
                self._fetch(cur, min(s, end))
                cur = min(s, end)
                if cur >= end: return
            cur = max(cur, e)
            if cur >= end: return
        if cur < end:
            self._fetch(cur, end)

    def _cache_off(self, iso_off):
        for s, e, c in self.spans:
            if s <= iso_off < e:
                return c + (iso_off - s)
        raise RuntimeError('gap after ensure')

    def seek(self, off, whence=0):
        if whence == 0: self.pos = off
        elif whence == 1: self.pos += off
        elif whence == 2: self.pos = self.total + off
        return self.pos

    def tell(self): return self.pos

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.total - self.pos
        n = min(n, self.total - self.pos)
        if n <= 0: return b''
        self._ensure(self.pos, self.pos + n)
        out = bytearray()
        cur = self.pos
        while cur < self.pos + n:
            for s, e, c in self.spans:
                if s <= cur < e:
                    take = min(e - cur, self.pos + n - cur)
                    self.fh.seek(c + (cur - s))
                    out += self.fh.read(take)
                    cur += take
                    break
        self.pos += n
        return bytes(out)

    def close(self):
        self._save_idx()
        self.fh.close()

if __name__ == '__main__':
    iso = RangeISO()
    iso.seek(0)
    hdr = iso.read(0x440)
    print('magic:', hdr[:6], hdr[0x20:0x34])
    import struct
    fst_off, fst_size = struct.unpack('>II', hdr[0x424:0x42C])
    print(f'fst_off={fst_off:#x} fst_size={fst_size} ({fst_size/1048576:.1f} MB)')
    iso.seek(fst_off)
    fst = iso.read(min(fst_size, 64))
    print('fst head:', fst[:32].hex())
    iso.close()
    import subprocess as sp
    sz = sp.run(['du','-sh',CACHE_DIR],capture_output=True,text=True).stdout.strip()
    print('cache:', sz)
