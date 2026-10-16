# Hand-off: paste one of these into Claude on your computer

Unreal has to be installed and run **on your computer**, so the Claude doing this work must be able to run commands
there. Pick one:

| | Best for | What runs where |
|---|---|---|
| **A. Claude Code (recommended)** | The whole setup, building, fixing errors | Runs commands directly on your computer and asks before each one |
| **B. Cowork** | If you'd rather stay in Cowork | Cowork plans; a local terminal extension (Desktop Commander) runs the commands; computer use (Pro/Max) clicks through installers and the Epic Games Launcher |

Either way you'll do three things yourself: sign in to the Epic Games Launcher, click **Install** on Unreal Engine 5.8
(or let computer use do it while you watch), and approve installers that need admin rights.

---

## A. Claude Code on your computer

1. Install Claude Code if you don't have it: open the Claude desktop app and use the **Code** tab with a local folder, or in a terminal run
   - Windows (PowerShell): `irm https://claude.ai/install.ps1 | iex`
   - Mac: `curl -fsSL https://claude.ai/install.sh | bash`
2. Clone the repo into a short path with no spaces (`C:\dev` or `~/dev`), open that folder in Claude Code, and paste:

```text
You're setting up my Unreal Engine 5.8 port of Walk the Archive on this computer.
Repo: https://github.com/bIipn/xr-campus-assets, branch unreal5-port (clone it to C:\dev\xr-campus-assets on
Windows or ~/dev/xr-campus-assets on a Mac if it isn't here yet, then check out unreal5-port).

Read unreal/CLAUDE.md and unreal/COWORK.md first, then follow COWORK.md from Step 0 through Step 5, in order.
After each step tell me in one or two sentences what happened and what's next.
- Ask me before installing anything or doing anything that needs admin rights.
- I'll sign in to the Epic Games Launcher myself; pause and tell me when it's time.
- If the C++ build or the setup script fails, fix it with the smallest change that follows unreal/contract/CONTRACT.md,
  commit the fix, and try again. If the same error survives two fixes, stop and explain it to me in plain words.
- When the campus runs, show me screenshots of the lobby, the Reading Room and the Recess Yard.
Then push your fixes to the unreal5-port branch.
```

---

## B. Cowork

1. In the Claude desktop app: **Settings → Extensions**, install **Desktop Commander** (it gives Cowork a terminal on
   this computer). On Pro/Max you can also turn on **Settings → General → Enable computer use** for the installer and Launcher steps.
2. Start a Cowork task, connect your `dev` folder, and paste:

```text
Set up my Unreal Engine 5.8 port of Walk the Archive on this computer.

Important: your own shell runs in the cloud, so run every command on THIS computer through the Desktop Commander
tools (start_process / read_process_output). First prove it works: run `git --version` (Windows: `where git`) with
Desktop Commander and show me the output. If you can't reach this computer's terminal, stop and tell me.

Repo: https://github.com/bIipn/xr-campus-assets, branch unreal5-port. Clone it into my connected dev folder if it isn't
there, check out unreal5-port, then read unreal/CLAUDE.md and unreal/COWORK.md and follow COWORK.md Step 0 to Step 5 in
order, reporting after each step. Use computer use only for GUI steps (Epic Games Launcher install of UE 5.8, installer
prompts), and let me type every password myself. Ask before installing anything. If a build or setup step fails twice,
stop and explain it in plain words.
```

**Optional:** upload the Cowork skill `unreal/cowork/walk-the-archive-unreal.zip` (**Customize → Skills → + →
Upload a skill**) so Cowork knows this project's rules in every future task.
