# How people will get the Unreal version

**Short answer:** Vercel stays the front door, but it can't run Unreal. People either **download** the game (Windows first) or **stream** it live in the browser from a GPU server (Pixel Streaming 2). Full research with sources: `docs/reference/delivery.md`.

| Way | What the visitor needs | Cost to you | Quality | Status |
|---|---|---|---|---|
| **Web campus** (today) | Any browser, phone or headset | Vercel (free tier) | Web quality | Live, keep it |
| **Download** (recommended first) | Windows 10/11 PC with a DirectX 12 GPU (8 GB+ VRAM), about 10–25 GB disk | itch.io: free; optional code signing about $10/month | Full Lumen/Nanite/MetaHuman | M9 |
| **PC VR** | Same build + Quest Link / Air Link / SteamVR | Free | Full (scaled for VR) | M8 |
| **Live stream in the browser** | Any modern browser | About **$0.6–1 per visitor-hour** self-hosted (1 GPU per visitor), or about **$1.5–2.8** with managed hosts (Vagon, Arcware, AWS GameLift Streams), plus a small server for signalling/TURN | Full, at the stream's video quality | Optional (M9) |
| Unreal → WebGL/WebGPU export | — | — | — | **Not possible** for this look (HTML5 export was removed from Unreal; third-party WebGPU efforts can't run Lumen/Nanite) |
| Standalone Quest (no PC) | — | — | — | **Not possible** with Lumen/Nanite; would need a separate mobile art pass |

## Recommended plan

1. **Now:** keep the web campus on Vercel. Add a "UE5 edition" section with a trailer (Movie Render Graph, path-traced stills) and system requirements.
2. **First release:** a Windows build on **itch.io** (`Tools/win/package_game.ps1`), optionally signed so Windows SmartScreen doesn't warn. Later the Epic Games Store and Steam ($100 each, refundable/recoupable).
3. **Live demos without a cloud bill:** run the stream from your own gaming PC for scheduled events, with a tiny VPS for the signalling and TURN servers. The Vercel page embeds Epic's player library (`@epicgames-ps/lib-pixelstreamingfrontend-ue5.8`) behind a "Live demo" button.
4. **If it takes off:** pay-per-minute streaming (Vagon Streams, Arcware, or AWS GameLift Streams embedded in the Vercel page, autoscaling to zero) with a daily visitor cap. Rule of thumb: 500 visitors × 10 minutes at $2/hour ≈ $170.

## Licence

The Unreal licence is free for this project. A 5% royalty applies only to game revenue above US$1M lifetime per product (less through the Epic Games Store). MetaHumans are included. Fab assets follow their own licence (a Personal tier for small creators); Poly Haven assets are CC0.
