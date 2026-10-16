---
name: walk-the-archive-unreal
description: Set up, build, fix and extend Ev Holt's Walk the Archive campus in Unreal Engine 5.8 (repo bIipn/xr-campus-assets, branch unreal5-port, folder unreal/). Use when asked to install Unreal for this project, build or run the campus, fix its C++ or editor-Python setup, make it photoreal, add MetaHumans, or package it.
---

# Walk the Archive in Unreal Engine 5.8

The project lives in the GitHub repo `bIipn/xr-campus-assets`, branch `unreal5-port`, folder `unreal/`.

## Always
1. Commands must run on the user's own computer: use a local terminal tool (Desktop Commander's `start_process` /
   `read_process_output`, or Claude Code locally). Cowork's built-in shell runs in the cloud and cannot reach Unreal.
2. Read `unreal/CLAUDE.md` (rules) and `unreal/COWORK.md` (the runbook) from the repo before doing anything.
3. The user signs in to Epic, GitHub and installers personally. Never type passwords or 2FA codes.
4. Ask before installing software, using admin rights, or deleting files.
5. Never commit generated Unreal content; only text fixes go back to GitHub (`unreal5-port`).

## Runbook in one breath
Step 0 clone + checkout → Step 1 `Tools/win/preflight.ps1` or `Tools/mac/preflight.sh` → Step 2 `install_prereqs`
then the user installs UE 5.8 from the Epic Games Launcher → Step 3 `build_editor` → Step 4 `setup_project` (all
`WTA_RESULT` lines ok) → Step 5 `play` and the checklist → Step 6 look-dev (`docs/LOOKDEV.md`) → Step 7 MetaHumans
(`docs/HUMANS.md`) → Step 8 `package_game` (`docs/DELIVERY.md`).

## When something fails
Read the first error, fix it with the smallest change that follows `unreal/contract/CONTRACT.md`, keep
`unreal/contract/CPP_API.md` in sync, commit, retry. Stop after two failed fixes of the same error and explain it plainly.

## Style
Short progress updates in plain words. Neat, aesthetic results. If the user asks a yes/no question, put "Yes" or "No" first.
