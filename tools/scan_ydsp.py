#!/usr/bin/env python3
"""Read-only scanner for candidate YDSP audio streams in game files.

Historical community notes describe the ASCII signature YDSP and a 4-byte
big-endian size field at offset +0x08. This scanner reports candidates only;
it does not extract, decode, or modify files, and the size interpretation must
be verified against the exact game revision.
"""
from __future__ import annotations

import argparse
import struct
from pathlib import Path

MAGIC = b"YDSP"
SIZE_OFFSET = 0x08
SIZE_BYTES = 4


def scan_file(path: Path) -> list[tuple[int, int, bool]]:
    """Return (offset, declared_size, fits_in_file) candidate tuples."""
    data = path.read_bytes()
    results: list[tuple[int, int, bool]] = []
    start = 0
    while True:
        offset = data.find(MAGIC, start)
        if offset < 0:
            break
        field = offset + SIZE_OFFSET
        if field + SIZE_BYTES <= len(data):
            declared = struct.unpack_from(">I", data, field)[0]
            results.append((offset, declared, declared > 0 and offset + declared <= len(data)))
        else:
            results.append((offset, 0, False))
        start = offset + 1
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Directory to scan")
    parser.add_argument("--limit", type=int, default=0,
                        help="Maximum number of files (0 means no limit)")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")
    if args.limit < 0:
        parser.error("--limit cannot be negative")

    checked = 0
    matches = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if args.limit and checked >= args.limit:
            break
        checked += 1
        try:
            candidates = scan_file(path)
        except OSError as exc:
            print(f"ERROR\t{path.relative_to(root).as_posix()}\t{exc}")
            continue
        for offset, declared, fits in candidates:
            matches += 1
            status = "IN_BOUNDS" if fits else "CHECK_SIZE_OR_TRUNCATED"
            print(f"{path.relative_to(root).as_posix()}\t0x{offset:X}\t{declared}\t{status}")
    print(f"Scanned {checked} files; found {matches} YDSP signature candidate(s).")
    print("Candidate reports only; size-field semantics are not yet confirmed for this revision.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
