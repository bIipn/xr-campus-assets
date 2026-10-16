#!/usr/bin/env bash
# build_editor.sh - generate project files and build the WalkTheArchiveEditor target with UE 5.8.
#   RunUBT.sh -projectfiles -project=<uproject> -game -rocket -progress
#   Engine/Build/BatchFiles/Mac/Build.sh WalkTheArchiveEditor Mac <Config> -Project=<uproject>
# Output is tee'd to Tools/.cache/build_editor.log. Exit code is the build tool's.
#   ./Tools/mac/build_editor.sh [--config Development|DebugGame|Debug] [--target WalkTheArchiveEditor] [--skip-projectfiles]
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
require_mac

CONFIG="Development"; TARGET="WalkTheArchiveEditor"; SKIP_PF=0
while [ $# -gt 0 ]; do
    case "$1" in
        --config) CONFIG="$2"; shift 2 ;;
        --target) TARGET="$2"; shift 2 ;;
        --skip-projectfiles) SKIP_PF=1; shift ;;
        -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
        *) fail "unknown argument $1"; exit 2 ;;
    esac
done

step "Build $TARGET $CONFIG"
[ -f "$UPROJECT" ] || { fail "no project file at $UPROJECT"; exit 1; }
if [ ! -f "$PROJECT_DIR/Source/$TARGET.Target.cs" ]; then
    fail "no $TARGET.Target.cs under $PROJECT_DIR/Source; the C++ sources must be present before building."
    exit 1
fi
require_engine
[ -f "$BUILD_SH" ] || { fail "Build.sh missing at $BUILD_SH"; exit 1; }
if ! xcodebuild -version >/dev/null 2>&1; then
    warn "Full Xcode was not found (xcodebuild -version failed); the build will fail without it. See install_prereqs.sh."
fi

init_cache_dir
LOG="$CACHE_DIR/build_editor.log"
: > "$LOG"
note "log: $LOG"

if [ "$SKIP_PF" != "1" ]; then
    step "Generate project files"
    if [ -f "$RUNUBT_SH" ]; then
        if ! run_logged "$LOG" "$RUNUBT_SH" -projectfiles "-project=$UPROJECT" -game -rocket -progress; then
            code=$?
            fail "project file generation failed (exit $code); see $LOG"
            result_line build_editor false "\"phase\": \"projectfiles\", \"exit_code\": $code, \"log\": \"$(json_escape "$LOG")\""
            exit "$code"
        fi
    else
        warn "RunUBT.sh not found at $RUNUBT_SH; skipping project files (Build.sh does not need them)."
    fi
fi

step "Compile"
CODE=0
run_logged "$LOG" "$BUILD_SH" "$TARGET" Mac "$CONFIG" "-Project=$UPROJECT" -WaitMutex || CODE=$?
BIN="$(module_binary)"
[ "$CONFIG" != "Development" ] && BIN="$PROJECT_DIR/Binaries/Mac/UnrealEditor-$PROJECT_NAME-Mac-$CONFIG.dylib"
BUILT=false; [ -f "$BIN" ] && BUILT=true
note "exit code: $CODE; module binary present: $BUILT"
note "log: $LOG"
OK=false; [ "$CODE" = "0" ] && [ "$BUILT" = "true" ] && OK=true
result_line build_editor "$OK" "\"target\": \"$TARGET\", \"config\": \"$CONFIG\", \"exit_code\": $CODE, \"binary\": \"$(json_escape "$BIN")\", \"log\": \"$(json_escape "$LOG")\""
[ "$CODE" = "0" ] || exit "$CODE"
[ "$BUILT" = "true" ] || exit 1
exit 0
