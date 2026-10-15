#!/usr/bin/env python3
"""Create a read-only inventory of files for modding research.

This script reads file metadata and hashes only. It does not unpack, modify,
or upload any files. Keep game files outside the Git repository.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            stat = path.stat()
            rows.append({
                "relative_path": path.relative_to(root).as_posix(),
                "extension": path.suffix.lower(),
                "size_bytes": stat.st_size,
                "sha256": sha256_file(path),
            })
        except (OSError, PermissionError) as exc:
            rows.append({
                "relative_path": path.relative_to(root).as_posix(),
                "extension": path.suffix.lower(),
                "size_bytes": None,
                "sha256": None,
                "error": str(exc),
            })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inventory files by relative path, extension, size, and SHA-256."
    )
    parser.add_argument("root", type=Path, help="Directory to scan (read-only)")
    parser.add_argument(
        "--format", choices=("csv", "json"), default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("inventory.csv"),
        help="Output report path (default: inventory.csv)",
    )
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")

    rows = inventory(root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "json":
        args.output.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    else:
        fieldnames = ["relative_path", "extension", "size_bytes", "sha256", "error"]
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    print(f"Inventoried {len(rows)} files from {root}")
    print(f"Report: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
