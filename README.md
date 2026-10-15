# WrestleMania XIX Mod

A clean workspace for research, tooling, and user-created mods for **WrestleMania XIX**. The original game files are intentionally not included; add your own local game dump/files when ready and keep them out of public commits unless you have the rights and permission to distribute them.

## Project status

- [x] Repository located and verified
- [x] Project scope and safe asset-handling notes
- [ ] Identify game archive/container formats from user-provided files
- [x] Build a read-only inventory/report tool
- [x] Add read-only signature inspection and candidate YDSP scan
- [ ] Add format-specific extract/replace tools only after formats are verified
- [ ] Run and verify tests in the repository's CI
- [ ] Test on backups and document reproducible steps

## Layout

- `docs/` — research notes, workflow, and implementation plan
- `tools/` — project-owned utilities (add only when the format is understood)
- `assets/reference/` — optional user-created reference images and notes; no game dumps
- `mods/` — source files for original or authorized mod work
- `build/` — generated output; ignored by Git

## Working principles

1. Work from a backup; never overwrite the only copy of game data.
2. Start with file inventory and metadata before attempting edits.
3. Preserve original files and record hashes for any file that is modified.
4. Keep proprietary game data, extracted assets, keys, and large binary dumps out of Git unless distribution is explicitly permitted.
5. Prefer small, documented, reversible changes.
6. Do not assume tools or file formats from another game are compatible. Verify each format against actual WrestleMania XIX files.

## First milestone

Once the game files are added locally, record the platform/version and a file listing (names, sizes, extensions). Use that inventory to choose the next investigation step without uploading the game itself.
