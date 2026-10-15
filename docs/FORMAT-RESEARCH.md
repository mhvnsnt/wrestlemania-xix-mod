# WrestleMania XIX — Format Research Notes

**Status:** Initial leads only. Nothing below is a confirmed format specification for every game build or platform.

## Target

The project targets WWE WrestleMania XIX for Nintendo GameCube. Confirm the exact region/revision from the owner's own copy before testing tools.

## Lead 1: MPC archive files

A public ZenHAX discussion titled "Day of Reckoning/Wrestlemania XIX .mpc files" reports that a community member adapted an existing QuickBMS script to inspect MPC archives used by Yukes wrestling games, including WrestleMania XIX. The post also notes a parsing issue and says reimporting was not yet working.

- Reference: https://zenhax.com/viewtopic.php%40t%3D17181.html
- Status: Unverified lead. Do not assume the script works on this project's exact dump or can safely rebuild archives.
- Next check: determine whether the owner's own disc image contains MPC files; record names, sizes, and SHA-256 hashes before testing anything.

## Lead 2: Community modding reports

A community thread documents a WrestleMania XIX mod project involving many textures and custom CAW content. This suggests texture replacement and save/CAW workflows are useful research areas, but it does not establish a general-purpose asset pipeline.

- Reference: https://legendsofmodding.org/threads/wrestlemania-xix-the-videogame.357/
- Status: Context only; not a format specification.

## Lead 3: General GameCube tools

GameCube File Tools (GCFT) supports several common GameCube formats, including GCM, RARC, BTI, J3D model formats, Yaz0, and Yay0. That is useful for identifying common containers, but it is not evidence that WrestleMania XIX uses those formats.

- Source: https://github.com/LagoLunatic/GCFT
- Releases: https://github.com/LagoLunatic/GCFT/releases
- Status: Candidate reference utility only. Do not copy it into this repository or assume compatibility without evidence.


## Lead 4: MPQ audio containers and YDSP audio

Older audio-modding discussions specifically mention WrestleMania XIX music stored in an MPQ container and describe YDSP audio extraction workflows used with Yuke's GameCube wrestling games. This is a separate lead from the MPC archive discussion; do not confuse MPQ and MPC.

- References: https://www.hcs64.com/mboard/forum.php?showthread=37239 and https://www.hcs64.com/mboard/forum.php?showthread=9185
- Status: Historical community reports; not a verified extractor/repacker for the user's exact game revision.
- Next check: search the user's file inventory for MPQ containers and the documented YDSP signature bytes, then verify candidate offsets and lengths on read-only samples before implementing anything.

## Investigation procedure

1. Work from a separate local copy of the owner's own game files.
2. Record platform, region/revision, filenames, file sizes, and SHA-256 hashes.
3. Inspect file signatures and sample bytes read-only; do not rely on extensions alone.
4. If MPC files exist, isolate a small sample and compare its structure against the public lead.
5. Keep format observations, hypotheses, and confirmed findings clearly separated.
6. Do not attempt archive repacking until extraction is understood and a round-trip test succeeds on a disposable copy.
7. Keep game images, proprietary extracted assets, and binaries out of Git by default.

## Current conclusion

The most concrete game-specific lead is the MPC archive discussion. The next meaningful step requires an inventory from the owner's actual game files; without that evidence, writing a game-specific extractor would be guesswork.
