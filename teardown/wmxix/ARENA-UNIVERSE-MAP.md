# WMXIX ARENAS → WESTERN HEART UNIVERSE MAP

**How WrestleMania XIX's arenas become Eastern Mind fighting stages.**

The principle: WMXIX gives us **geometry** (arena layouts, wall structures, outdoor environments, cage frameworks). Eastern Mind gives us **soul** (bitmaps, textures, atmosphere, meaning). We take their bones and give them our spirit.

**Status:** Arena meshes are mapped in the ISO but not yet decoded (YOBJ vertex dequantization in progress — see `~/workspace/tools/wmxix-mesh-decode/APPROACH.md`). This document maps what each arena *becomes* so decoding has a target.

---

## PART 1: COMPLETE ARENA INVENTORY

### Main Show Arenas (`bg/00`, `bg/01`, `bg/02`)

| Slot | Files | Likely Identity |
|------|-------|-----------------|
| `00` | 00.ymg (304KB), 00.tex (666KB), 00.ycg, 00_add/ent/gt/light/scr variants | Primary weekly show arena (RAW) |
| `01` | 01.ymg (279KB), 01_ent.tex, 01_light variants | Secondary weekly show arena (SmackDown) |
| `02` | 02.ymg (230KB), 02.tex (687KB) | PPV/WrestleMania XIX main arena |

Each has: base mesh (`.ymg`), textures (`.tex`), skeleton (`.ycg`), entrance staging (`.ent`), ground/terrain (`.gt`), lighting rig (`.light`), screen overlays (`.scr`).

**What we get:** Three full enclosed wrestling arenas with entrance ramps, ring aprons, crowd bowl geometry, lighting rigs, and Titantron screen placements.

### Revenge Mode Environment Sets (lettered slots)

WMXIX's Revenge Mode sends you fighting through real-world locations outside the ring. These are the out-of-ring brawling environments:

| Slots | Count | Type |
|-------|-------|------|
| `A0`–`A4` | 5 | `.pac` arena packages (~1.1MB each) — full environment sets |
| `C0`–`C2` | 3 | `.pac` arena packages — environment sets |
| `F1`–`F6` | 6 | `.pac` arena packages — environment sets |
| `H3`–`H9` | 7 | `.pac` arena packages — environment sets |
| `P0`–`P3` | 4 | `.pac` arena packages — environment sets |
| `S0`–`S5` | 6 | `.pac` arena packages — environment sets |
| `T0`–`T3` | 4 | `.pac` arena packages — environment sets |

**Total: 35 environment packages.** Exact location identities (construction site, parking lot, mall, etc.) are not yet documented — this is teardown work still open. What matters for Western Heart: these are **outdoor/open-air brawling environments** with varied geometry (not just flat rings).

### Backstage Areas (`bg/bs/`, 61 files)

| Pattern | Content |
|---------|---------|
| `bs/0_0` through `bs/1_1` | Backstage corridor/room sets with `.tex` (390–810KB), `.ymg` (270–475KB), `.ycg`, `_ad2` variants, lighting |

**What we get:** Enclosed interior corridor/room geometry — hallways, locker rooms, backstage areas. Perfect donors for interior stages.

### Cage Structures (`bg/cage/`, 2 files)

| File | Likely Identity |
|------|-----------------|
| `cage.pac` | Standard steel cage match structure |
| `hell.pac` | **Hell in a Cell** — the roofed cell structure |

**What we get:** Enclosed fighting structures with walls on all sides + roof. The Hell in a Cell is the most architecturally unique — a complete enclosed combat box.

### Props & Dressing

| Directory | Files | Content |
|-----------|-------|---------|
| `bg/object/` | 61 | Environmental props for Revenge Mode locations |
| `bg/placard/` | 51 | Crowd signs, banners, arena dressing |
| `bg/weapon/` | 61 | Hardcore weapons (chairs, tables, etc.) |
| `bg/audi.pac` | 1 | Audience/crowd package |
| `bg/vw.pac` | 1 | View/visual package |
| `bg/tuto.pac` | 1 | Tutorial arena |
| `bg/light.pac` | 1 | Lighting package |
| `bg/f0`, `bg/h0`–`h2` | 4 | Miscellaneous arena pieces |

