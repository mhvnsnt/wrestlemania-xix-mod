#!/usr/bin/env python3
"""Read-only file signature report for modding research.

Prints a short hexadecimal prefix and readable ASCII approximation for each
file in a directory. It does not extract or modify files.
"""
from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_BYTES = 32


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Directory to inspect")
    parser.add_argument("--bytes", type=int, default=DEFAULT_BYTES,
                        help=f"Bytes to read from each file (default {DEFAULT_BYTES})")
    parser.add_argument("--limit", type=int, default=0,
                        help="Maximum number of files (0 means no limit)")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")
    if args.bytes < 1:
        parser.error("--bytes must be at least 1")
    if args.limit < 0:
        parser.error("--limit cannot be negative")

    files = (p for p in sorted(root.rglob("*")) if p.is_file())
    count = 0
    for path in files:
        if args.limit and count >= args.limit:
            break
        try:
            with path.open("rb") as handle:
                prefix = handle.read(args.bytes)
            size = path.stat().st_size
        except OSError as exc:
            print(f"ERROR\t{path.relative_to(root).as_posix()}\t{exc}")
            continue
        hex_bytes = prefix.hex(" ")
        ascii_bytes = "".join(chr(b) if 32 <= b < 127 else "." for b in prefix)
        print(f"{path.relative_to(root).as_posix()}\t{size}\t{hex_bytes}\t{ascii_bytes}")
        count += 1

    print(f"Inspected {count} files under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
