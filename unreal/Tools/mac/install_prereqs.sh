#!/usr/bin/env bash
# install_prereqs.sh - install the macOS prerequisites for Walk the Archive, then list the manual steps.
# Checks Xcode (must come from the App Store; cannot be scripted without a signed-in `mas`),
# Homebrew (prints the official install command; it needs your password), then
#   brew install --cask epic-games blender
# Unreal Engine 5.8 itself is installed from the Launcher after signing in (printed at the end).
#   ./Tools/mac/install_prereqs.sh [--only epic-games,blender] [--skip blender] [--dry-run]
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
require_mac

ONLY=""; SKIP=""; DRY_RUN=0
while [ $# -gt 0 ]; do
    case "$1" in
        --only) ONLY="$2"; shift 2 ;;
        --skip) SKIP="$2"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
        *) fail "unknown argument $1"; exit 2 ;;
    esac
done

wanted() {
    # wanted <item>: true when the item is selected by --only/--skip.
    local item="$1"
    if [ -n "$ONLY" ]; then case ",$ONLY," in *",$item,"*) ;; *) return 1 ;; esac; fi
    case ",$SKIP," in *",$item,"*) return 1 ;; esac
    return 0
}

init_cache_dir
LOG="$CACHE_DIR/install_prereqs.log"
FAILED=0

step "Xcode"
if xcodebuild -version >/dev/null 2>&1; then
    note "present: $(xcodebuild -version | head -1) at $(xcode-select -p)"
else
    warn "Full Xcode is not installed or not selected. The C++ project needs it (Epic's 5.8 page: Xcode 26.0 minimum, 26.1.1 recommended, 26.4 not compatible)."
    note "Install Xcode from the App Store, then run:"
    note "  sudo xcode-select -s /Applications/Xcode.app && sudo xcodebuild -license accept"
    note "and open Xcode once so it installs its components."
    if command -v mas >/dev/null 2>&1; then note "(mas is installed: 'mas install 497799835' installs Xcode if you are signed in to the App Store.)"; fi
fi

step "Homebrew"
if command -v brew >/dev/null 2>&1; then
    note "present: $(command -v brew)"
else
    fail "Homebrew is missing. Install it (asks for your password), then rerun this script:"
    note '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    FAILED=1
fi

if command -v brew >/dev/null 2>&1; then
    for cask in epic-games blender; do
        wanted "$cask" || continue
        step "brew cask: $cask"
        if brew list --cask "$cask" >/dev/null 2>&1; then
            note "present"
            continue
        fi
        if [ "$cask" = "epic-games" ] && [ -d "/Applications/Epic Games Launcher.app" ]; then note "present (installed outside Homebrew)"; continue; fi
        if [ "$cask" = "blender" ] && [ -d "/Applications/Blender.app" ]; then note "present (installed outside Homebrew)"; continue; fi
        if [ "$DRY_RUN" = "1" ]; then note "[dry run] brew install --cask $cask"; continue; fi
        if ! run_logged "$LOG" brew install --cask "$cask"; then
            fail "brew install --cask $cask failed (see $LOG)"; FAILED=1
        fi
    done
fi

step "git"
if have_clt && command -v git >/dev/null 2>&1; then note "present: $(git --version)"; else note "git arrives with Xcode / the Command Line Tools (xcode-select --install)."; fi

step "Manual steps that remain"
note "1. Open Epic Games Launcher and sign in (Epic account + two-factor code)."
note "2. Unreal Engine > Library > \"+\" > choose 5.8.x > Install (default folder /Users/Shared/Epic Games/UE_5.8)."
note "3. Start the engine once from the Launcher so it registers; then run Tools/mac/build_editor.sh."
note "4. Keep this repo in a path without spaces for UAT cooks."

if [ "$FAILED" != "0" ]; then
    result_line install_prereqs false "\"log\": \"$(json_escape "$LOG")\""
    exit 1
fi
result_line install_prereqs true "\"log\": \"$(json_escape "$LOG")\""
exit 0
