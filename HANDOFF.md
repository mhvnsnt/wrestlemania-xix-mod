# HANDOFF — wrestlemania-xix-mod

**Last updated: 2026-11-22 (America/New_York).**
**Repo:** `mhvnsnt/wrestlemania-xix-mod` (PUBLIC), default branch `main`.
**Purpose of this file:** any agent that picks up work here reads this FIRST, then the linked docs. It states what we've done, where we're at, and what we're working toward — so the owner can say "go to this repo, pick up the work" and you just know. Update this file in the same PR whenever the state changes (add, don't delete).

## 1. What this repo is

The WrestleMania XIX modding project — a clean workspace for research, tooling, and user-created mods for WrestleMania XIX (GameCube, GW9E78). The original game files are intentionally NOT included: add your own local game dump/files when ready, and keep them out of public commits unless you have the rights and permission to distribute them.

At 24.5 MB it holds the mod workspace: `teardown/`, `mods/`, `tools/`, `assets/`, `testbed/`, `tests/`, `docs/`. The full teardown mirror (2026-10-15) is in here, and the WMXIX work feeds Western Heart's wrestling side — the game-reverse-engineering workbench is where the cross-game teardown work lives.

## 2. Where we're at

### DONE
- **Complete teardown mirror (2026-10-15):** the full WrestleMania XIX teardown mirror is in the repo (README documents it). The game is torn down; the mirror is the record.
- **AGENTS.md + anti-clobber laws (2026-10-17, PR #17):** `AGENTS.md` with the owner's anti-clobber laws, plus the working-method statement (2026-10-27, commit `3680970`).
- **Last push 2026-11-20** (repo metadata; no new content commits after Oct 27 — the push reflects repo-level activity).

### IN PROGRESS
- **Three open PRs:** PR #20 — "Docs: pre-made parts first rule" (2026-11-20, `docs/premade-parts-first`); PR #19 — "Docs: sourcing rule" (2026-11-19, `docs/sourcing-rule`); PR #18 — "Teardown mirror: WMXIX YOBJ/YANM/DOL decoder work from game-reverse-engineering branches" (`mirror/teardown-wmxix-20261019`, open since Oct 19). Next step: a merge call on #18, #19, #20 — #18 is the real work (decoder mirror), #19/#20 are docs rules.
- **Mod tooling in the workspace:** `tools/`, `testbed/`, `tests/` exist; what the next mod or decoder step is is not recorded in the repo state read 2026-11-22.

### BLOCKED
- **Nothing recorded as blocked in the repo state read 2026-11-22.** No blocked item is named in this repo. The open PRs are awaiting a merge decision, not unblocked work.
- **Standing boundary, not a block:** original game files are never committed here. Mods are built from the user's own local dump, kept out of public commits.

## 3. What we're working toward

**The goal:** WrestleMania XIX fully decoded and moddable — YOBJ/YANM/DOL decoders working, mods built on the real files, feeding Western Heart's wrestling systems.

**The bar (owner):** PULL-100% — the real files, pulled from the real source, wired in; REAL-SOURCE-ONLY — no hand-tooled lookalikes; NO-DEFERRAL — get the full game, all files, whatever decryption/decompiling it takes. ARCHIVE-ORG-FIRST for any acquisition. Done means decoders that actually decode and mods that actually run — proven, not described.

**In order:** (1) merge or close PRs #18, #19, #20; (2) finish the YOBJ/YANM/DOL decoder work; (3) next mod per the owner's call.

## 4. Standing rules that apply here

- **Branch → PR → merge, always.** Never push to main directly. Add-only, zero-conflict PRs, no force pushes.
- **Checkpoint-and-save law:** CHECKPOINT.md first, update after every step; the repo is the save; resume, never restart.
- **No-temp-storage law:** nothing in /tmp or any wipeable location, ever. Everything goes straight into the repo or a durable folder the second it exists.
- **Never-delete-game-files / store-verify-clear:** game files (ISOs, ROMs, full-game archives, teardown source) are NEVER auto-deleted. They leave local disk only after verified 100% on GitHub OR TeraBox, with retrievability proven and the deletion logged. Never kill in-progress downloads/uploads.
- **Original game files stay OUT of this public repo.** Mods are built from the owner's own local dump. Nothing gets committed here unless there are rights and permission to distribute it.
- **Archive-org-first law:** for ANY game acquisition, archive.org is checked FIRST — live, with the item's actual files inspected. A stale note is NOT a check.
- **Real-source-only:** every part comes from the actual source code and files, wired up fully. No hand-tooled lookalikes, no fake panels.
- **Anti-clobber law (owner 2026-10-17):** do not clobber other lanes' work. Add, don't overwrite.
- **No-gaps / solve-it law:** a gap or block is never the end of the work — route-switch until it's done or every reasonable route is exhausted with exact errors recorded.
- **Licence-not-a-gate:** licence status never gates pulling in material that helps; licence/source is still logged honestly next to the item.

## 5. Key files and paths

| What | Where |
|---|---|
| Modding overview (start here) | `README.md` |
| Teardown mirror | `teardown/` |
| Mods | `mods/` |
| Tooling / decoders | `tools/` |
| Assets | `assets/` |
| Testbed + tests | `testbed/`, `tests/` |
| Docs | `docs/` |
| Agent notes / working method | `AGENTS.md`, `WORKING-METHOD.md` |
| Open PRs | #18 (YOBJ/YANM/DOL decoder mirror), #19 (sourcing rule), #20 (pre-made parts first rule) |
| Main teardown workbench | `mhvnsnt/game-reverse-engineering` |

There are no releases in this repo. Original game files are intentionally absent.

## 6. Open decisions needing the owner

- **Merge PRs #18, #19, #20?** #18 is the YOBJ/YANM/DOL decoder mirror from the game-reverse-engineering branches — the real work. #19/#20 are docs rules. Merging #18 lands the decoder work; leaving it open leaves the mirror out of main. His call — lanes do not decide merges.
- **What's the next mod / decoder step after #18?** Not recorded in the repo; his call, not a lane's guess.
- **No other owner decision is recorded as open in this repo's state.**

## 7. How to pick up

1. Read this HANDOFF.md first, then `README.md`, `AGENTS.md`, and `WORKING-METHOD.md`.
2. Check the three open PRs (#18, #19, #20) — leave them alone unless told to merge.
3. Never commit original game files here. Work from a local dump; keep game files out of public commits.
4. Check what other agents are already doing before starting anything (never start a duplicate session; anti-clobber: add, don't overwrite).
5. Resume from the stated next step — never restart, never re-derive finished work.
6. Land work branch → PR → merge, add-only. Update this HANDOFF.md in the same PR when the state changes. Prove decoder/mod work by running it, not by describing it.
