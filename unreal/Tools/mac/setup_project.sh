#!/usr/bin/env bash
# setup_project.sh - run the headless editor setup (Scripts/setup_project.py) and check every WTA_RESULT line.
#   1. configure_plugins.py enables the optional plugins this engine has.
#   2. Builds the editor module first if Binaries/Mac/UnrealEditor-WalkTheArchive.dylib is missing.
#   3. UnrealEditor-Cmd <uproject> -ExecutePythonScript=<Scripts/setup_project.py> -unattended -nopause
#      -nosplash -stdout -FullStdOutLogOutput -ScriptErrorsAreFatal, tee'd to Tools/.cache/setup.log.
#   4. check_results.py judges the log; exit is non-zero if the editor or any step failed.
# The first run compiles shaders and can take 10-40 minutes before the first step prints.
#   ./Tools/mac/setup_project.sh [--steps probe,import_meshes,...] [--nullrhi] [--no-build] [--skip-plugins] [--force]
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
require_mac

STEPS="all"; NULLRHI=0; NO_BUILD=0; SKIP_PLUGINS=0; FORCE=0
while [ $# -gt 0 ]; do
    case "$1" in
        --steps) STEPS="$2"; shift 2 ;;
        --steps=*) STEPS="${1#--steps=}"; shift ;;
        --nullrhi) NULLRHI=1; shift ;;
        --no-build) NO_BUILD=1; shift ;;
        --skip-plugins) SKIP_PLUGINS=1; shift ;;
        --force) FORCE=1; shift ;;
        -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
        *) fail "unknown argument $1"; exit 2 ;;
    esac
done

step "Setup project (headless editor Python)"
[ -f "$UPROJECT" ] || { fail "no project file at $UPROJECT"; exit 1; }
[ -f "$SETUP_SCRIPT" ] || { fail "no setup script at $SETUP_SCRIPT"; exit 1; }
require_engine
[ -x "$EDITOR_CMD" ] || { fail "editor binary missing at $EDITOR_CMD"; exit 1; }
PY="$(best_python || true)"
[ -n "$PY" ] || { fail "no Python found (the engine ships one under Engine/Binaries/ThirdParty/Python3/Mac/bin)"; exit 1; }

case "$SETUP_SCRIPT" in *" "*) warn "the setup script path contains spaces ($SETUP_SCRIPT). -ExecutePythonScript treats the first space-separated token as the file, so the run may never start a step; move the repo to a path without spaces (COWORK.md step 0) if no WTA_RESULT line appears." ;; esac

if editor_open_on_project && [ "$FORCE" != "1" ]; then
    fail "An Unreal Editor has this project open. It holds a write lock on loaded assets; close it and rerun (or pass --force)."
    exit 1
fi

init_cache_dir
LOG="$CACHE_DIR/setup.log"
ENGINE_LOG="$CACHE_DIR/setup_editor_full.log"
: > "$LOG"
note "log: $LOG"

if [ "$SKIP_PLUGINS" != "1" ]; then
    step "Optional plugins"
    code=0
    run_logged "$LOG" "$PY" "$COMMON_DIR/configure_plugins.py" --uproject "$UPROJECT" --engine "$ENGINE_ROOT" || code=$?
    if [ "$code" != "0" ]; then fail "configure_plugins.py failed (exit $code)"; exit "$code"; fi
fi

BIN="$(module_binary)"
if [ ! -f "$BIN" ]; then
    if [ "$NO_BUILD" = "1" ]; then fail "editor module missing ($BIN); run build_editor.sh first."; exit 1; fi
    step "Editor module missing; building it first"
    "$WTA_MAC_DIR/build_editor.sh" || { code=$?; fail "build_editor.sh failed; see its log."; exit "$code"; }
fi

step "Run the editor headless"
note "First run on this machine: shader compilation can take 10-40 minutes before the first WTA_RESULT line."
UE_EXIT=0
if [ "$STEPS" != "all" ] && [ -n "$STEPS" ]; then export WTA_STEPS="$STEPS"; note "WTA_STEPS=$STEPS"; fi
ARGS=("$UPROJECT" "-ExecutePythonScript=$SETUP_SCRIPT" -unattended -nopause -nosplash -stdout -FullStdOutLogOutput -ScriptErrorsAreFatal "-abslog=$ENGINE_LOG")
[ "$NULLRHI" = "1" ] && ARGS+=(-NullRHI)
( cd "$PROJECT_DIR" && run_logged "$LOG" "$EDITOR_CMD" "${ARGS[@]}" ) || UE_EXIT=$?
note "editor exit code: $UE_EXIT"

step "Check results"
CHECK_EXIT=0
if [ "$STEPS" != "all" ] && [ -n "$STEPS" ]; then
    "$PY" "$COMMON_DIR/check_results.py" "$LOG" --steps "$STEPS" || CHECK_EXIT=$?
else
    "$PY" "$COMMON_DIR/check_results.py" "$LOG" || CHECK_EXIT=$?
fi
OK=false; [ "$UE_EXIT" = "0" ] && [ "$CHECK_EXIT" = "0" ] && OK=true
note "setup log: $LOG"
note "full engine log: $ENGINE_LOG"
result_line setup_project "$OK" "\"editor_exit\": $UE_EXIT, \"check_exit\": $CHECK_EXIT, \"log\": \"$(json_escape "$LOG")\", \"steps\": \"$(json_escape "$STEPS")\""
[ "$OK" = "true" ] || exit 1
exit 0
