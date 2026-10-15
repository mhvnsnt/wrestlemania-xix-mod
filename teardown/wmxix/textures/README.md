# WMXIX Arena Textures

**1,167 PNGs** decoded from the GameCube TPL textures inside `bg/*.tex`
(2026-10-13). Per-arena directories match the 43 arena OBJ names.

## Format (measured)

`.tex` container: `[u32 LE count][u32 0x10000][u32 0][u32 0x10]`
+ count × 32-byte entries: `[16B name]["tpl\0"][u32 LE size][u32 LE data offset][u32 0]`

Each entry is a standard GameCube **TPL** (magic `0x0020AF30`):
`[u32 magic][u32 numImages][u32 imageTableOffset]`; the image table is
numImages × u32 offsets to 36-byte image headers:
`[u16 height][u16 width][u32 format][u32 dataOffset][u32 wrapS][u32 wrapT]`
`[u32 minFilter][u32 magFilter][f32 lodBias][u8 edgeLOD][u8 minLOD][u8 maxLOD][u8 unpacked]`.
Paletted formats (C4/C8/C14X2): palette header follows the image headers —
`[u16 numEntries][u16 pad][u32 palFormat 0=IA8/1=RGB565/2=RGB5A3][u32 palOffset]`.

Decoder: `../decode_tpl.py` (formats I4/I8/IA4/IA8/RGB565/RGB5A3/RGBA8/C4/C8/C14X2/CMPR).

**Validation:** decoded `edit_data/.../tq0_417_TPL/c3_c_00.tpl` (C8 paletted, 64×32)
against the artist's source `.tga` of the same texture left on disc —
mean abs diff 4.2/255 (palette quantization only). Also eye-verified:
`ring/ar_a3.png` is the WWF.com ring-apron banner, pixel-perfect.

## Coverage

19 of 43 arenas have same-basename `.tex` companions (see `TEX-MANIFEST.txt`).
24 have none on disc:
- `01` (bg/01.tex absent — shares bg/00/bg/02 texture set or untextured)
- `*_ad2` LOD variants (share base arena textures)
- `add_x8, eff_x8, gt_x8, scr_x8, scr_wm, post, c_mat, mat, dummy_x8`
  (small untextured pieces / materials)

Extractor: `../extract_arena_textures.py` (streams from ISO, no intermediates).
