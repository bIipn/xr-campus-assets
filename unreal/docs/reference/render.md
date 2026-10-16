# Unreal Engine 5 — current release and max-fidelity PC rendering setup (research, 2026-10-16)

Scope: the Walk the Archive / XRLibraries Campus port (interior-heavy, photoreal, walkable; PC first; Mac unknown). Everything below is for **UE 5.8.x** unless stated. Each claim is tagged with how it was verified:

- **[docs]** Epic documentation / release notes / unrealengine.com text (seen through search-engine excerpts; dev.epicgames.com itself is not reachable from this container).
- **[src]** verified against engine source or config files: a public `UE5.7` source mirror (`RendererSettings.h`, `Scene.h`, `EngineTypes.h`, `Version.h` = 5.7.0) and a packaged **UE 5.8** `BaseScalability.ini` (dated 2026-10-15, identified as 5.8 because Medium GI selects `r.Lumen.FinalGatherMethod=0`, i.e. Lumen Lite). Copies are in `(research cache: raw engine headers, not in repo) `.
- **[ini]** key seen in real shipped `DefaultEngine.ini` files on GitHub (confirms spelling and section).
- **[2nd]** secondary coverage only (Tom Looman, Guru3D, Digital Production, forum posts, Epic staff replies). Treat as likely but re-check in the editor.
- **[unverified]** could not confirm; do not rely on it.

Section 12 lists every item I could not confirm.

---

## 1. Current version (as of 16 Oct 2026)

| Item | Value | Verification |
|---|---|---|
| Latest release line | **Unreal Engine 5.8** | [docs] unrealengine.com "Unreal Engine 5.8 is now available"; dev.epicgames.com 5.8 release notes |
| 5.8.0 release date | **17 June 2026**, announced at State of Unreal 2026 (Unreal Fest Chicago). Some outlets print 18 June; one third-party blog claims 23 June (ignore). | [docs]/[2nd] |
| Latest hotfix | **5.8.3**, forum post "5.8.3 Hotfix Released" (author Flak), **22 Sept 2026**. Earlier: 5.8.1 = 28 July 2026; 5.8.2 = late Aug 2026 (on or before 31 Aug). | [2nd] forum + two independent dates |
| Newer preview? | **No 5.9 Preview exists** as of today. Epic calls 5.8 "the last planned major UE5 release"; a "5.9 confirmed" claim from Unreal Fest Seoul (20–21 Aug 2026) exists only in secondary sources (AI/MCP-plugin focus, no date). Plan on 5.8.x. | [docs]/[2nd] |
| Next engine | **UE6 Early Access targeted late 2027** (Epic, State of Unreal 2026). | [docs] |
| Previous line | 5.7 shipped Nov 2025 (last hotfix seen: 5.7.4). | [2nd] |
| "Production Ready" in 5.8 (official list) | MegaLights, Movie Render Graph, Audio Insights, Dataflow for Chaos Cloth, Live Link Hub, Iris. | [docs] State of Unreal 2026 roundup |
| New in 5.8 (rendering) | **Lumen Lite (Beta)**; MegaLights production + noise reduction + transmission (SSS) support + "light finder" debug; Metal Ray Shaders + **Path Tracing on Mac** (use macOS ≥ 26.4); Intel-Mac rendering removed; experimental SM6 on iOS (Metal Shader Converter); Mesh Terrain (Experimental); Procedural Vegetation Editor (Experimental, Nanite foliage); Substrate Toon Shading (Experimental); "Fog Screen Space Scattering" (Experimental); shader-permutation reductions across VSM/Substrate/MegaLights/Lumen/volumetric fog. | [docs]/[2nd] |

Install target for Cowork: **UE 5.8.3** from the Epic Games Launcher (Windows or macOS). `.uproject` → `"EngineAssociation": "5.8"`.

---

## 2. RHI / shader-model requirements (what the headline features need)

[docs] "Some features of Unreal Engine 5 require DirectX 12 with Shader Model 6 (SM6) to work, such as Nanite and Virtual Shadow Maps." and "Lumen Hardware Ray Tracing now requires SM6 to be set in Project Settings."

Epic's "Supported features by rendering path (desktop)" table [docs]:

| Rendering path | Lumen SWRT | Lumen HWRT | Nanite | VSM | TSR | Path Tracer |
|---|---|---|---|---|---|---|
| Deferred, DX12 SM6 (Windows) | yes | yes | yes | yes | yes | yes |
| Deferred, Vulkan SM6 (Linux/Windows) | yes | yes | yes | yes | yes | yes |
| Deferred, Metal SM6 (macOS, Apple Silicon) | yes | yes (Experimental, see §11) | yes (Beta, M2+) | yes (Beta, M2+) | yes | yes (5.8+) |
| Deferred, DX11 / Metal SM5 | yes | no | no | no | yes | no |
| Forward (any) | no | no | no | no | no | no |

Project settings (verified keys, [ini]):

```ini
[/Script/WindowsTargetPlatform.WindowsTargetSettings]
DefaultGraphicsRHI=DefaultGraphicsRHI_DX12
-D3D12TargetedShaderFormats=PCD3D_SM5
+D3D12TargetedShaderFormats=PCD3D_SM6
-D3D11TargetedShaderFormats=PCD3D_SM5

[/Script/MacTargetPlatform.MacTargetSettings]
-TargetedRHIs=SF_METAL_SM5
+TargetedRHIs=SF_METAL_SM6

[/Script/LinuxTargetPlatform.LinuxTargetSettings]
-TargetedRHIs=SF_VULKAN_SM5
+TargetedRHIs=SF_VULKAN_SM6
```

Notes:
- Shipping **only** SM6 means no SM5 shaders in the package, so the game cannot fall back to DX11 on an old GPU; that is intended for this project (we require DX12/SM6 hardware).
- I found **no official deprecation of DX11/SM5 in 5.7 or 5.8** [docs search negative]; it still exists but gets none of the features above.
- Vulkan on Linux: Epic's Linux requirements page [docs] recommends Ubuntu 22.04, quad-core CPU, 32 GB RAM, "GeForce 2080 with 8 GB+ VRAM"; drivers **NVIDIA 570+**, **AMD RADV 24.2.8+ (25.0+ recommended)**; "Lumen Hardware Ray Tracing now requires SM6" applies there too (Vulkan ray tracing). The cvar `r.Vulkan.RayTracing=True` appears in shipped Linux project inis [ini] but I could not confirm its documentation [unverified].

---

## 3. Lumen GI + reflections

Status: production (since 5.0/5.1); **Lumen Lite = Beta in 5.8** [docs].

### 3.1 Project settings → ini keys (Rendering section) [src: RendererSettings.h 5.7; values from EngineTypes.h]