**What we get:** A full prop library for dressing stages — objects to scatter, crowd systems, weapon geometry (some adaptable as stage props).

### Inventory Summary

| Category | Count | Decoded? |
|----------|-------|----------|
| Main show arenas | 3 | Mapped, not decoded |
| Revenge Mode environments | 35 | Mapped, not decoded |
| Backstage interiors | ~8 sets | Mapped, not decoded |
| Cage structures | 2 | Mapped, not decoded |
| Prop/object/weapon/placard libraries | 234 files | Mapped, not decoded |
| **TOTAL** | **~45 arena configurations** | **0 decoded yet** |

---

## PART 2: UNIVERSE MAPPING — WHAT EACH BECOMES

### The Translation Principle

Every WMXIX arena goes through three transformations:

1. **STRIP** — Remove WWE branding: Titantron screens → blank or Eastern Mind imagery, crowd signs → removed or replaced, ring aprons → retextured, American arena architecture → neutralized
2. **RESCALE** — Tekken-style fighting happens on a tighter plane than wrestling. The ring area becomes the combat zone (~16.8 units wide per the stage template). Surrounding geometry becomes background/visual depth.
3. **RE-SOUL** — Apply the Eastern Mind land identity: the land's element, color palette, bitmap textures, atmospheric effects, and meaning.

### Type-by-Type Mapping

#### Main Show Arenas (00, 01, 02) → Enclosed Palace Stages

The three big indoor arenas are the donors for **walled stages** — places where the architecture closes in.

| WMXIX Source | Western Heart Target | What Changes | What Stays |
|--------------|---------------------|--------------|------------|
| `00` (primary arena) | **Helix Palace** (Stage 2) | Titantron → five glowing doorways (Greed, Appetite, Immortality, Sexual Desire, Destruction); crowd → reflective metallic surfaces; arena lights → sickly colored glows | Enclosed bowl shape, wall structure (enables wall combos), entrance ramp (becomes palace corridor), tiered seating geometry (becomes palace balconies) |
| `01` (secondary arena) | **Octagonal Shrine Par-Fang** (Stage 6) | Everything WWE → ancient stone; bright arena → dim sacred stillness; screens → removed | Enclosed structure, dramatic verticality, the feeling of being inside something ancient and significant |
| `02` (PPV arena) | **Phantom Marketplace** (Stage 5) | Concourse areas → market stalls; crowd → giant watching eyes; bright lights → liminal twilight | Large open interior, multiple levels/zones (becomes market districts), the bustling energy of a full venue |

#### Revenge Mode Environments (A/C/F/H/P/S/T slots) → Open Land Stages

The 35 outdoor brawling environments are the donors for **open stages** — places where the sky is visible and movement is free.

| WMXIX Source Type | Western Heart Target | What Changes | What Stays |
|------------------|---------------------|--------------|------------|
| Outdoor industrial/construction (likely F or H slots) | **Plains of Chi-U** (Stage 1) | Concrete/steel → scorched earth; construction lights → burning sky; scaffolding → Fire Tower of Time silhouette | Open flat fighting plane, scattered vertical elements (become background structures), no walls (maximum movement) |
| Outdoor natural/park (likely S or T slots) | **Tree of Life** (Stage 4) | Urban → Sha-mo Desert; any greenery → colossal tree; sky → Eastern Mind horizon | Open outdoor layout, natural ground plane, distant background geometry (becomes desert/tree vista) |
| Any open environment + shader work | **Palace of Dreaming** (Stage 3) | Stable reality → rippling/morphing; solid → reflective and uncertain | The fighting plane itself (must stay stable for gameplay); everything *around* it gets the water/morph shader treatment |

