# No Mercy Wrestlers

Port of the 10 working WWF No Mercy (N64, 2000) wrestler models — 13 GLB files —
into the WrestleMania XIX modding project. Moved per owner directive 2026-10-16:
these models live in the wrestling game, not in Western Heart.

## Roster

| Wrestler | Files |
|----------|-------|
| Kevin Nash | `kevin_nash/kevin_nash_1.glb` |
| Kurt Angle | `kurt_angle/kurt_angle_1.glb` |
| Rhyno | `rhino/rhyno_1.glb` |
| Rob Van Dam | `rob_van_dam/rob_van_dam_1.glb` |
| Scott Hall | `scot_hall/scott_hall_1.glb` |
| Shawn Michaels | `shawn_michaels/shawn_michaels_1.glb`, `shawn_michaels_2.glb` |
| Stephanie McMahon | `stephanie_mcmahon/stephanie_mcmahon_1.glb` |
| Steve Austin | `steve_austin/steve_austin_1.glb` |
| The Rock | `the_rock/the_rock_1.glb`, `the_rock_2.glb`, `the_rock_bald.glb` |
| Triple H | `triple_h/triple_h_1.glb` |

## Provenance

- **Source:** `game-reverse-engineering/wwf-no-mercy/re-docs/assets/3d Assets/characters/`
  in the Western Heart pipeline workspace (reverse-engineered from WWF No Mercy,
  AKI engine). Subdirectory names preserved as-is for traceability (`rhino/`,
  `scot_hall/` match the source layout).
- **Status:** all 13 files verified working per the teardown model inventory.
- **Format:** glTF 2.0 binary (`.glb`).
- **Moved:** 2026-10-16 via PR `feature/no-mercy-wrestlers` — COPY, not delete.
  Source files remain untouched in the Western Heart workspace.

## File hashes (SHA-256, at move time)

```
751dfe8d91c4052a3f84b344641f7d2eea539365a2fea01f30b98f550baaa138  kevin_nash/kevin_nash_1.glb
945dc3fa5f8db306f51c2d2f7d2893e4125a74876c17a501ed1715d895a9fe49  kurt_angle/kurt_angle_1.glb
ce4925ca16b39c8009e3bbe7450236dc8f6df6d3846ac94ab52605d248dc62bf  rhino/rhyno_1.glb
96dba8097b6e0db231781c2a8cfc7cc5decf21140c8100a88dc711588f980dcc  rob_van_dam/rob_van_dam_1.glb
6bdb6543a08e331e9aef70ac5a8cb13529c4efc7cdc890544e6f6d660b951fe5  scot_hall/scott_hall_1.glb
c5a699c03752fffaa32512b265a3249d157ca0c4c9b13ae30bc50459fb9017da  shawn_michaels/shawn_michaels_1.glb
4ac44b43db73a4119b9f1094ad57ba4bc8bf8bdfc320cc39d6cef13ec9a17423  shawn_michaels/shawn_michaels_2.glb
16e1d0ca06783283d7d48515d26ec4abbb9b32f9e03b91cc381fa30fbf5b9454  stephanie_mcmahon/stephanie_mcmahon_1.glb
a85269a41acc109094b881ab061745967ef501b2278aafdb76bb916b56c56b30  steve_austin/steve_austin_1.glb
03a8c481e2edc9b72f2909c9d4881f2692339897de768dae93755104418ed329  the_rock/the_rock_1.glb
9ebb6cf2c080e641c8526902a1573cec8ca927e12b13d5a1a6c581adc0968fa9  the_rock/the_rock_2.glb
15666cadf09d17c84297e211c0d6b8f503bc7eea03203387bcbe23322689a6a5  the_rock/the_rock_bald.glb
a497d54890dcccfca14fd9dcfffa0b75090966fcb932f22edde494a0daf2b921  triple_h/triple_h_1.glb
```

## Target version

WrestleMania XIX (GameCube, GW9E78) — models are reference/port assets for the
WMXIX modding toolchain, not game-native YOBJ files.

## Installation

No install required — reference assets. Consumers: import GLBs into Blender
(`File > Import > glTF 2.0`) or any glTF tool to compare against `teardown/wmxix/`
YOBJ wrestler models.

## Validation

`sha256sum -c` against the hash block above. Re-exported files keep the original
names; variants get new filenames.

## Uninstall / rollback

Delete this folder. Nothing else in the repo references it.