| Project setting (display name) | ini key (`[/Script/Engine.RendererSettings]`) | Values |
|---|---|---|
| Dynamic Global Illumination Method | `r.DynamicGlobalIlluminationMethod` | 0 None, **1 Lumen**, 2 Screen Space (Beta), 3 Plugin |
| Reflection Method | `r.ReflectionMethod` | 0 None, **1 Lumen**, 2 Screen Space |
| Use Hardware Ray Tracing when available | `r.Lumen.HardwareRayTracing` | True/False |
| Ray Lighting Mode | `r.Lumen.HardwareRayTracing.LightingMode` | **0 Surface Cache**, **2 Hit Lighting for Reflections**, **1 Hit Lighting** (GI + reflections, most expensive). Note the non-sequential numbering: enum `ELumenRayLightingMode { SurfaceCache=0, HitLightingForReflections=2, HitLighting=1 }` [src]. The cvar help text: "0 - Use Lumen Surface Cache for ray hit lighting… best GI and reflection performance" [src]. |
| Software Ray Tracing Mode | `r.Lumen.TraceMeshSDFs` | 0 Global Tracing, **1 Detail Tracing** |
| High Quality Translucency Reflections | `r.Lumen.TranslucencyReflections.FrontLayer.EnableForProject` | True/False |
| Ray Traced Translucent Refractions | `r.Lumen.Reflections.HardwareRayTracing.Translucent.Refraction.EnableForProject` | True/False |
| Screen Tracing Source | `r.Lumen.ScreenTracingSource` | 0 Scene Color, 1 Anti-aliased Scene Color with Translucency |
| Generate Mesh Distance Fields (Software Ray Tracing group) | `r.GenerateMeshDistanceFields` | True (required for SWRT fallback and DFAO) |
| Distance field voxel density | `r.DistanceFields.DefaultVoxelDensity` | float (0.2 default) |
| Support Hardware Ray Tracing (Hardware Ray Tracing group) | `r.RayTracing` | True |
| Generate Ray Tracing Proxies (5.7+) | `r.RayTracing.RayTracingProxies.ProjectEnabled` | True/False |
| Texture LOD (ray tracing) | `r.RayTracing.UseTextureLod` | True/False |
| Support Compute Skin Cache (required by HWRT) | `r.SkinCache.CompileShaders` | True |

[docs] "Lumen uses hardware ray tracing when **Use Hardware Ray Tracing when available** is checked and when **Ray Lighting Mode** is set to Hit Lighting for Reflections"; "By default, Lumen uses Surface Cache for best performance, but can be set to Hit Lighting for Reflections for higher quality." Enabling Support Hardware Ray Tracing prompts for Support Compute Skin Cache. HWRT "adds significant scene update cost in scenes with more than 100,000 instances" and "requires rebuilding the TLAS every frame" (performance guide).

### 3.2 SWRT vs HWRT for this project
- **HWRT (recommended on PC)**: traces real triangles (ray-tracing proxies / Nanite fallback meshes), better interior accuracy, supports Hit Lighting; needs DX12 SM6 + DXR GPU. Epic's performance guide: "recommended as a default option on consoles for both 30 fps and 60 fps".
- **SWRT**: distance fields (Detail Tracing per-mesh SDF or Global SDF); works on SM5 and Macs M1+; lower quality on thin geometry (shelves, railings) and more leaking indoors.
- Hit Lighting is additionally gated per scalability level by `r.Lumen.HardwareRayTracing.HitLighting.Allowed` (**0 at Low/Medium/High, 1 at Epic/Cinematic** in 5.8 defaults) [src 5.8 scalability]. So Hit Lighting only takes effect at **Epic+ GI quality** unless you override that cvar in your own `DefaultScalability.ini`.

### 3.3 Quality knobs
Per-Post-Process-Volume (Global Illumination / Reflections categories) [src Scene.h]: `LumenSceneLightingQuality`, `LumenSceneDetail`, `LumenSceneViewDistance`, `LumenSceneLightingUpdateSpeed`, `LumenFinalGatherQuality`, `LumenFinalGatherLightingUpdateSpeed`, `LumenMaxTraceDistance`, `LumenReflectionQuality`, `LumenRayLightingMode` (override enum: Project Default / Surface Cache / Hit Lighting for Reflections / Hit Lighting), `LumenMaxReflectionBounces`, `LumenMaxRefractionBounces`.

Scalability (UE 5.8 `BaseScalability.ini`, `[GlobalIlluminationQuality@N]`) [src]:

| Level | Key lines |
|---|---|
| 0 Low | Lumen off (`r.Lumen.DiffuseIndirect.Allow=0`), DFAO on |
| 1 Medium (**Lumen Lite**) | `r.Lumen.DiffuseIndirect.Allow=1`, **`r.Lumen.FinalGatherMethod=0`** (Irradiance Field final gather with probe occlusion), surface cache atlas 2048, `r.Lumen.TraceMeshSDFs.Allow=0`, HitLighting.Allowed=0, skeletal meshes excluded from RT scene |
| 2 High (60 fps console target) | `r.Lumen.FinalGatherMethod=1` (Screen Probe Gather), atlas 3584, `ScreenProbeGather.DownsampleFactor=32`, `RadianceCache.ProbeResolution=16`, `TracingOctahedronResolution=8`, HitLighting.Allowed=0 |
| 3 Epic (30 fps console / high-end PC) | atlas 4096, `DownsampleFactor=16`, `RadianceCache.ProbeResolution=32`, `NumProbesToTraceBudget=150`, `TraceMeshSDFs.Allow=1`, **`HitLighting.Allowed=1`**, `r.RayTracing.Scene.BuildMode=1` |
| Cine | as Epic but `DownsampleFactor=8`, `TracingOctahedronResolution=16`, `NumProbesToTraceBudget=350`, `FullResolutionJitterWidth=.5`, translucency volume probes 16/350 |

`[ReflectionQuality@N]`: Medium = SSR only (`r.Lumen.Reflections.Allow=0`); High = Lumen reflections at `DownsampleFactor=2`; Epic = `DownsampleFactor=1`, `ScreenSpaceReconstruction.NumSamples=5`, front-layer translucency reflections **allowed** (`FrontLayer.Allow=1`, `Enable=0` → enable via PPV/`EnableForProject`); Cine = `SSR.Quality=4`, `FrontLayer.Enable=1`.

### 3.4 Lumen Lite (5.8, Beta) [docs]/[src]
"A new medium-quality setting for Global Illumination using Irradiance Fields with Probe Occlusion supported by Lumen", automatic probe placement, "about 2× faster than Lumen High" (60 fps on PS5 / Switch 2 / medium PCs). It is **selected automatically by `sg.GlobalIlluminationQuality 1` + `sg.ReflectionQuality 1`**, i.e. `r.Lumen.FinalGatherMethod=0`. No rays for reflections at that level (SSR on smooth, radiance-probe mips on rough). For this project it is the **Medium** preset, not the showcase path.

### 3.5 Lumen Performance guide facts [docs]
Targets: "30 and 60 fps on consoles with 8 ms and 4 ms frame budgets at 1080p"; Epic level ≈ 30 fps console, High ≈ 60 fps; Lumen runs at internal 1080p and is upsampled with TSR for 4K. Optional `r.Lumen.ScreenProbeGather.IntegrateDownsampleFactor 2` (not in default presets; a 5.8 community note says Epic removed it from High as "too noisy" [2nd]).

