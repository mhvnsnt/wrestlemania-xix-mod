# Tools

## Read-only file inventory

`inventory_files.py` records each file's relative path, extension, size in bytes, and SHA-256. It does not edit or unpack the scanned files.

Examples:

```bash
python tools/inventory_files.py /path/to/working-copy --format csv --output /tmp/wm19-inventory.csv
python tools/inventory_files.py /path/to/working-copy --format json --output /tmp/wm19-inventory.json
```

## Read-only signature inspection

`inspect_signatures.py` prints file size, a short hexadecimal prefix, and an ASCII approximation. This helps compare file signatures without extracting or changing anything.

```bash
python tools/inspect_signatures.py /path/to/working-copy --limit 100
python tools/inspect_signatures.py /path/to/working-copy --bytes 64
```

Write reports outside the scanned directory so report files do not become input files on later scans. Use a working copy or a folder containing only files you are authorized to inspect.

## Candidate YDSP audio signature scan

`scan_ydsp.py` searches files for the ASCII `YDSP` marker and reports its offset plus a candidate 4-byte big-endian size value at offset `+0x08`. This interpretation comes from historical community notes and is **not yet validated against this game's exact revision**. It only reports candidates; it does not carve or decode audio.

```bash
python tools/scan_ydsp.py /path/to/working-copy --limit 200
```

Treat `IN_BOUNDS` as a plausibility check, not proof that the candidate is a valid stream. Keep reports outside the scanned directory.

## Planned tool order

1. Read-only inventory and hashing
2. File-signature / archive inspection
3. Extraction for confirmed formats
4. Replacement and repacking with round-trip tests

See [FORMAT-RESEARCH.md](../docs/FORMAT-RESEARCH.md) for game-specific leads and confidence levels. Do not add a format-specific tool merely because it worked for a different game. Each tool should include usage, supported versions, safe test fixtures, and failure/rollback behavior.