**Note:** Exact slot-to-location mapping (which letter = construction site vs. parking lot) is still open teardown work. The mapping above is by *type*, not specific slot. Once arenas are decoded, we'll assign specific slots to specific stages based on what the geometry actually looks like.

#### Backstage Interiors (bs/) → Corridor/Transition Spaces

| WMXIX Source | Western Heart Target | What Changes | What Stays |
|--------------|---------------------|--------------|------------|
| Backstage corridors/rooms | **Helix Palace interior rooms** (Stage 2 background) | Fluorescent → sickly colored glow; concrete → reflective metal; doors → the five desire doorways | Corridor layout, room divisions, the feeling of moving through connected interior spaces |
| Backstage areas | **Wrestling Mode** locker room / pre-fight areas | WWE → neutral; branding → removed | Functional interior spaces for the separate Wrestling Mode |

#### Cage Structures → Sacred Enclosed Stages

| WMXIX Source | Western Heart Target | What Changes | What Stays |
|--------------|---------------------|--------------|------------|
| `hell.pac` (Hell in a Cell) | **The Drill Wound** (Stage 7, secret) | Steel mesh → bone and screaming faces; cell roof → wound interior; industrial → organic horror | **The entire enclosed-box concept** — fighting inside something that closes over you. The cell *is* the wound. Green blood rain replaces arena lighting. Floating eyeballs replace crowd. |
| `cage.pac` (steel cage) | **Octagonal Shrine Par-Fang** alt / Wrestling Mode cage matches | Steel → ancient stone/metal; chain-link → carved panels | Eight-sided enclosure maps to the octagonal shrine concept; wall-bounce geometry |

The Hell in a Cell → Drill Wound mapping is the most direct in the entire set. A roofed steel cage where you can't escape is *already* the feeling of being inside a wound. We just change what the walls are made of.

#### Prop Libraries → Stage Dressing

| WMXIX Source | Western Heart Use |
|--------------|-------------------|
| `bg/object/` (61 files) | Scatter props for Revenge Mode-derived stages; retextured to Eastern Mind objects |
| `bg/placard/` (51 files) | Template for crowd-sign *system* (replaced with Eastern Mind sigils/glyphs, not WWE signs) |
| `bg/weapon/` (61 files) | Wrestling Mode weapons; some adaptable as stage props (tables → market stalls, etc.) |
| `bg/audi.pac` | Crowd system architecture — how to populate background with watchers (replaced with eyes/souls/spirits per stage) |

---

## PART 3: BEFORE/AFTER — THE 7 STAGES

### STAGE 1: PLAINS OF CHI-U (Fire / Confrontation)

| | Before (WMXIX) | After (Western Heart) |
|---|---|---|
| **Donor** | Revenge Mode outdoor industrial environment (F/H slot, TBD after decode) | — |
| **Geometry** | Flat brawling area, scattered construction/industrial props, open sky | Same flat plane. Props removed or replaced with scorched debris. |
| **Lighting** | Daylight or construction floodlights | **Burning sky** — deep orange/red gradient. The Fire Tower of Time looms as a background silhouette (modeled or billboarded). |
| **Floor** | Concrete/asphalt texture | Scorched earth with half-melted clock faces embedded (Eastern Mind bitmap) |
| **Walls** | None (open) | None (open) — souls don't fall out of the head |
| **Atmosphere** | Urban brawl | Confrontation. Heat shimmer. The air itself feels aggressive. |
| **Force on win** | — | **Fire** — +chip damage for the rest of the set |

### STAGE 2: HELIX PALACE (Metal / Eternity)

