# Project Plan

## Goal

Build a maintainable, reversible modding workflow for WrestleMania XIX using files supplied by the repository owner. The game itself is not stored in this repository.

## Phase 1 — Inventory

- Record game platform/version and source of the files.
- Produce a filename, size, extension, and hash inventory.
- Identify likely archives/containers from signatures and metadata rather than trusting extensions alone.
- Keep untouched originals in a separate local backup.

## Phase 2 — Format research

- Confirm each container format with samples and reproducible evidence.
- Document byte order, offsets, compression, alignment, and checksum behavior when relevant.
- Keep uncertain findings marked as hypotheses.
- Do not borrow format assumptions from Tekken, other wrestling games, or unrelated projects without verification.

## Phase 3 — Minimal tools

- Begin with read-only inspection and reporting.
- Add extraction only after the format is confirmed.
- Add replacement/repacking only after round-trip tests succeed on disposable copies.
- Include validation and clear error messages.

## Phase 4 — Mod workflow

- Keep original/authorized source files separate from generated output.
- Track each change in a manifest with input hash, output hash, tool version, and notes.
- Test one small change at a time.
- Document rollback steps.

## Acceptance criteria

- A new user can reproduce the inventory.
- Tools do not silently overwrite source files.
- Unsupported or malformed input fails safely.
- No game binaries or extracted proprietary assets are committed by default.