---

## 4. Nanite

| Feature | 5.8 status | Enable | Verification |
|---|---|---|---|
| Nanite static meshes | Production | Project setting "Nanite" → `r.Nanite.ProjectEnabled=True`; per asset "Enable Nanite Support" | [src]/[ini] |
| Nanite Tessellation / Displacement | Introduced Experimental (5.3). **No official status change found for 5.6–5.8**; multiple open bug reports on landscapes in 5.6–5.8. Treat as Experimental. | `r.Nanite.AllowTessellation=1` + `r.Nanite.Tessellation=1` in `[/Script/Engine.RendererSettings]`; displacement in material (Displacement output + Nanite "Enable Tessellation" per mesh) | [ini] keys; status [unverified] |
| Nanite Skeletal Meshes ("Nanite Skinning") | **Experimental** (Epic staff reply, Oct 2026: 5.8 adds experimental Nanite Translucency; morph targets, grooms, cloth, blend shapes still unsupported). Skeletal Mesh Editor → "Enable Nanite Support". | [2nd] Epic staff forum reply; [docs] editor checkbox |
| Nanite Foliage (assemblies + voxels + skinning) | **Experimental** (introduced 5.7; project setting "Nanite Foliage (Experimental)" → `r.Nanite.Foliage=1`; 5.8 adds the experimental Procedural Vegetation Editor). | [src 5.7 header]/[docs] |
| Platforms | DX12 SM6 / Vulkan SM6 / Metal SM6 (Apple M2+, Beta). | [docs] |

Note: Rocketbox NPC skeletal meshes should stay **non-Nanite** (regular skeletal + skin cache). Use Nanite for all static architecture, furniture, books, exhibits.

---

## 5. Virtual Shadow Maps (VSM)

Status: Production-ready since 5.3 [2nd]. Project setting **Shadow Map Method = Virtual Shadow Maps** → `r.Shadow.Virtual.Enable=1` (enum `EShadowMapMethod: ShadowMaps=0, VirtualShadowMaps=1`) [src]. Requires SM6; designed for Nanite geometry (non-Nanite meshes also work but cost more; moving lights invalidate cached pages).

5.8 scalability defaults `[ShadowQuality@N]` [src]:

| cvar | Low | Med | High | Epic | Cine |
|---|---|---|---|---|---|
| `r.Shadow.Virtual.MaxPhysicalPages` | 512 | 512 | 2048 | 4096 | 8192 |
| `r.Shadow.Virtual.ResolutionLodBiasDirectional` | 0 | 0 | 0 | -1.5 | -1.5 |
| `r.Shadow.Virtual.ResolutionLodBiasDirectionalMoving` | 0 | 0 | 0 | -1.5 | -1.5 |
| `r.Shadow.Virtual.ResolutionLodBiasLocal` | 1.0 | 1.0 | 0 | 0 | 0 |
| `r.Shadow.Virtual.ResolutionLodBiasLocalMoving` | 2.0 | 2.0 | 1.0 | 1.0 | 0 |
| `r.Shadow.Virtual.SMRT.RayCountDirectional` / `SamplesPerRayDirectional` | 0/2 | 4/2 | 8/4 | 8/4 | 16/8 |
| `r.Shadow.Virtual.SMRT.RayCountLocal` / `SamplesPerRayLocal` | 0/2 | 4/2 | 4/4 | 8/4 | 16/8 |
| `r.Shadow.Virtual.MarkCoarsePagesLocal` | 2 | 2 | 2 | 1 | 1 |
| `r.VolumetricFog` / `.GridPixelSize` / `.GridSizeZ` / `.HistoryMissSupersampleCount` | 0 | 0 | 1/16/64/4 | 1/8/128/4 | 1/4/128/16 |
| `r.Shadow.MaxResolution` / `MaxCSMResolution` | – | – | – | 2048 | 4096 |

Page-pool overflow shows as a log warning; for a campus-sized map keep the Epic value (4096) or raise to 8192 on 12 GB+ GPUs. Negative directional bias = sharper sun shadows.

---

## 6. MegaLights

Status: Experimental 5.5 → **Beta 5.7** (added directional lights, Niagara lights, translucency, hair) → **Production Ready 5.8** ("We greatly reduced noise… improving overall performance to achieve 60 fps"; adds transmission/SSS support and a light-finder debug tool) [docs].