| | Before (WMXIX) | After (Western Heart) |
|---|---|---|
| **Donor** | `bg/00` primary show arena + `bg/bs/` backstage interiors | — |
| **Geometry** | Enclosed arena bowl, entrance ramp, tiered seating | Same bowl. Seating tiers become palace balconies. Ramp becomes palace corridor. Backstage rooms become the five desire chambers (visible through doorways). |
| **Lighting** | Bright arena spots, Titantron glow | **Sickly colored glows** — each of the five doorways (Greed, Appetite, Immortality, Sexual Desire, Destruction) emits its own color. Everything reflective, metallic, too shiny. |
| **Floor** | Wrestling mat / arena floor | Polished reflective metal (Metal063/Metal049A from ambientCG) |
| **Walls** | Arena walls, crowd barriers | **Walled** — palace walls. Wall combos enabled. |
| **Atmosphere** | Sports entertainment spectacle | Eternity. Desire. The bedazzled-Jello aesthetic at maximum. It wants you to stay forever. |
| **Force on win** | — | **Metal** — health regenerates slightly between rounds |

### STAGE 3: PALACE OF DREAMING (Water / Change)

| | Before (WMXIX) | After (Western Heart) |
|---|---|---|
| **Donor** | Any open Revenge Mode environment (S/T slot, TBD) + custom shader layer | — |
| **Geometry** | Standard open brawling area | Unchanged fighting plane — **must stay stable for gameplay**. |
| **Lighting** | Normal | Shifting, uncertain. The light source seems to move when you're not looking. |
| **Floor** | Ground texture | Reflective surface showing a sky that isn't there (planar reflection or faked) |
| **Walls** | None | None — but the *background* walls ripple like water |
| **Atmosphere** | Normal | Change. Objects morph in peripheral vision (background animation only). The palace won't stay still. |
| **Force on win** | — | **Water** — faster sidestep for the rest of the set |
| **Technical note** | — | This stage is primarily a **shader/post-processing** transformation, not a geometry one. The WMXIX donor provides the base; the Dreaming identity is all in the material and background animation systems. |

### STAGE 4: TREE OF LIFE (Wood / Life)

| | Before (WMXIX) | After (Western Heart) |
|---|---|---|
| **Donor** | Revenge Mode outdoor natural environment (S/T slot, TBD) | — |
| **Geometry** | Open outdoor area with natural features | Same open plane. A **colossal tree** dominates the background (new geometry or large billboard — the Tree of Life with glowing soul-fruit). Roots break through the fighting plane as decorative non-interactive geometry. |
| **Lighting** | Daylight | Warm natural light, slightly golden. The Sha-mo Desert stretches to the horizon on one side. |
| **Floor** | Grass/dirt | Living earth with root textures (Wood096/Wood095 from ambientCG as base) |
| **Walls** | None | None (open) |
| **Atmosphere** | Outdoor brawl | Life. Growth. The tree watches. Soul-fruit glows softly. |
| **Force on win** | — | **Wood** — extended reach (hitbox extension) for the rest of the set |

### STAGE 5: PHANTOM MARKETPLACE (Liminal)

| | Before (WMXIX) | After (Western Heart) |
|---|---|---|
| **Donor** | `bg/02` PPV arena (large interior with concourse zones) | — |
| **Geometry** | Big indoor venue, multiple levels, concourse areas | Concourse levels become **market stall rows**. The arena floor becomes the central trading pit. Upper tiers become overlooking balconies where the eyes watch. |
| **Lighting** | Bright event lighting | **Liminal twilight** — neither day nor night. The light feels like it's coming from nowhere. |
| **Floor** | Arena floor | Packed earth / strange market ground (Fabric085/Fabric084 for stall awnings) |
| **Walls** | Arena walls | Open on the sides — but the **Eyeball Mountains** surround the venue. Giant eyes that follow the fighters (background animation). |
| **Atmosphere** | Big fight feel | The uncanny. Stalls sell things that shouldn't exist. The eyes never blink. |
| **Special** | — | **Mid-boss stage** — The Trader (Mokujin mimic). Win here to *trade* one claimed force for another. |
| **Force on win** | — | None — instead: force trading mechanic |

### STAGE 6: OCTAGONAL SHRINE PAR-FANG (Earth / Source)

