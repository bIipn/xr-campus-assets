#!/usr/bin/env bash
# package_game.sh - cook and package Walk the Archive for Mac with RunUAT BuildCookRun.
#   RunUAT.sh BuildCookRun -project=<uproject> -noP4 -platform=Mac -clientconfig=<Config>
#     -build -cook -allmaps -stage -pak -iostore -archive -archivedirectory=unreal/Packaged/Mac
# Output is tee'd to Tools/.cache/package_Mac_<Config>.log. The app lands in unreal/Packaged/Mac/Mac/.
#   ./Tools/mac/package_game.sh [--config Development|Shipping|DebugGame|Test] [--archive DIR] [--skip-build] [--no-iostore]
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
require_mac

CONFIG="Development"; ARCHIVE=""; SKIP_BUILD=0; NO_IOSTORE=0
while [ $# -gt 0 ]; do
    case "$1" in
        --config) CONFIG="$2"; shift 2 ;;
        --archive) ARCHIVE="$2"; shift 2 ;;
        --skip-build) SKIP_BUILD=1; shift ;;
        --no-iostore) NO_IOSTORE=1; shift ;;
        -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
        *) fail "unknown argument $1"; exit 2 ;;
    esac
done
case "$CONFIG" in Development|Shipping|DebugGame|Test) ;; *) fail "unknown config $CONFIG"; exit 2 ;; esac

step "Package Mac $CONFIG"
[ -f "$UPROJECT" ] || { fail "no project file at $UPROJECT"; exit 1; }
require_engine
[ -f "$RUNUAT_SH" ] || { fail "RunUAT.sh missing at $RUNUAT_SH"; exit 1; }
[ -n "$ARCHIVE" ] || ARCHIVE="$UNREAL_DIR/Packaged/Mac"
mkdir -p "$ARCHIVE"
case "$UPROJECT$ARCHIVE" in *" "*) warn "a path contains spaces; UAT on Mac is known to misquote them. Move the repo to a path without spaces if the cook fails." ;; esac
editor_open_on_project && warn "An editor has this project open; close it if the cook fails to save or lock files."

init_cache_dir
LOG="$CACHE_DIR/package_Mac_$CONFIG.log"
: > "$LOG"
note "log: $LOG"
note "archive: $ARCHIVE"

ARGS=(BuildCookRun "-project=$UPROJECT" -noP4 -utf8output -unattended -platform=Mac "-clientconfig=$CONFIG")
[ "$SKIP_BUILD" = "1" ] || ARGS+=(-build)
ARGS+=(-cook -allmaps -stage -pak)
[ "$NO_IOSTORE" = "1" ] || ARGS+=(-iostore)
ARGS+=(-archive "-archivedirectory=$ARCHIVE")
CODE=0
( cd "$PROJECT_DIR" && run_logged "$LOG" "$RUNUAT_SH" "${ARGS[@]}" ) || CODE=$?

APP="$(ls -d "$ARCHIVE/Mac/"*.app 2>/dev/null | head -1 || true)"
PRESENT=false; [ -n "$APP" ] && PRESENT=true
note "UAT exit code: $CODE; app present: $PRESENT${APP:+ ($APP)}"
OK=false; [ "$CODE" = "0" ] && [ "$PRESENT" = "true" ] && OK=true
result_line package_game "$OK" "\"platform\": \"Mac\", \"config\": \"$CONFIG\", \"exit_code\": $CODE, \"archive\": \"$(json_escape "$ARCHIVE")\", \"app\": \"$(json_escape "$APP")\", \"log\": \"$(json_escape "$LOG")\""
[ "$CODE" = "0" ] || exit "$CODE"
[ "$PRESENT" = "true" ] || exit 1
exit 0
