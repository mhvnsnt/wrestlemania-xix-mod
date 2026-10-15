# Tools

## Read-only file inventory

`inventory_files.py` records each file's relative path, extension, size in bytes, and SHA-256. It does not edit or unpack the scanned files.

Examples:

```bash
python tools/inventory_files.py /path/to/a/working-copy --format csv --output /tmp/wm19-inventory.csv
python tools/inventory_files.py /path/to/a/working-copy --format json --output /tmp/wm19-inventory.json
```

Use a working copy or a folder containing only files you are authorized to inspect. Write the report outside the scanned directory so a prior report does not become an inventory input.

## Planned tool order

1. Read-only inventory and hashing
2. File-signature / archive inspection
3. Extraction for confirmed formats
4. Replacement and repacking with round-trip tests

Do not add a format-specific tool merely because it worked for a different game. Each tool should include usage, supported versions, test fixtures that are safe to redistribute, and failure/rollback behavior.