| | Before (WMXIX) | After (Western Heart) |
|---|---|---|
| **Donor** | `bg/01` secondary arena + `bg/cage/cage.pac` structural concept | — |
| **Geometry** | Enclosed arena | Transformed into an **eight-sided shrine**. Stone, ancient, still. Smaller fighting area than other stages (more intimate, more final). The cage concept informs the octagonal enclosure — walls on eight sides. |
| **Lighting** | Arena spots | Minimal. Cold stone under a dark sky. The sky above is **the inside of the head** — dark, vast, veined. |
| **Floor** | Arena floor | Ancient stone (ambientCG stone textures — to be pulled) |
| **Walls** | Arena walls | **Walled** — eight stone walls. Wall combos enabled. The walls feel like they've been here forever. |
| **Atmosphere** | Sports arena | Source. Stillness. This is where it ends. The air is heavy with finality. |
| **Special** | — | **Final boss** — The Assembled Soul (True Ogre moveset). All nine styles. Yourself. |
| **Force on win** | — | **Earth** — damage reduction for the rest of the set |

### STAGE 7 (SECRET): THE DRILL WOUND (No Element)

| | Before (WMXIX) | After (Western Heart) |
|---|---|---|
| **Donor** | `bg/cage/hell.pac` (**Hell in a Cell**) | — |
| **Geometry** | Roofed steel cell enclosing the ring | **The cell IS the wound.** Same enclosed-box structure, but the walls are bone and screaming faces. The roof closes over you like the skull closing. |
| **Lighting** | Arena lights through mesh | **Green blood rain** (particle system). Sickly green ambient. The only light is biological. |
| **Floor** | Ring mat | Wound floor — wet, organic, wrong |
| **Walls** | Steel mesh | Bone walls with screaming faces (Eastern Mind drill-wound bitmaps). **Fully enclosed** — no escape, just like the Cell. |
| **Atmosphere** | Brutal cage match | Body horror. Eyeballs float past. The walls are alive and in pain. |
| **Unlock** | — | Win arcade mode without losing a round ("flawless trial") |
| **Force on win** | — | None. This stage gives nothing. It only witnesses. |

---

## PART 4: TECHNICAL INTEGRATION PLAN

### Pipeline: Decoded Arena → Godot 4

```
WMXIX ISO (bg/*.ymg)
  → YOBJ decoder (fixed-point s16 /64 — see tools/wmxix-mesh-decode/)
  → OBJ/FBX export
  → Blender cleanup (strip WWE branding, rescale to 16.8-unit combat plane)
  → Eastern Mind retexture (bitmap application, material assignment)
  → Godot 4 import (.glb via Blender export)
  → Stage JSON config (prototype/stages/{id}.json per STAGE-TEMPLATE.md)
  → Lighting/atmosphere pass (per-stage Godot WorldEnvironment)
```

### What STAGE-TEMPLATE.md Needs (Additions)

The current template (`prototype/stages/STAGE-TEMPLATE.md`) covers the basics. For WMXIX-derived stages, add:

```json
{
  "geometrySource": {
    "donor": "wmxix",
    "slot": "bg/00",
    "originalType": "main-show-arena",
    "decodeStatus": "pending | decoded | integrated"
  },
  "transformations": {
    "stripped": ["titantron", "crowd-signs", "wwe-branding"],
    "rescaled": true,
    "rescaleNotes": "Combat plane set to 16.8 units; surrounding geometry pushed to background layer"
  },
  "wallConfig": {
    "walled": true,
    "wallHeight": 3.0,
    "wallMaterial": "path/to/wall/texture/",
    "wallComboEnabled": true
  },
  "background": {
    "type": "3d-model",
    "layers": [
      {"distance": "near", "source": "arena-geometry-background"},
      {"distance": "far", "source": "eastern-mind-billboard-or-skybox"}
    ]
  },
  "atmosphere": {
    "worldEnvironment": "path/to/stage-env.tres",
    "fogColor": "#hex",
    "fogDensity": 0.0,
    "particles": ["blood-rain", "soul-fruit-glow", "heat-shimmer"],
    "animatedBackground": false
  }
}
```

