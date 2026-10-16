#!/usr/bin/env bash
# open_editor.sh - open WalkTheArchive.uproject in the UE 5.8 editor (detached).
#   ./Tools/mac/open_editor.sh [--wait] [--log]
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
require_mac

WAIT=0; SHOWLOG=0
for a in "$@"; do case "$a" in --wait) WAIT=1 ;; --log) SHOWLOG=1 ;; -h|--help) sed -n '2,3p' "$0"; exit 0 ;; *) fail "unknown argument $a"; exit 2 ;; esac; done

step "Open editor"
[ -f "$UPROJECT" ] || { fail "no project file at $UPROJECT"; exit 1; }
require_engine
[ -x "$EDITOR_BIN" ] || { fail "UnrealEditor binary missing at $EDITOR_BIN"; exit 1; }
BIN="$(module_binary)"
[ -f "$BIN" ] || warn "editor module not built ($BIN); the editor will offer to compile it. Prefer build_editor.sh."

ARGS=("$UPROJECT")
[ "$SHOWLOG" = "1" ] && ARGS+=(-log)
if [ "$WAIT" = "1" ]; then
    ( cd "$PROJECT_DIR" && "$EDITOR_BIN" "${ARGS[@]}" ); CODE=$?
    note "editor exited with $CODE"
    OK=false; [ "$CODE" = "0" ] && OK=true
    result_line open_editor "$OK" "\"exit_code\": $CODE"
    exit "$CODE"
fi
# Detached: the editor keeps running after this script returns.
init_cache_dir
( cd "$PROJECT_DIR" && nohup "$EDITOR_BIN" "${ARGS[@]}" >/dev/null 2>&1 & echo $! > "$CACHE_DIR/editor.pid" ) || true
PID="$(cat "$CACHE_DIR/editor.pid" 2>/dev/null || echo 0)"
note "started PID $PID: \"$EDITOR_BIN\" ${ARGS[*]}"
result_line open_editor true "\"pid\": $PID"
exit 0
