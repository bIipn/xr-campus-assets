#!/usr/bin/env bash
# play.sh - launch Walk the Archive as a game from the editor binary (-game) in a 1920x1080 window.
#   ./Tools/mac/play.sh [--resx 1920] [--resy 1080] [--map /Game/WTA/Maps/L_Campus] [--fullscreen] [--log] [--wait]
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
require_mac

RESX=1920; RESY=1080; MAP=""; FULLSCREEN=0; SHOWLOG=0; WAIT=0
while [ $# -gt 0 ]; do
    case "$1" in
        --resx) RESX="$2"; shift 2 ;;
        --resy) RESY="$2"; shift 2 ;;
        --map) MAP="$2"; shift 2 ;;
        --fullscreen) FULLSCREEN=1; shift ;;
        --log) SHOWLOG=1; shift ;;
        --wait) WAIT=1; shift ;;
        -h|--help) sed -n '2,3p' "$0"; exit 0 ;;
        *) fail "unknown argument $1"; exit 2 ;;
    esac
done

step "Play"
[ -f "$UPROJECT" ] || { fail "no project file at $UPROJECT"; exit 1; }
require_engine
[ -x "$EDITOR_BIN" ] || { fail "UnrealEditor binary missing at $EDITOR_BIN"; exit 1; }
BIN="$(module_binary)"
[ -f "$BIN" ] || { fail "editor module not built ($BIN); run build_editor.sh and setup_project.sh first."; exit 1; }

ARGS=("$UPROJECT")
[ -n "$MAP" ] && ARGS+=("$MAP")
ARGS+=(-game "-ResX=$RESX" "-ResY=$RESY")
if [ "$FULLSCREEN" = "1" ]; then ARGS+=(-fullscreen); else ARGS+=(-windowed); fi
[ "$SHOWLOG" = "1" ] && ARGS+=(-log)
note "Controls: WASD move, mouse look, Shift sprint, Space jump, E/LMB interact, Tab cursor, T tour, M map, Esc menu."
if [ "$WAIT" = "1" ]; then
    CODE=0; ( cd "$PROJECT_DIR" && "$EDITOR_BIN" "${ARGS[@]}" ) || CODE=$?
    OK=false; [ "$CODE" = "0" ] && OK=true
    result_line play "$OK" "\"exit_code\": $CODE"
    exit "$CODE"
fi
init_cache_dir
( cd "$PROJECT_DIR" && nohup "$EDITOR_BIN" "${ARGS[@]}" >/dev/null 2>&1 & echo $! > "$CACHE_DIR/play.pid" ) || true
PID="$(cat "$CACHE_DIR/play.pid" 2>/dev/null || echo 0)"
note "started PID $PID: \"$EDITOR_BIN\" ${ARGS[*]}"
result_line play true "\"pid\": $PID"
exit 0
