# xr-campus-assets

Baked 3D rooms for the **XRLibraries Campus** concept (an unofficial concept by Ev Holt, *Walk the Archive*).
These files are downloaded by the site's build and loaded by the campus page at runtime.

| Path | What it is |
|---|---|
| `lib/lib.glb` | The Reading Room (library): geometry (Meshopt), KTX2 textures, baked lightmap in the occlusion slot (texCoord 1), baked vertex lighting on small objects |
| `lib/probe.hdr` | Reflection probe rendered from the middle of the room (RGBE, 512×256) |

Everything here was modelled, textured and lit from scratch in Blender (Cycles) with procedurally generated textures;
nothing was downloaded from asset libraries. The campus itself lives in a separate project.
