# Look development: from greybox to photoreal

M1 gives an accurate campus lit by Lumen, but its surfaces are the web build's painted canvases. M2 replaces them room by room.
The order below gives the biggest visual jump first. Check every change on the **Epic** preset at 1440p, and once on
**Cinematic** with the Path Tracer for a ground-truth comparison.

## 1. Lighting first (an hour, huge payoff)

- **Exposure:** the unbound PostProcessVolume uses auto exposure in EV100 (about 4 indoors to 15 in sun) with Local Exposure on. Tune *Exposure Compensation* per wing with small local PostProcessVolumes; the setup builds one for the Workshop School (+0.7, so white classrooms read white instead of grey). Reading Room +0.3 to +0.7 is worth a try, galleries 0, yard 0.
- **Self-lit surfaces:** the web's glows are display referred, so the setup gives light fixtures physical luminance (about 3,000 cd/m² for a ceiling panel; saturated indoor glows about 250 so they keep their colour) and puts the web's unlit pictures (frosted windows, screens, labels, the horizon) on `M_WTA_Unlit`, which shows them as drawn whatever the exposure. Both stay out of Lumen's GI (`emissive.py`).
- **Sun and sky:** one Directional Light (*Atmosphere Sun Light* on), Sky Atmosphere, Sky Light (*Real Time Capture*), Volumetric Clouds and Exponential Height Fog with volumetric fog. In the Reading Room, a little volumetric fog makes visible light shafts through the arched window.
- **Practical lights in physical units:** gallery downlights around 1,500–3,000 lm (the setup puts a 2,000 lm downlight under each museum ceiling disc), desk lamps 800–1,000 lm at 2700–3000 K, Reading Room pendants 8–11 klm, plus a large Rect Light under the laylight (about 5000 K). Each school ceiling panel is a Rect Light of its own size (3,500 lm, pointing down). Each exhibit has its own spotlight (about 600 lm, 30° cone); keep artwork the brightest thing in a gallery.
- **MegaLights** keeps many shadowed lights cheap. Give the shadowed lights a source radius of 2–8 cm so shadows look soft and real.

## 2. Materials (most of the work)

Use one **master material** (Substrate slab) with texture-set parameters (base colour, normal, ORM/roughness, optional height for Nanite displacement) and make a material instance per surface.
Sources, in order of preference:

1. **Fab / Quixel Megascans** inside the editor (*Window → Fab*): photoscanned surfaces and props that import with Nanite. Since 2025 most Megascans cost money, but a free subset remains, and anything claimed before 2025 stays in your library. Check each item's licence in the Fab panel.
2. **Poly Haven** (CC0, no attribution needed): textures, HDRIs and models. Search on polyhaven.com for the terms below.
3. The repo's generated textures in `assets/tex` (licence-clean fallback). `bl/textures.py` can regenerate them at 4K.

| Surface | Where | Search terms | Notes |
|---|---|---|---|
| Polished stone / terrazzo floor | Lobby, galleries | "terrazzo", "marble floor", "polished concrete" | Low roughness with variation so reflections break up |
| Painted plaster walls | Galleries (colours per gallery: teal, navy, plum) | "plaster", "painted wall" | Tint the base colour per gallery from `DT_Galleries.WallColor` |
| Oak parquet | Reading Room floor | "wood floor", "oak planks", "parquet" | Keep the web layout; add a rug with fibre normals |
| Walnut joinery | Reading Room cases, rails, window | "walnut", "dark wood" | Clearcoat for lacquer |
| Book spines | Reading Room | modelled already | Vary hue and roughness per book; add worn edges |
| Leather | Chairs | "leather" | Subsurface off; use sheen |
| Brass | Lamps, rails, signs | "brass", "worn brass" | Metallic 1, roughness 0.25–0.45 with smudges |
| Glass | Exhibit cases, windows | engine glass | Translucent, front-layer reflections on |
| Linoleum, lockers, tiles | Workshop School | "linoleum", "painted metal", "ceramic tiles" | |
| Stone / brick exterior | Building shells | "stone wall", "brick" | Thick walls; add trims |
| Pavers, grass, soil | Recess Yard | "paving", "grass", "soil" | Landscape + Megascans grass/foliage; Nanite foliage is experimental in 5.8 |

## 3. Set dressing and detail

- Replace greybox furniture with Megascans/Fab props of the same size (benches, lecterns, lab equipment, lockers, planters).
- Add the small things real rooms have: skirting boards, light switches, exit signs, fire extinguishers, vents, cable trays in the school, scuffs on floors near doors, dust on high shelves.
- Exhibit art: keep the web artwork (`/Game/WTA/Art`) on the canvases, but give the frames real wood and glass, and add museum placards with real typography.

## 4. People and motion

See `HUMANS.md`. Small ambient motion makes spaces feel alive: curtains, dust motes in light shafts (Niagara, very few particles, large and soft, so no sparkle), the coaster running in the background, birds outside.

## 5. Camera and post

- Field of view about 75–80° on a 16:9 monitor; head-bob is gentle (2.6 cm) and can be turned off.
- Motion blur off while walking, on for rides and cinematics. Film grain off or very low. Bloom subtle (default threshold), lens flares off.
- Keep colour grading light. Tone mapping stays Unreal's default filmic curve; match the Reading Room against the Cycles reference stills in `assets/lib/preview_window.jpg` and `preview_stacks.jpg`.

## 6. Performance targets

| Preset | Target |
|---|---|
| Epic | 1440p 60 fps on RTX 4070 / RX 7800 XT class (TSR 67%) |
| High | 1080p 60 fps on RTX 3060 / RX 6600 class |
| Medium (Lumen Lite) | 1080p 60 fps on older GPUs, Steam Deck-class handhelds |
| Cinematic | Screenshots and trailers only |

Use `stat unit`, `stat gpu`, *Lumen* and *Nanite* visualisation modes, and the 5.8 MegaLights light-finder view to find hotspots.
