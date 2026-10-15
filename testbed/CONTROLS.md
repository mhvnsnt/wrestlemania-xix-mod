# WMXIX Testbed — Controls Reference

**Verified against:** WWE WrestleMania XIX Prima Official Strategy Guide (2004), via archive.org
(`wwe-wrestlemania-xixprimas-official-strategy-guide-2004`).

**Source wins:** The guide's controls differ from common assumptions. This document follows the guide.

## Prima Button Numbering (GameCube)

| Prima # | GameCube Button |
|---------|----------------|
| 1 | A |
| 2 | B |
| 3 | Y |
| 4 | X |
| 5 | Start |
| 6 | L |
| 7 | R |
| 8 | Z |
| s | Control Stick |
| g | C-Stick |
| + Control Pad | D-pad |

## Real WrestleMania XIX Controls

| Action | Button (Guide) | Testbed |
|--------|----------------|---------|
| Walk / Move | Control Stick | Virtual joystick (left) |
| Light Grapple | A (tap) | A tap |
| Heavy Grapple | A (hold) | A hold (>300ms) |
| Light Strike | B (tap) | B tap |
| Heavy Strike | B (hold) | B hold (>300ms) |
| Strike Combination | B tap repeatedly | B tap repeatedly (alternates punch/kick) |
| Run | X (tap/hold) | X hold = run mode (2x speed) |
| Irish Whip | A+X, or X from grapple | X tap near opponent |
| Climb turnbuckle | X + Stick toward turnbuckle | Not yet (no turnbuckle interaction) |
| Grab Weapon | Y | Y (placeholder — no weapons in testbed) |
| Grapple Reversal (timed) | L | L shoulder button |
| Strike Reversal (timed) | R | R shoulder button |
| Tag Partner / Partner commands | Z near partner | Z (placeholder — 1 opponent) |
| Taunt | D-pad | ★ button |
| Special Taunt → Special Move | A+B with full Special Slot | A with full special meter |
| Pause | Start | II button (top-left) |
| Switch target / Camera | Z / C-Stick | Z (placeholder) |

## Testbed-Specific

- **Special Meter** (HUD bar): fills as you land actions. At 100%, next A press = Special Move.
- **Tap vs Hold**: 300ms threshold distinguishes light vs heavy (tap/hold).
- **Reversals**: In the real game these are timing-based against the opponent's attack animation. Testbed plays the reversal animation; full timing window vs AI attacks is future work.
- **Irish Whip**: Shoves the dummy toward the nearest ropes (real game: toward ropes, can throw in/out of ring).
