# Realism plan (Ev said "go" — 2026-10-15)

Decision (from research): stay on the web. Realism = baked lighting (Blender Cycles) + PBR textures + env reflections,
inside the Quest budgets (<100 draw calls / 750K tris on Quest 2; <200 / 1.5M on Quest 3; 72 FPS). Everything free.

## Order of work
1. Photoreal LIBRARY room first (hero room): modeled + baked in Blender (bpy 5.2.2 in `bl/` venv), exported glTF,
   lightmap in the glTF occlusion slot (texCoord 1) -> three.js lightMap; KTX2 (toktx in `ktx/usr/bin`) + Meshopt via gltf-transform.
2. Drop it into the campus: `buildLibrary()` in parts/world.js keeps the interactive bits (book covers, proxies, signs,
   Rosa, freedom board), static geometry comes from the glTF. Same coordinates: X -32..-12, Z -13..7, H_LIB 7.6,
   door on east wall z -4.6..-1.4 (H_HALL 3.4), arched window on west wall z -5.2..-0.8 (y 1.0..4.6).
3. WebXR entry (VR button, XR rig follows cam, thumbstick walk, HUD hidden in VR).
4. Preview deploy (Vercel PREVIEW only, never production) + artifact republish.
5. Later: other rooms through the same pipeline; IWSDK port for VR hand grabbing.

## Files
- bl/            Python venv with bpy (Blender 5.2.2 LTS as a module). `bl/bin/python`.
- bl/textures.py tileable PBR texture generator (numpy/PIL) -> assets/tex/
- bl/library.py  builds the room, bakes, exports -> assets/lib/
- bl/post.py     glTF post-process (lightmap, compression)
- ktx/usr/bin/toktx  KTX2 encoder (needs LD_LIBRARY_PATH=ktx/usr/lib)
- Poly Haven / ambientCG are BLOCKED by the proxy; all textures are generated here (CC0-equivalent, ours).

## Blender <-> three.js axes
Blender (x, y, z) -> glTF (x, z, -y). Model in Blender with X = campus x, Y = -campus z, Z = up.

## Deploy of big assets (status 2026-10-15 17:05)
- deploy/assets.json lists { files:[{ dest:'lib/lib.glb', url:<github release url>, sha256 }] }; make_patch.mjs bundles
  parts/fetch_assets.mjs as web/fetch_assets.mjs and the Vercel build runs it (downloads into public/lib with hash check).
- Needs Ev's OK for a public repo `xr-campus-assets` on his GitHub (asked 2026-10-15 16:20; gh is authenticated as bIipn, REST only).
- Artifact (claude.ai): publish lib/lib.glb + lib/probe.hdr as artifact `files` (no token cost).
- Full bake running in background: assets/lib/bake_full.log (started 16:58). After it: bl/bin/python bl/post.py && node tools/post.mjs assets/lib lib

## Resumable bake (after the container restarted mid-bake, 2026-10-15 17:24)
- `nohup nice -n 5 bl/bin/python bl/bake.py --lm 128 --vc 96 --size 2048 > assets/lib/bake.log 2>&1 &`
  loads assets/lib/library.blend, bakes per object, saves lightmap.exr + bake_progress.json + bake_work.blend after each;
  re-run the same command to resume. Ends with 'bake complete' (probe.exr + lib_raw.gltf exported).
- Then: `bl/bin/python bl/post.py && node tools/post.mjs assets/lib lib` -> assets/lib/lib.glb + probe.hdr
- Then copy to /home/claude/xr-campus-assets/lib/ (repo bIipn/xr-campus-assets, cloned, push works), commit+push,
  `python3 tools/assets_manifest.py /home/claude/xr-campus-assets` -> deploy/assets.json, then build_deploy.py, make_patch.mjs, deploy preview.
- Artifact: publish xrlibraries-campus.html with files {'lib/lib.glb', 'lib/probe.hdr'} (url https://claude.ai/artifact/57Bmd1ZgY9mV49uM4aSHeC).
- Calibrate BAKED.lib.exposure in parts/baked.js against assets/lib/preview_window.jpg (Blender AgX, exposure -1).

## Status 2026-10-15 22:00 PDT — DONE for the library
- Full bake done (2K lightmap 128 spp, vertex 96 spp, shelf rows got their own 1024x512 lightmap via bl/bake_rows.py because
  vertex lighting sampled only their corners). Lightmaps travel in the glTF *emissive* slot (occlusion would be squeezed to 1 channel
  by gltf-transform); parts/baked.js moves emissiveMap -> lightMap. BAKED.lib.exposure = 0.78 (matched to Blender AgX preview).
- Assets pushed: bIipn/xr-campus-assets commit f96a0a3 (lib/lib.glb 8.75 MB, lib/probe.hdr). deploy/assets.json pins that commit.
- Vercel PREVIEW dpl_2Z1UDbGm9EBqVqY53XpFyDfqE4Jw https://walk-the-archive-jmhgtppvm-biipns-projects.vercel.app (build fetched both assets, sha256 ok).
- Artifact Version 11 (https://claude.ai/artifact/57Bmd1ZgY9mV49uM4aSHeC): room files as base64 .txt (artifact host rejects .glb/.hdr).
  Regenerate with: python3 -c "import base64;[open('assets/lib/'+n+'.txt','w').write(base64.b64encode(open('assets/lib/'+n,'rb').read()).decode()) for n in ('lib.glb','probe.hdr')]"
- Next: other rooms through the same pipeline (library.py is the template), IWSDK port for hand grabbing, NPC instructors. VR entry untested (needs a headset).
