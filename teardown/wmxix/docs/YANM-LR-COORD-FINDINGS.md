# WMXIX L/R Final — Coordinator Gap-Fill Findings (2026-10-14)

**Question:** For each YANM L/R track pair (fingers A4955E6E/BA955E6E, thumbs
579B89D0/579B8E50, toes 007FD58C/1E7FD58C, LEG BD5B2A59/BD5B5259, etc.), which
track is anatomically LEFT vs RIGHT?

**Status:** Watchdog item-6 verdict ("consistent up to global mirror") CONFIRMED
as the correct build posture. The anatomical final bit is NOT reliably
resolvable headless — new conflicting evidence found (see §3).

## 1. What is SOLID (no change from watchdog)

- Track side-bits pair via exact XOR (0x1E000000 fingers/toes, 0x780 thumbs,
  0x7800 LEG, 0xF0/0x0F others) — consistent across all 170 clips.
- Side-bit → ycg bind-pose y-sign: 0x04000000-bit SET ↔ ycg y<0 (item-6, 6/6).
- ycg group structure (measured 2026-10-14, 000_0.ycg): 21 unique hashes =
  8 singles (1 rec) + 5 doubles (2 rec) + 8 triples (3 rec) = 42 records.
  L/R is encoded ACROSS XOR-paired groups (e.g. 613B7547/613B75B7 = 0xF0,
  7AD45E02/64D45E02 = 0x1E000000, BD5B2A59/BD5B5259 = 0x7800), whose records
  are exact y-mirrors (x/z identical, y negated, record order reversed).
- ymg body frame ground truth: Bip R Thigh local (−0.14, **+10.40**, 0),
  Bip L Thigh (−0.14, **−10.40**, 0); R/L Clavicle ±3.04 → **R=+y, L=−y**.
- ycg bind pos ≈ ymg bone LOCAL pos under identity (mean NN 2.50; x-mirror
  17.62 rules out x-flip; y-mirror also 2.50 — expected, both sides mirrored).

## 2. NEW: ycg-y-sign vs ymg-name-side (6 large-|y| records)

| ycg group | ycg y | NN ymg bone (dist) | name side | y<0=L? |
|---|---|---|---|---|
| 64DB300F | −8.25 | Bip L Finger4 (5.19) | L | YES |
| 64DB300F | +8.25 | Bip R Finger4 (5.08) | R | YES |
| 7CC9B660 | −4.54 | Bip L Finger4 (4.69) | L | YES |
| 7CC9B660 | +4.54 | Bip R Finger4 (4.75) | R | YES |
| 347D3654 | +5.38 | **Bip L Finger0 (2.52)** | L | **NO** |
| 347D3654 | −5.38 | **Bip R Finger0 (2.65)** | R | **NO** |

4/6 support y<0=L; **347D3654 (decisive NN: 2.52 vs 5.43 runner-up)
contradicts it** (y>0=L for this group).

## 3. Interpretation of the conflict

- 347D3654's yag track is ANIMATED within clips (84 keys, not static) →
  not the thumb (thumbs are posed-per-move, never animated). Its NN to
  Finger0 is likely positional coincidence; true anatomy unknown.
- ycg positions are parent-relative; parent frames vary per group (finger
  local frames are rotated — ymg Finger0/Finger1 local-y signs already
  violate the body convention). y-sign is only trustworthy for groups whose
  parent frame is body-aligned (thigh/clavicle-proven).
- **Conclusion:** ycg-y-sign → anatomical side is NOT uniform across groups
  headless. The final bit needs either (a) YOBJ full-mesh assembly (mesh
  shares the ymg frame; open problem), or (b) the CAW l1/r1 ground truth
  (edit_data/MODEL/Man/Wrist/mr0_000/l1.ymg vs r1.ymg — files located,
  v0x00030001 vertex format still to parse), or (c) visual reference.

## 4. Build recommendation (unchanged)

Map side-bits CONSISTENTLY (all SET→one side, all CLEAR→other) across every
track type. The output is correct up to a single global mirror, which is
functionally irrelevant for the chimera build (mirrored wrestling animations
are standard practice). Do NOT attempt per-group anatomical assignment —
the 347D3654 conflict proves headless per-group assignment is unreliable.

## 5. Provenance

- Probes: /tmp/wmxix-coord/lr_probe.py, lr_world.py, lr_sign.py (ephemeral).
- Source files: worktree .scratch model__wrestler__000_0.ycg,
  docs/wrestler-skeleton-000.json, docs/ycg-group-mapping.json.
- Did NOT modify the watchdog worktree; all work in /tmp.