### Lighting/Atmosphere System: The Five Lands + Liminal

Each land gets a **Godot WorldEnvironment preset**:

| Land | Ambient | Directional | Fog | Signature Effect |
|------|---------|-------------|-----|------------------|
| Fire (Chi-U) | `#3a1a0a` (ember) | `#ff6a2a` (burning) | Orange, light | Heat shimmer (shader) |
| Metal (Helix) | `#1a1a2a` (cold) | `#a0a0ff` (reflective) | None | Five colored point lights (desire doorways) |
| Water (Dreaming) | `#0a2a3a` (deep) | `#6abaff` (shifting) | Blue, medium | Ripple/morph background shader |
| Wood (Life) | `#2a3a1a` (natural) | `#ffdd88` (golden) | None | Soul-fruit glow particles |
| Earth (Shrine) | `#1a1a1a` (dark) | `#888899` (cold stone) | Dark, heavy | Veined head-interior skybox |
| Liminal (Marketplace) | `#2a2a3a` (twilight) | `#9999bb` (nowhere light) | Purple-gray | Watching eyes (animated background) |
| Wound (Drill) | `#0a2a0a` (sickly) | `#44ff44` (blood-green) | Green, dense | Blood rain particles, floating eyes |

### Decoding Priority Order

Not all arenas are equally urgent. Decode in this order:

1. **`hell.pac`** → The Drill Wound (most direct mapping, highest uniqueness)
2. **`bg/00`** → Helix Palace (walled stage, core to the game)
3. **`bg/01`** → Octagonal Shrine (final boss stage, high impact)
4. **One open Revenge Mode environment** → Plains of Chi-U (first stage players see)
5. **`bg/02`** → Phantom Marketplace (mid-boss, complex)
6. **Remaining** → Fill out the roster as needed

### File Organization (per TEARDOWN-TO-REPO LAW)

```
western-heart/teardown/wmxix/
  ARENA-UNIVERSE-MAP.md     ← this file
  arenas/
    hell/                   ← decoded Hell in a Cell
      hell.obj              ← raw decode
      hell-cleanup.blend    ← branding stripped, rescaled
      drill-wound.json      ← stage config
    arena-00/
      ...
  props/
    objects/                ← bg/object/ decodes
    weapons/                ← bg/weapon/ decodes (Wrestling Mode)
    placards/               ← bg/placard/ (reference for sigil system)
```

---

## OPEN QUESTIONS

1. **Exact Revenge Mode location identities** — Which lettered slot is the construction site? The parking lot? The mall? Requires either decoding and visually identifying, or finding WMXIX modding community documentation. Doesn't block the universe mapping (we map by type), but would sharpen specific assignments.

2. **Crowd system** — WMXIX has a full crowd (audi.pac, placard/). Western Heart replaces crowds with eyes/souls/spirits. Do we adapt the crowd *placement* system (where watchers go) while replacing the watcher *models*? Probably yes — the architecture is useful even when the content changes completely.

3. **Wrestling Mode arenas** — The separate Wrestling Mode (per owner's directive) needs its own arena set. The main show arenas (00/01/02) are the natural donors, kept closer to their wrestling origins. This document focuses on the Tekken-mode (Eastern Mind) transformation; Wrestling Mode arena mapping is a separate pass.

4. **Scale validation** — The 16.8-unit combat plane comes from the tk prototype's ARENA_LIMIT. WMXIX arenas are built for wrestling (larger ring + ringside area). The rescale factor needs validation once geometry is decoded — we may need to adjust either the template or the rescale approach.

---

*Mapping authored 2026-10-13. Updates as arenas decode — each decoded arena gets its specific slot assignment confirmed in this document.*
