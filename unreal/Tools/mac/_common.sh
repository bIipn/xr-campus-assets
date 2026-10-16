#!/usr/bin/env bash
# _common.sh - shared helpers for the Walk the Archive macOS tools. Source it:
#   source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
# Every path is quoted when it reaches a program, so "/Users/Shared/Epic Games" is safe.

set -euo pipefail

# ---- repo layout (Tools/mac -> Tools -> unreal -> repo root) ----
WTA_MAC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$(dirname "$WTA_MAC_DIR")"
UNREAL_DIR="$(dirname "$TOOLS_DIR")"
REPO_ROOT="$(dirname "$UNREAL_DIR")"
COMMON_DIR="$TOOLS_DIR/common"
CACHE_DIR="$TOOLS_DIR/.cache"
PROJECT_DIR="$UNREAL_DIR/WalkTheArchive"
PROJECT_NAME="WalkTheArchive"
UPROJECT="$PROJECT_DIR/WalkTheArchive.uproject"
SETUP_SCRIPT="$PROJECT_DIR/Scripts/setup_project.py"
ENGINE_VERSION="5.8"

step() { printf '\033[36m==> %s\033[0m\n' "$*"; }
note() { printf '    %s\n' "$*"; }
warn() { printf '\033[33mWARNING: %s\033[0m\n' "$*"; }
fail() { printf '\033[31mERROR: %s\033[0m\n' "$*" >&2; }

require_mac() {
    # These scripts drive macOS tools; WTA_ALLOW_NON_MAC=1 only exists for syntax smoke tests.
    if [ "$(uname -s)" != "Darwin" ] && [ "${WTA_ALLOW_NON_MAC:-0}" != "1" ]; then
        fail "this script is for macOS (uname says $(uname -s)); use Tools/win/*.ps1 on Windows."
        exit 1
    fi
}

init_cache_dir() { mkdir -p "$CACHE_DIR"; }

json_escape() {
    # Minimal JSON string escaping for the WTA_RESULT line (backslash, quote, newline).
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    printf '%s' "$s"
}

result_line() {
    # result_line <step> <true|false> [extra JSON members without braces]
    local step="$1" ok="$2" extra="${3:-}"
    if [ -n "$extra" ]; then
        printf 'WTA_RESULT {"step": "%s", "ok": %s, %s}\n' "$step" "$ok" "$extra"
    else
        printf 'WTA_RESULT {"step": "%s", "ok": %s}\n' "$step" "$ok"
    fi
}

have_clt() { xcode-select -p >/dev/null 2>&1; }

system_python() {
    # A usable python3, or nothing. On a Mac without the Command Line Tools, /usr/bin/python3
    # is a stub that pops the CLT installer, so it only counts when the tools are present.
    if command -v python3 >/dev/null 2>&1; then
        if [ "$(uname -s)" != "Darwin" ] || have_clt || [ "$(command -v python3)" != "/usr/bin/python3" ]; then
            if python3 -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
                command -v python3
                return 0
            fi
        fi
    fi
    return 1
}

engine_root_fallback() {
    # Pure-bash copy of find_engine.py's search for Macs without any Python yet.
    local wanted="$ENGINE_VERSION" root dat
    if [ -n "${UE_ROOT:-}" ] && [ -d "$UE_ROOT/Engine/Binaries" ] && [ -d "$UE_ROOT/Engine/Build" ]; then
        printf '%s' "$UE_ROOT"; return 0
    fi
    dat="${WTA_LAUNCHER_DAT:-/Users/Shared/Epic Games/UnrealEngineLauncher/LauncherInstalled.dat}"
    if [ -f "$dat" ]; then
        # Take the InstallLocation that precedes or follows the AppName UE_<wanted> entry.
        root="$(tr -d '\n' < "$dat" | grep -o '{[^{}]*}' | grep "\"AppName\"[[:space:]]*:[[:space:]]*\"UE_$wanted\"" | head -1 \
               | sed -n 's/.*"InstallLocation"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' || true)"
        if [ -n "$root" ] && [ -d "$root/Engine/Binaries" ]; then printf '%s' "$root"; return 0; fi
    fi
    root="/Users/Shared/Epic Games/UE_$wanted"
    if [ -d "$root/Engine/Binaries" ] && [ -d "$root/Engine/Build" ]; then printf '%s' "$root"; return 0; fi
    return 1
}