- Enable: Project Settings → Rendering → **Direct Lighting → MegaLights** → `r.MegaLights.EnableForProject=True` [src]. Enabling prompts for **Support Hardware Ray Tracing** ("recommended setting for MegaLights") [docs]. The 5.7-era tooltip: "When MegaLights is enabled, other direct lighting algorithms like Deferred Shading will no longer be used, and other shadowing methods like Ray Traced Shadows, Distance Field Shadows and Shadow Maps will no longer be used. MegaLights requires Hardware Ray Tracing" [src] (newer builds fall back to software/Lumen tracing data when HWRT is unavailable [2nd]).
- Per light: light component property **Allow MegaLights**; **Shadow Method = Ray Tracing (default) or Virtual Shadow Maps** (VSM shadows come from full Nanite geometry but only approximate area shadows, extra per-light cost) [docs].
- Per Post Process Volume: `bMegaLights` override [2nd].
- Scalability/device gate: **`r.MegaLights.Allowed`** (source: `TEXT("r.MegaLights.Allowed")`, "Whether the MegaLights feature is allowed by scalability and device profiles") [src]. The docs page prints it as `r.MegaLights.Allow 0`; the source spelling `Allowed` is authoritative.
- Other verified cvars: `r.MegaLights.HardwareRayTracing` [src], `r.MegaLights.HardwareRayTracing.Bias` / `.NormalBias` [src], `r.MegaLights.DirectionalLights` ("Whether to support directional lights", default 0 in 5.5-era builds) [src], `r.MegaLights.DistantScreenTraces.Length` [docs], `r.MegaLights.Volume` [2nd].
- 5.8 scalability defaults (in `[ShadowQuality@N]`) [src]: `r.MegaLights.NumSamplesPerPixel` 2/2/4/4/4; `r.MegaLights.DownsampleMode` 2/2/2/2/**0** (Cine = full res); `r.MegaLights.ScreenTraces.Quality` 0/0/1/1/1; `FrontLayerTranslucency.Allow` 0/0/1/1/1 (`SpecularOnly=1`, `SoftShadows=0` except Cine `0/1`, `TexturedRectLights` Cine only); `Spatial.UseHistorySpatialVariance` 0/0/1/1/1; `Volume.GridPixelSize/GridSizeZ` 16/64 → 8/128 at Epic+.
- Why it matters here: museum galleries with dozens of shadowed spot/rect lights per room are exactly the case; MegaLights gives one consistent cost regardless of light count.

---

## 7. Temporal Super Resolution (TSR)

Project setting **Anti-Aliasing Method** → `r.AntiAliasingMethod=4` (enum `EAntiAliasingMethod`: 0 None, 1 FXAA, 2 TAA, 3 MSAA, **4 TSR**) [src enum + [ini]]. Temporal Upsampling → `r.TemporalAA.Upsampling=True`. Screen percentage: `r.ScreenPercentage` (runtime) / `r.ScreenPercentage.Default` + `r.ScreenPercentage.Default.Desktop.Mode` (project) [src]; `sg.ResolutionQuality` presets in 5.8: Performance 50, Balanced 58.328, Quality 66.662, Native 100 [src]. TSR shaders handle 25%–200% [docs]. TSR runs on SM5 hardware too [docs].

5.8 `[AntiAliasingQuality@N]` [src]:

| cvar | Low | Med | High | Epic | Cine |
|---|---|---|---|---|---|
| `r.TSR.History.ScreenPercentage` | 100 | 100 | 100 | **200** | 200 |
| `r.TSR.History.UpdateQuality` | 0 | 1 | 2 | 3 | 3 |
| `r.TSR.History.R11G11B10` | 1 | 1 | 1 | 1 | **0** (fp16 history) |
| `r.TSR.ShadingRejection.Flickering` | 0 | 0 | 1 | 1 | 1 |
| `r.TSR.RejectionAntiAliasingQuality` | 0 | 1 | 1 | 2 | 2 |
| `r.TSR.ReprojectionField` | 0 | 0 | 1 | 1 | 1 |
| `r.TSR.Resurrection` | 0 | 1 | 1 | 1 | 1 |

`r.TSR.AsyncCompute=1` moves TSR to async compute [docs]. For the photoreal target: Epic AA + `r.ScreenPercentage 67–100`.

---

## 8. Substrate materials

Status: Experimental 5.2–5.6 → **Production-Ready in 5.7**, "enabled by default for any newly created project"; upgraded projects keep legacy materials unless opted in (Project Settings → Rendering → Substrate, restart) [docs]. 5.8 adds experimental Substrate Toon Shading [docs].

Keys [src]: `r.Substrate=1` ("Substrate materials"); `r.Substrate.ProjectGBufferFormat` = **0 Blendable GBuffer** (default for new projects, "favours speed over fidelity, broad compatibility") or **1 Adaptive GBuffer** ("per-pixel topology and layered closures on modern hardware"); `r.Substrate.ProjectClosuresPerPixel`; `r.Substrate.ProjectClosuresPerPixelOverride`; `r.Substrate.OpaqueMaterialRoughRefraction` (Experimental); `r.Refraction.Blur` (translucent rough refraction); `r.Substrate.EnableLayerSupport` (Experimental material layers). Caveats [docs]: converted materials are incompatible with non-Substrate projects; Substrate materials render black if Substrate is disabled; the Path Tracer did not support Substrate in 5.2 (verify in 5.8 before relying on PT stills with Substrate). For the campus (wood, brass, leather, glass, wax figures with SSS): use Substrate with **Adaptive GBuffer (1)** on the PC build; keep Blendable (0) if a Mac build matters.

---

## 9. Path Tracer (reference stills)

Requirements [docs]: "The Path Tracer requires Hardware Ray Tracing to be enabled for the project" (`r.RayTracing=True`), Project Setting **Path Tracing** → `r.PathTracing=True` [src], Default RHI = DirectX 12, NVIDIA RTX or DXR-capable GTX (Twinmotion's page also lists AMD RX 6000+), Windows 10 1809+. **5.8: Path Tracing now supported on Mac** (Metal Ray Shaders; "please use macOS ≥ 26.4 due to driver bug") [docs]. Maturity label: none printed on the docs page [unverified]; it has been the offline reference renderer since 4.27 and is the MRG "Path Traced Renderer" node. Per-PPV settings live under **Path Tracing** (samples per pixel, max bounces, denoiser, etc.) and `r.ScreenPercentage.Default.PathTracer.Mode` [src]. Known limits: no Lumen features; verify Substrate/Nanite displacement/volumetric fog support per 5.8 docs.

---

## 10. Post process: Local Exposure, Auto Exposure, defaults

### 10.1 Local Exposure (PPV → Lens → Local Exposure) [src Scene.h]
Properties (display names): **Method** (`ELocalExposureMethod`: Bilateral, Fusion (Experimental)), **Highlight Contrast**, **Shadow Contrast**, Highlight Contrast Curve, Shadow Contrast Curve, Highlight Threshold, Shadow Threshold, **Detail Strength**, **Blurred Luminance Blend**, Blurred Luminance Kernel Size Percent, Highlight Threshold Strength, Shadow Threshold Strength, **Middle Grey Bias**. Project-wide defaults: `r.DefaultFeature.LocalExposure.HighlightContrastScale` and `r.DefaultFeature.LocalExposure.ShadowContrastScale` (project templates ship **0.8/0.8**; 1.0 = off) [src]/[ini]. Epic describes Local Exposure as "edge-aware… for high-contrast scenes such as interiors with bright outdoors visible through windows and doors" [docs] — exactly the library/gallery case. Debug: Show → Visualize → Local Exposure.

### 10.2 Auto Exposure (PPV → Lens → Exposure) [src Scene.h]
**Metering Mode** (`AutoExposureMethod`: Auto Exposure Histogram / Auto Exposure Basic / Manual), **Exposure Compensation** (`AutoExposureBias`) + curve, **Apply Physical Camera Exposure**, Low Percent / High Percent, **Min Brightness / Max Brightness** (`AutoExposureMinBrightness/MaxBrightness`; shown as **Min EV100 / Max EV100** when the extended luminance range is on), Speed Up / Speed Down, Histogram Log Min / Max.
Project defaults: `r.DefaultFeature.AutoExposure` (on/off), `r.DefaultFeature.AutoExposure.Method` (0 Histogram, 1 Basic, 2 Manual — enum order `AEM_Histogram, AEM_Basic, AEM_Manual`), `r.DefaultFeature.AutoExposure.Bias`, `r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange` ("Extend default luminance range in Auto Exposure settings") [src]. Pre-exposure: `r.UsePreExposure` [ini].
Interior guidance [docs]+[2nd]: enable the extended range so Min/Max are in EV100; typical campus ranges: interiors **EV100 ≈ 6–10**, exteriors **≈ 12–15**; set Min EV100 ≈ 4–6 and Max EV100 ≈ 15–16 so windows do not blow out; Speed Up 3 / Speed Down 1; Exposure Compensation ~0 to +1 for dim reading rooms; for the Path Tracer stills use **Manual** with physical camera values. (Specific numbers are recommendations, not Epic defaults.)

### 10.3 "Default Settings" project keys [src]
`r.DefaultFeature.Bloom`, `r.DefaultFeature.AmbientOcclusion`, `r.DefaultFeature.AmbientOcclusionStaticFraction`, `r.DefaultFeature.MotionBlur`, `r.DefaultFeature.LensFlare`, `r.DefaultFeature.LightUnits` (`ELightUnits`: 0 Unitless, 1 Candelas, 2 Lumens, 3 EV, 4 Nits), `r.MSAACount`, `r.PostProcessing.PropagateAlpha`, `r.CustomDepth`.

---

## 11. Virtual Texturing, volumetrics, sky, cinematics

### 11.1 Virtual Texturing (Project Settings → Rendering → Virtual Textures) [src]
`r.VirtualTextures` ("Enable virtual texture support"), `r.VirtualTexturedLightmaps` ("Enable virtual texture lightmaps", needs lighting rebuild), `r.VT.TileSize` ("Tile size", power of two, restart), `r.VT.TileBorderSize`, `r.VT.AnisotropicFiltering`, `r.VT.EnableAutoImport` ("Enable virtual texture on texture import"). Runtime VT family toggles: `r.vt.rvt.EnableBaseColor`, `.EnableBaseColorRoughness`, `.EnableBaseColorSpecular`, `.EnableMask4`, `.EnableWorldHeight`, `.EnableDisplacement`, `.HighQualityPerPixelHeight`. Mesh-paint VT: `r.MeshPaintVirtualTexture.Support` etc. Scalability: `r.VT.MaxAnisotropy` 8 at Epic/Cine [src]. Mobile key `r.Mobile.VirtualTextures` is irrelevant here. Use SVT for the large 4K/8K PBR sets from `assets/lib` (import with auto-VT on).

### 11.2 Heterogeneous Volumes / Volumetric Fog
Project setting "**Heterogeneous Volumes (Experimental)**" → `r.HeterogeneousVolumes=1`; "Shadow Casting" `r.HeterogeneousVolumes.Shadows`; "Composite with Translucency" `r.Translucency.HeterogeneousVolumes` [src 5.7 header; 5.8 label change not found]. Renders volume-domain materials sampling **Sparse Volume Textures** (VDB import), real-time and Path Tracer [docs]. 5.8 scalability (`[EffectsQuality@N]`) [src]: `r.HeterogeneousVolumes.Allowed`, `.DownsampleFactor` (8→2→1), `.MaxStepCount` (128→256→1024), `.Shadows.Resolution` (128→512→1024), `.Shadows.Precision`, `.UseExistenceMask`, Cine adds `.ApplyFogInscattering=1`, `.Shadows.Type=0`, `.Shadows.MaxSampleCount=16`, `r.Translucency.HeterogeneousVolumes.Type=0`.
Volumetric fog (Exponential Height Fog actor → Volumetric Fog) cvars: `r.VolumetricFog`, `r.VolumetricFog.GridPixelSize`, `r.VolumetricFog.GridSizeZ`, `r.VolumetricFog.HistoryMissSupersampleCount` (values in §5 table) [src]; light-function atlas for fog: `r.VolumetricFog.LightFunction` [src]. Local Fog Volumes: `r.SupportLocalFogVolumes` [src]. Dusty reading-room light shafts = volumetric fog at Epic (`GridPixelSize 8`, `GridSizeZ 128`) + MegaLights volume lighting (`r.MegaLights.Volume.*`).

### 11.3 Sky Atmosphere + Volumetric Clouds
Project keys [src]: `r.SupportSkyAtmosphere` ("Support Sky Atmosphere" — reserves samplers for aerial perspective on translucency), `r.SupportSkyAtmosphereAffectsHeightFog`, `r.SupportExpFogMatchesVolumetricFog`, `r.SupportCloudShadowOnForwardLitTranslucent`, `r.Water.SingleLayerWater.SupportCloudShadow`. Recommended actor stack [docs]: Directional Light (**Atmosphere Sun Light** on), Sky Atmosphere, Sky Light (**Real Time Capture**), Volumetric Cloud, Exponential Height Fog. Scalability `[EffectsQuality@N]` [src]: `r.SkyAtmosphere.FastSkyLUT` (1 at ≤Epic, 0 at Cine), `r.SkyAtmosphere.SampleCountMin/Max` (4/128 Epic, 8/256 Cine), `r.SkyAtmosphere.AerialPerspectiveLUT.*`, `r.SkyAtmosphere.TransmittanceLUT.SampleCount` (10 → 30 Cine), `r.SkyAtmosphere.MultiScatteringLUT.SampleCount` (15 → 20). Cloud cvars verified in source [src]: `r.VolumetricCloud.ViewRaySampleMaxCount` (default 768), `r.VolumetricCloud.ReflectionRaySampleMaxCount` (default 80), `r.VolumetricCloud.ShadowMap`, `r.VolumetricCloud.SkyAO`, `r.VolumetricCloud.DistanceToSampleMaxCount`, `r.VolumetricCloud.Shadow.ReflectionRaySampleMaxCount`. Clouds matter mostly for the recess yard; indoors keep them but let Lumen's sky light real-time capture feed GI through windows.

### 11.4 Movie Render Graph (MRG)
**Production-Ready in 5.8** (official State of Unreal list; Digital Production: redesigned Queue window exposing graph settings, nDisplay support, per-shot light isolation) [docs]/[2nd]. Plugin: Movie Render Pipeline (MRG is part of it; previously shown as "Movie Render Graph (Beta)" in the Queue's Settings column). Legacy MRQ presets remain usable interchangeably [docs]. Use the **Path Traced Renderer** node for stills and the **Deferred Renderer** node (+ Console Variables node for `r.ScreenPercentage 200`, TSR Cine, `sg.*Quality 4`) for trailers. Python: `unreal.MoviePipelineQueueSubsystem` / `MoviePipelineQueue` remain; MRG-specific class names (e.g. graph config) are **not verified here** — have Cowork read `unreal.MovieGraph*` from the editor's Python stubs before scripting.

---

## 12. Mac vs Windows (and Linux) — what the user's machine can do

Epic hardware/software specs page [docs] (current revision):

| | Windows | macOS | Linux |
|---|---|---|---|
| OS | **Windows 11** recommended (Win10 64-bit in older revisions) | Latest macOS (page lists Sonoma 14.5 minimum; 5.8 Mac Path Tracing wants **macOS 26.4+**); **Intel Macs: no rendering support in 5.8** (cook/headless only) | Ubuntu 22.04 recommended |
| CPU | Quad-core Intel/AMD, 2.5 GHz+ | Apple Silicon **M3 recommended**, M1/M2 minimum "depending on rendering features" | Quad-core |
| RAM | **32 GB** | **32 GB+** rec., 16 GB min | 32 GB |
| GPU | **DirectX 12 compatible, 8 GB+ VRAM**, latest drivers; HWRT needs NVIDIA RTX / DXR GTX (Epic) or AMD RX 6000+ (Twinmotion page) | Integrated Apple GPU, Metal SM6 (macOS 15+ for SM6 per Epic's Metal parity blog) | "GeForce 2080, 8 GB+"; NVIDIA 570+, RADV 24.2.8+ (25+ rec.) |
| IDE | Visual Studio 2022 (VS Code/Rider supported) | Xcode 26.0 min / 26.1.1 rec. (page says **Xcode 26.4 is not compatible**) | clang toolchain v25 |
| Lumen SWRT | yes | yes (M1+) | yes |
| Lumen HWRT | yes (DXR) | **M2+ Experimental** on the newest page revision (an older revision says "Not currently supported"); 5.8 added Metal Ray Shaders. Expect it to work on M3/M4 but treat as experimental. | yes (Vulkan RT, SM6) |
| MegaLights | yes (production) | **M2+ Experimental** (same caveat) | yes |
| Nanite / VSM | yes | **M2+ Beta** | yes |
| Path Tracer | yes | **yes, new in 5.8** (macOS ≥ 26.4) | yes (Vulkan RT) [2nd] |
| Substrate | yes | yes (prefer Blendable GBuffer) | yes |
| TSR | yes | yes | yes |
| Shader format keys | `PCD3D_SM6` | `SF_METAL_SM6` | `SF_VULKAN_SM6` |

Practical rule for Cowork: on **Windows + RTX/RX 6000+** build the full stack (HWRT Lumen + Hit Lighting for Reflections, MegaLights, Nanite, VSM, Substrate Adaptive, Path Tracer stills). On an **Apple Silicon Mac**: M1 → SWRT Lumen only, no Nanite/VSM; **M2+** → Nanite/VSM (Beta) and try HWRT/MegaLights (Experimental) with a fallback device profile forcing `r.Lumen.HardwareRayTracing=False` and `r.MegaLights.Allowed=0` if artifacts/crashes appear; Path Tracer only on macOS 26.4+. Intel Mac → not viable.

### GPU tier for Lumen HWRT + Nanite + VSM at 1440p/60 (inference, not an Epic spec)
Epic only publishes console budgets (Lumen High = 4 ms @1080p internal, 60 fps; Epic = 8 ms @ 30 fps; TSR upsample). Public PC data points: Hellblade II (Nanite + VSM + SW Lumen) needs **RTX 4070 / RTX 3080 / RX 7800 XT** class for 1440p60 with upscaling (PC Games Hardware); third-party Avowed numbers put an RTX 4070 at ~60 fps 1440p Ultra native and an RTX 5080 at ~95 fps 1440p max + full RT (unverified sites). Derived guidance:

| Target | GPU |
|---|---|
| 1440p60, **High** GI/reflections (Screen Probe Gather, HWRT Surface Cache), VSM High, MegaLights 4 spp, TSR 67% | RTX 4070 / 5070 / RX 7800 XT / RX 9070 (8–12 GB) — minimum spec |
| 1440p60, **Epic** GI/reflections + Hit Lighting for Reflections, VSM Epic, TSR 67–80% | RTX 4070 Ti Super / 5070 Ti / RX 9070 XT (16 GB) — recommended spec |
| 1440p60 near-native (TSR 100%) Epic + Hit Lighting, MegaLights Epic, volumetric fog Epic | RTX 4080 / 5080 (16 GB) |
| Cinematic preset / 4K60 / Path Tracer turnaround | RTX 4090 / 5090 (24–32 GB) |

VRAM: 8 GB is Epic's floor; Nanite streaming pool + VSM 4096 pages + ray-tracing BVH + VT pool make **12–16 GB** the comfortable floor for this content.

---

## 13. Scalability groups (ship Low … Cinematic)

Groups (console vars) [src 5.8 BaseScalability.ini `[ScalabilitySettings]`]: `sg.ResolutionQuality`, `sg.ViewDistanceQuality`, `sg.AntiAliasingQuality`, `sg.ShadowQuality`, `sg.GlobalIlluminationQuality`, `sg.ReflectionQuality`, `sg.PostProcessQuality`, `sg.TextureQuality`, `sg.EffectsQuality`, `sg.FoliageQuality`, `sg.ShadingQuality` (and `sg.LandscapeQuality` exists in the engine's Scalability API but has **no** `[LandscapeQuality@N]` sections in the 5.8 base file I inspected). Levels **0 Low, 1 Medium, 2 High, 3 Epic, 4 Cinematic**; ini sections are `[GroupName@0..3]` and `[GroupName@Cine]`. Resolution presets (5.8): Performance 50 / Balanced 58.328 / Quality 66.662 / Native 100. Auto-detect: `PerfIndexThresholds_*` lines drive the benchmark (`UGameUserSettings::RunHardwareBenchmark()` → `ApplyHardwareBenchmarkResults()`); set all groups with `UGameUserSettings::SetOverallScalabilityLevel(n)` then `ApplySettings()`, or per group with `sg.GlobalIlluminationQuality 3` etc. Project overrides go in **`Config/DefaultScalability.ini`** (same section names; they layer over `Engine/Config/BaseScalability.ini`); per-platform overrides in `DefaultDeviceProfiles.ini` (`[Windows DeviceProfile]` `+CVars=`).

What each level means for this project (5.8 defaults; see §3–§7 for the numbers):

| Preset | GI | Reflections | Shadows | AA | Notes |
|---|---|---|---|---|---|
| Low (0) | Lumen off, DFAO | SSR | VSM 512 pages, no SMRT rays, no volumetric fog | TSR min | SM6 still required by our package |
| Medium (1) | **Lumen Lite** (irradiance field) | SSR | VSM 512 pages | TSR | Switch-2/handheld-PC class |
| High (2) | Lumen Screen Probe Gather, surface cache | Lumen refl. half-res | VSM 2048, fog 16/64 | TSR | 60 fps console class |
| Epic (3) | + hit lighting allowed, SDF detail tracing | Lumen refl. full-res, front-layer translucency allowed | VSM 4096, bias -1.5, fog 8/128 | TSR history 200% | default for the PC showcase |
| Cinematic (4) | probes ×2, octahedron 16, budget 350 | SSR Q4, front-layer on | VSM 8192, SMRT 16/8, fog 4/128/16, MegaLights full-res | fp16 history | MRG/stills only |

Suggested project `DefaultScalability.ini` deltas (verified keys): keep Epic as default; in `[GlobalIlluminationQuality@2]` optionally keep `r.Lumen.HardwareRayTracing.HitLighting.Allowed=0` (as shipped); in `[GlobalIlluminationQuality@3]` nothing to change; in `[ShadowQuality@3]` consider `r.Shadow.Virtual.MaxPhysicalPages=8192` for ≥12 GB cards; in `[GlobalIlluminationQuality@Cine]` add `r.Lumen.HardwareRayTracing.LightingMode=1` (full Hit Lighting) for MRG renders only.

---

## 14. Ready-to-paste `DefaultEngine.ini` renderer block (verified keys only)

```ini
[/Script/Engine.RendererSettings]
; ---- GI / reflections (Lumen) ----
r.DynamicGlobalIlluminationMethod=1                 ; Dynamic Global Illumination Method = Lumen (0 None,1 Lumen,2 SSGI,3 Plugin)
r.ReflectionMethod=1                                ; Reflection Method = Lumen (0 None,1 Lumen,2 SSR)
r.Lumen.HardwareRayTracing=True                     ; Use Hardware Ray Tracing when available (falls back to SWRT on non-RT GPUs)
r.Lumen.HardwareRayTracing.LightingMode=2           ; Ray Lighting Mode: 0 Surface Cache, 2 Hit Lighting for Reflections, 1 Hit Lighting (GI+refl, very costly)
r.Lumen.TraceMeshSDFs=1                             ; Software Ray Tracing Mode = Detail Tracing (per-mesh SDF) when SWRT is used
r.Lumen.TranslucencyReflections.FrontLayer.EnableForProject=True   ; High Quality Translucency Reflections (glass cases, windows)
r.Lumen.Reflections.HardwareRayTracing.Translucent.Refraction.EnableForProject=True ; Ray Traced Translucent Refractions (HWRT only)
r.Lumen.ScreenTracingSource=1                       ; Screen Tracing Source = anti-aliased scene color with translucency (less emissive noise)
r.GenerateMeshDistanceFields=True                   ; Generate Mesh Distance Fields (required for SWRT fallback + DFAO)
r.DistanceFields.DefaultVoxelDensity=0.2            ; Distance field voxel density (engine default; raise for small props)
; ---- Hardware ray tracing / path tracer ----
r.RayTracing=True                                   ; Support Hardware Ray Tracing (DX12 SM6 / Vulkan SM6 / Metal SM6)
r.RayTracing.RayTracingProxies.ProjectEnabled=True  ; Generate Ray Tracing Proxies (5.7+; simplified RT geometry for Nanite meshes)
r.RayTracing.Shadows=False                          ; legacy Ray Traced Shadows off (VSM + MegaLights handle shadows)
r.SkinCache.CompileShaders=True                     ; Support Compute Skin Cache (required by HWRT for skinned NPCs)
r.PathTracing=True                                  ; Path Tracing (reference stills; needs r.RayTracing)
; ---- Direct lighting / shadows ----
r.MegaLights.EnableForProject=True                  ; MegaLights (production in 5.8; many shadowed area lights)
r.Shadow.Virtual.Enable=1                           ; Shadow Map Method = Virtual Shadow Maps (0 Shadow Maps, 1 VSM)
; ---- Geometry ----
r.Nanite.ProjectEnabled=True                        ; Nanite
r.Nanite.AllowTessellation=1                        ; allow Nanite tessellation (displacement; experimental, optional)
r.Nanite.Tessellation=1                             ; enable Nanite tessellation at runtime (optional; pair with the line above)
; ---- Materials ----
r.Substrate=1                                       ; Substrate materials (production since 5.7; new projects default on)
r.Substrate.ProjectGBufferFormat=1                  ; Substrate GBuffer Format: 0 Blendable (default, cheaper), 1 Adaptive (layers/topology, PC high-end)
r.Material.RoughDiffuse=True                        ; Enable Rough Diffuse Material (energy-correct rough dielectrics)
r.Material.EnergyConservation=True                  ; Enable Energy Conservation on Material
; ---- Anti-aliasing / upscaling ----
r.AntiAliasingMethod=4                              ; Anti-Aliasing Method = TSR (0 None,1 FXAA,2 TAA,3 MSAA,4 TSR)
r.TemporalAA.Upsampling=True                        ; Temporal Upsampling (TSR upscales from r.ScreenPercentage)
; ---- Exposure / post defaults ----
r.DefaultFeature.AutoExposure=True                  ; Auto Exposure on by default
r.DefaultFeature.AutoExposure.Method=0              ; Auto Exposure method: 0 Histogram, 1 Basic, 2 Manual
r.DefaultFeature.AutoExposure.Bias=0.0              ; Auto Exposure Bias (exposure compensation, EV)
r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True ; Min/Max Brightness become Min/Max EV100 (physical light units)
r.DefaultFeature.LocalExposure.HighlightContrastScale=0.8      ; Local Exposure Highlight Contrast (1.0 = off); windows vs interiors
r.DefaultFeature.LocalExposure.ShadowContrastScale=0.8         ; Local Exposure Shadow Contrast (1.0 = off)
r.DefaultFeature.LightUnits=1                       ; Light Units: 0 Unitless, 1 Candelas, 2 Lumens, 3 EV, 4 Nits
r.DefaultFeature.Bloom=True                         ; Bloom
r.DefaultFeature.AmbientOcclusion=True              ; SSAO default (Lumen provides most AO; keep for non-Lumen levels)
r.DefaultFeature.MotionBlur=False                   ; Motion Blur off for a walkable archive (enable per-PPV for cinematics)
r.DefaultFeature.LensFlare=False                    ; Image-based lens flares off
; ---- Virtual texturing ----
r.VirtualTextures=True                              ; Enable virtual texture support (streaming VT for 4K/8K PBR sets)
r.VT.EnableAutoImport=True                          ; Enable virtual texture on texture import
r.VT.TileSize=128                                   ; VT tile size (power of two; restart)
r.VT.TileBorderSize=4                               ; VT tile border size
r.VT.AnisotropicFiltering=True                      ; VT anisotropic filtering
r.VirtualTexturedLightmaps=False                    ; no VT lightmaps (fully dynamic lighting)
; ---- Sky / fog / volumetrics ----
r.SupportSkyAtmosphere=True                         ; Support Sky Atmosphere
r.SupportSkyAtmosphereAffectsHeightFog=True         ; Sky Atmosphere affects height fog
r.SupportLocalFogVolumes=True                       ; Support Local Fog Volumes (per-room haze)
r.HeterogeneousVolumes=1                            ; Heterogeneous Volumes (Experimental) for VDB smoke/dust (optional)
r.HeterogeneousVolumes.Shadows=1                    ; Heterogeneous volume shadow casting (optional)
; ---- Lighting pipeline ----
r.AllowStaticLighting=False                         ; fully dynamic (Lumen); drops static-lighting shader permutations (optional)
r.CustomDepth=3                                     ; Custom Depth-Stencil Pass = Enabled with Stencil (outline/highlight FX)

[/Script/WindowsTargetPlatform.WindowsTargetSettings]
DefaultGraphicsRHI=DefaultGraphicsRHI_DX12          ; Default RHI = DirectX 12
-D3D12TargetedShaderFormats=PCD3D_SM5
+D3D12TargetedShaderFormats=PCD3D_SM6               ; D3D12 SM6 only (Nanite/VSM/HWRT/MegaLights need SM6)
-D3D11TargetedShaderFormats=PCD3D_SM5               ; no DX11 fallback shaders

[/Script/MacTargetPlatform.MacTargetSettings]
-TargetedRHIs=SF_METAL_SM5
+TargetedRHIs=SF_METAL_SM6                          ; Metal SM6 (Apple Silicon M2+ for Nanite/VSM)

[/Script/LinuxTargetPlatform.LinuxTargetSettings]
-TargetedRHIs=SF_VULKAN_SM5
+TargetedRHIs=SF_VULKAN_SM6                         ; Vulkan SM6

[/Script/HardwareTargeting.HardwareTargetingSettings]
TargetedHardwareClass=Desktop
AppliedTargetedHardwareClass=Desktop
DefaultGraphicsPerformance=Maximum
AppliedDefaultGraphicsPerformance=Maximum
```

Notes on the block: every key exists in `RendererSettings.h` (5.7) or in shipped project inis; values marked "optional" can be dropped. `r.CustomDepth=3` value mapping (Enabled with Stencil) is from memory of `ECustomDepthStencil` and not re-verified here. Toggling Substrate, Nanite, HWRT or SM6 requires an editor restart and a full shader recompile. On a Mac build set `r.Substrate.ProjectGBufferFormat=0` and expect `r.MegaLights`/HWRT to be experimental.

---

## 15. Items I could NOT confirm (say so, do not invent)

1. Official Experimental/Beta/Production label for **Nanite Tessellation/Displacement** in 5.6–5.8 (only bug reports found).
2. Whether **Nanite Skeletal Mesh** support changed label in 5.8 (Epic staff says still mostly missing features; a blog claims "beta in 5.7 / production in 5.8" — contradicted, ignore).
3. **Heterogeneous Volumes** label in 5.8 (5.7 header still says "(Experimental)").
4. **Path Tracer** maturity label (docs page has none).
5. Exact **5.8.2** date (late August 2026, ≤ 31 Aug).
6. Whether 5.8's Metal Ray Shaders moved **Lumen HWRT / MegaLights on Mac** beyond "M2+ Experimental"; the requirements page has two conflicting revisions.
7. `r.Vulkan.RayTracing` semantics; `EScreenPercentageMode` numeric values; whether `ExtendDefaultLuminanceRange` now defaults to True (community claim) — set it explicitly.
8. MRG Python class names (`unreal.MovieGraph*`) — read from the editor stubs on the target machine.
9. GPU tier numbers in §12 are inferences from console budgets + third-party game benchmarks, not Epic specs.
10. Volumetric-cloud cvar defaults come from a UE source mirror of unknown minor version (768 / 80).

## 16. Primary sources consulted (search-engine excerpts)
- dev.epicgames.com: Unreal Engine 5.8 Release Notes; 5.7 Release Notes; Hardware and Software Specifications; macOS / Linux Development Requirements; Lumen Global Illumination and Reflections; Lumen Technical Details; Lumen Performance Guide; Hardware Ray Tracing; MegaLights; Nanite Virtualized Geometry; Virtual Shadow Maps; Temporal Super Resolution (+FAQ); Substrate Materials overview; Path Tracer; Ray Tracing and Path Tracing Features; Auto Exposure; Virtual Texturing (settings & properties); Heterogeneous Volumes; Sky Atmosphere component properties; Movie Render Graph / transition guide; Scalability Reference; Supported Features by Rendering Path.
- unrealengine.com: "Unreal Engine 5.8 is now available"; "State of Unreal 2026: top news"; "Bringing Unreal Engine on macOS up to feature parity with Windows".
- forums.unrealengine.com: 5.8.1 / 5.8.2 / 5.8.3 Hotfix Released; "Unreal Engine 5.8 Preview"; "Status of Skinned Meshes (and MetaHuman) and Nanite Support" (Epic staff reply).
- Engine source/config mirrors on GitHub (5.7.0 headers; 5.8 packaged BaseScalability/BaseEngine/BaseDeviceProfiles) — copies saved under `…/scratchpad/ue/research/raw/`.
- Secondary: Tom Looman "UE 5.8 Performance Highlights", Guru3D, Digital Production, Inven Global, GameFromScratch, PC Games Hardware (Hellblade II benchmarks).

---

## Critic notes (2026-10-16, completeness critic; see `../critic.md`)

1. **Verified against the saved sources in `raw/`** (5.7 `RendererSettings.h`/`EngineTypes.h`/`Scene.h`, 5.8 `BaseScalability.ini`/`BaseEngine.ini`): every `[/Script/Engine.RendererSettings]` key in §14 **except** `r.Nanite.AllowTessellation` and `r.Nanite.Tessellation`, which are not project settings in the header (names unverified here, Experimental feature) → **drop both lines from the v1 ini**. Enum numerics confirmed: `ELumenRayLightingMode` SurfaceCache=0 / HitLightingForReflections=2 / HitLighting=1; `ECustomDepthStencil::EnabledWithStencil=3` (so `r.CustomDepth=3` is no longer "from memory"); `EShadowMapMethod` ShadowMaps=0 / VirtualShadowMaps=1; `ESubstrateStorageFormat` Blendable=0 / Adaptive=1; `EAutoExposureMethod` Histogram=0 / Basic=1 / Manual=2; `ELightUnits` Unitless=0 / Candelas=1 / Lumens=2 / EV=3 / Nits=4; `ELumenSoftwareTracingMode` DetailTracing=1 / GlobalTracing=0; `r.AntiAliasingMethod` maps to `AAM_*` (TSR=4 corroborated by shipped inis, the numeric enum body is not in the saved files).
2. `r.MegaLights.Allowed` / `r.MegaLights.Allow`: **neither spelling appears** in the saved 5.8 `BaseScalability.ini` or `BaseDeviceProfiles.ini`; the `[src]` tag in §6 could not be reproduced here. Only `r.MegaLights.EnableForProject` is verified — keep that in the ini and confirm the scalability gate name with the probe job before writing any `DefaultScalability.ini` line for it. `r.MegaLights.DirectionalLights` / `.HardwareRayTracing` likewise unverified here.
3. `r.Lumen.TraceMeshSDFs=1`: the project setting exists (5.7 header, "Software Ray Tracing Mode") and 5.8 scalability still toggles `r.Lumen.TraceMeshSDFs.Allow` (0 @1, 0 @2, 1 @3, 1 @Cine), but `dl/ue58traps.md` claims detail tracing is deprecated since 5.7. Unresolved from here; HWRT is the primary path, so **omit the line in v1** and set it after the probe.
4. §12 Mac row: `delivery.md` quotes an older Epic page ("Lumen HWRT and MegaLights not currently supported on Mac"); this report's "M2+ Experimental" is the newer revision. Agreed plan: Experimental at best, **never a dependency**; ship a Mac device-profile fallback (`r.Lumen.HardwareRayTracing=False`, MegaLights off). Also note: `[Mac DeviceProfile]` in 5.8 `BaseDeviceProfiles.ini` contains no Lumen/MegaLights cvars (no evidence either way).
5. The user's machine is **unknown** (the "M5 Max / macOS 26.5.1" line in `dl/ue58traps.md` §6 describes the third-party skill author's Mac, not the user's).
6. Nothing in §1 (dates 17 Jun / 22 Sep 2026, "last planned UE5 release") could be re-verified: dev.epicgames.com, unrealengine.com and the forums are blocked from this container and the web-search budget was exhausted. The PixelStreaming infrastructure repo's branch list (`UE5.8` current, no `UE5.9`) is the only independent corroboration obtained.
7. Placement note for non-UPROPERTY cvars (if any are ever needed): `[SystemSettings]` exists in 5.8 `BaseEngine.ini` (line 2229); `[/Script/Engine.RendererSettings]` is also applied as a cvar section at startup (long-standing engine behaviour, not re-verified here).