find_engine() {
    # Sets ENGINE_ROOT, ENGINE_VERSION_FOUND, ENGINE_PYTHON, EDITOR_APP, EDITOR_BIN, EDITOR_CMD,
    # BUILD_SH, RUNUAT_SH, RUNUBT_SH. Returns 1 when no engine is found.
    local py=""
    ENGINE_ROOT=""
    if py="$(system_python)"; then
        ENGINE_ROOT="$("$py" "$COMMON_DIR/find_engine.py" --platform mac --get root 2>/dev/null || true)"
    fi
    if [ -z "$ENGINE_ROOT" ]; then
        ENGINE_ROOT="$(engine_root_fallback || true)"
    fi
    if [ -z "$ENGINE_ROOT" ]; then
        return 1
    fi
    ENGINE_VERSION_FOUND="$(sed -n 's/.*"MajorVersion"[^0-9]*\([0-9]*\).*/\1/p' "$ENGINE_ROOT/Engine/Build/Build.version" 2>/dev/null | head -1 || true)"
    ENGINE_VERSION_FOUND="${ENGINE_VERSION_FOUND:-?}.$(sed -n 's/.*"MinorVersion"[^0-9]*\([0-9]*\).*/\1/p' "$ENGINE_ROOT/Engine/Build/Build.version" 2>/dev/null | head -1 || true)"
    ENGINE_VERSION_FOUND="$ENGINE_VERSION_FOUND.$(sed -n 's/.*"PatchVersion"[^0-9]*\([0-9]*\).*/\1/p' "$ENGINE_ROOT/Engine/Build/Build.version" 2>/dev/null | head -1 || true)"
    ENGINE_PYTHON="$ENGINE_ROOT/Engine/Binaries/ThirdParty/Python3/Mac/bin/python3"
    EDITOR_APP="$ENGINE_ROOT/Engine/Binaries/Mac/UnrealEditor.app"
    EDITOR_BIN="$EDITOR_APP/Contents/MacOS/UnrealEditor"
    # UnrealEditor-Cmd may not ship on Mac; the .app binary takes the same arguments.
    EDITOR_CMD="$ENGINE_ROOT/Engine/Binaries/Mac/UnrealEditor-Cmd"
    [ -x "$EDITOR_CMD" ] || EDITOR_CMD="$EDITOR_BIN"
    BUILD_SH="$ENGINE_ROOT/Engine/Build/BatchFiles/Mac/Build.sh"
    RUNUAT_SH="$ENGINE_ROOT/Engine/Build/BatchFiles/RunUAT.sh"
    RUNUBT_SH="$ENGINE_ROOT/Engine/Build/BatchFiles/RunUBT.sh"
    return 0
}

require_engine() {
    if ! find_engine; then
        fail "Unreal Engine $ENGINE_VERSION was not found. Install it from the Epic Games Launcher (Unreal Engine > Library > + > $ENGINE_VERSION.x > Install) or set UE_ROOT to the engine folder."
        exit 1
    fi
    note "Engine $ENGINE_VERSION_FOUND at $ENGINE_ROOT"
}

best_python() {
    # The engine's bundled Python when present, else the system one.
    if [ -n "${ENGINE_PYTHON:-}" ] && [ -x "$ENGINE_PYTHON" ]; then printf '%s' "$ENGINE_PYTHON"; return 0; fi
    system_python
}

run_logged() {
    # run_logged <logfile> <command...> : stream to the console and append to the log; returns the command's exit code.
    local log="$1"; shift
    printf '    > %s\n' "$*"
    { printf '> %s\n' "$*"; } >> "$log"
    local code=0
    "$@" 2>&1 | tee -a "$log" || code="${PIPESTATUS[0]}"
    return "$code"
}

editor_open_on_project() {
    # The open editor holds a write lock on loaded assets; headless jobs must not run beside it.
    if [ "$(uname -s)" != "Darwin" ]; then return 1; fi
    # No grep -q: with pipefail an early exit would SIGPIPE the upstream grep and hide the match.
    ps -axo command= 2>/dev/null | grep -v grep | grep "UnrealEditor.*$PROJECT_NAME\.uproject" >/dev/null
}

module_binary() {
    # The editor module built by build_editor.sh (Development configuration).
    printf '%s' "$PROJECT_DIR/Binaries/Mac/UnrealEditor-$PROJECT_NAME.dylib"
}
