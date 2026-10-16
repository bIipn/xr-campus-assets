#!/usr/bin/env bash
# preflight.sh - check this Mac for Walk the Archive (Unreal Engine 5.8) and print a verdict.
# Collects macOS version, CPU, RAM, GPU (system_profiler + sysctl), free disk on the repo volume,
# and whether UE 5.8, Xcode, git, Blender, Homebrew and the Epic Games Launcher are installed.
# Verdict: STANDARD (Apple Silicon: software Lumen; M2+ may try HWRT/MegaLights, Experimental)
# or NOT_SUPPORTED (Intel Mac, macOS < 14, < 16 GB). FULL is Windows-only in 5.8.
# Writes Tools/.cache/preflight.json. Exit 0 for STANDARD, 2 for NOT_SUPPORTED, 1 on error.
#   ./Tools/mac/preflight.sh [--json]
source "$(dirname "${BASH_SOURCE[0]}")/_common.sh"
require_mac

PRINT_JSON=0
for a in "$@"; do case "$a" in --json) PRINT_JSON=1 ;; -h|--help) sed -n '2,9p' "$0"; exit 0 ;; esac; done

step "Preflight: macOS"
OS_VERSION="$(sw_vers -productVersion 2>/dev/null || echo 0)"
OS_MAJOR="${OS_VERSION%%.*}"
ARCH="$(uname -m)"
CPU="$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo unknown)"
CORES="$(sysctl -n hw.ncpu 2>/dev/null || echo 0)"
MEM_BYTES="$(sysctl -n hw.memsize 2>/dev/null || echo 0)"
RAM_GB=$(( MEM_BYTES / 1024 / 1024 / 1024 ))

# GPU: Apple Silicon reports the chip and core count (memory is unified); Intel Macs report VRAM.
GPU_NAME=""; GPU_CORES=""; GPU_VRAM=""
if command -v system_profiler >/dev/null 2>&1; then
    SP="$(system_profiler SPDisplaysDataType 2>/dev/null || true)"
    GPU_NAME="$(printf '%s\n' "$SP" | sed -n 's/^[[:space:]]*Chipset Model: *//p' | head -1)"
    GPU_CORES="$(printf '%s\n' "$SP" | sed -n 's/^[[:space:]]*Total Number of Cores: *//p' | head -1)"
    GPU_VRAM="$(printf '%s\n' "$SP" | sed -n 's/^[[:space:]]*VRAM ([^)]*): *//p' | head -1)"
fi
[ -n "$GPU_NAME" ] || GPU_NAME="$CPU"

FREE_GB="$(df -kP "$REPO_ROOT" 2>/dev/null | awk 'NR==2 {printf "%d", $4/1024/1024}')"
FREE_GB="${FREE_GB:-0}"

# Installed tools.
ENGINE_ROOT=""; ENGINE_VERSION_FOUND=""
if find_engine; then :; fi
XCODE_PATH="$(xcode-select -p 2>/dev/null || true)"
XCODE_VERSION="$(xcodebuild -version 2>/dev/null | head -1 || true)"
GIT_VERSION=""
if have_clt && command -v git >/dev/null 2>&1; then GIT_VERSION="$(git --version 2>/dev/null || true)"; fi
BLENDER=""
if [ -x "/Applications/Blender.app/Contents/MacOS/Blender" ]; then BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"
elif command -v blender >/dev/null 2>&1; then BLENDER="$(command -v blender)"; fi
BREW="$(command -v brew 2>/dev/null || true)"
LAUNCHER=""; [ -d "/Applications/Epic Games Launcher.app" ] && LAUNCHER="/Applications/Epic Games Launcher.app"
SYS_PY="$(system_python 2>/dev/null || true)"

VERDICT="STANDARD"; REASONS=()
if [ "$ARCH" != "arm64" ]; then
    VERDICT="NOT_SUPPORTED"; REASONS+=("Intel Mac ($ARCH): UE 5.8 removed Intel Mac rendering support.")
fi
if [ "${OS_MAJOR:-0}" -lt 14 ] 2>/dev/null; then
    VERDICT="NOT_SUPPORTED"; REASONS+=("macOS $OS_VERSION: 14.5 (Sonoma) or newer is required.")
fi
if [ "$RAM_GB" -lt 16 ]; then
    VERDICT="NOT_SUPPORTED"; REASONS+=("RAM is ${RAM_GB} GB; the editor with Lumen and Nanite needs 16 GB (32 GB recommended).")
fi
if [ "$VERDICT" != "NOT_SUPPORTED" ]; then
    case "$CPU" in
        *" M1"*) REASONS+=("$CPU: software Lumen only; Nanite and Virtual Shadow Maps need M2 or newer.") ;;
        *) REASONS+=("$CPU: software Lumen + Nanite/VSM (Beta). HWRT Lumen and MegaLights are Experimental on Mac and stay off in DefaultDeviceProfiles.ini.") ;;
    esac
    [ "$RAM_GB" -lt 32 ] && REASONS+=("RAM is ${RAM_GB} GB; 32 GB is recommended for shader compiles.")
    [ "$FREE_GB" -lt 120 ] && REASONS+=("Only ${FREE_GB} GB free; UE 5.8 (~50 GB), Xcode (~15 GB) and the shader cache need around 120 GB.")
    if [ -z "$XCODE_VERSION" ]; then REASONS+=("Full Xcode (26.0+, 26.1.1 recommended) is required for the C++ build; the Command Line Tools alone are not enough."); fi
fi
case "$REPO_ROOT" in *" "*) REASONS+=("The repo path contains spaces; UAT cooks on Mac are known to misquote them. Prefer a path without spaces.") ;; esac

init_cache_dir
JSON_PATH="$CACHE_DIR/preflight.json"
reasons_json=""
for r in "${REASONS[@]+"${REASONS[@]}"}"; do
    [ -n "$reasons_json" ] && reasons_json="$reasons_json, "
    reasons_json="$reasons_json\"$(json_escape "$r")\""
done
cat > "$JSON_PATH" <<EOF
{
  "step": "preflight",
  "platform": "mac",
  "time": "$(date +%Y-%m-%dT%H:%M:%S)",
  "os": {"version": "$(json_escape "$OS_VERSION")", "arch": "$ARCH"},
  "cpu": {"name": "$(json_escape "$CPU")", "cores": ${CORES:-0}},
  "ram_gb": $RAM_GB,
  "gpus": [{"name": "$(json_escape "$GPU_NAME")", "cores": "$(json_escape "$GPU_CORES")", "vram": "$(json_escape "$GPU_VRAM")", "memory": "unified"}],
  "disk": {"path": "$(json_escape "$REPO_ROOT")", "free_gb": $FREE_GB},
  "repo_root": "$(json_escape "$REPO_ROOT")",
  "installed": {
    "unreal": $( [ -n "$ENGINE_ROOT" ] && printf '{"root": "%s", "version": "%s"}' "$(json_escape "$ENGINE_ROOT")" "$ENGINE_VERSION_FOUND" || printf 'null' ),
    "epic_launcher": $( [ -n "$LAUNCHER" ] && printf '"%s"' "$(json_escape "$LAUNCHER")" || printf 'null' ),
    "xcode": $( [ -n "$XCODE_VERSION" ] && printf '{"path": "%s", "version": "%s"}' "$(json_escape "$XCODE_PATH")" "$(json_escape "$XCODE_VERSION")" || printf 'null' ),
    "command_line_tools": $( have_clt && printf 'true' || printf 'false' ),
    "git": $( [ -n "$GIT_VERSION" ] && printf '"%s"' "$(json_escape "$GIT_VERSION")" || printf 'null' ),
    "blender": $( [ -n "$BLENDER" ] && printf '"%s"' "$(json_escape "$BLENDER")" || printf 'null' ),
    "homebrew": $( [ -n "$BREW" ] && printf '"%s"' "$(json_escape "$BREW")" || printf 'null' ),
    "system_python": $( [ -n "$SYS_PY" ] && printf '"%s"' "$(json_escape "$SYS_PY")" || printf 'null' )
  },
  "verdict": "$VERDICT",
  "reasons": [$reasons_json]
}
EOF

note "macOS    : $OS_VERSION ($ARCH)"
note "CPU      : $CPU ($CORES cores)"
note "RAM      : ${RAM_GB} GB (unified with the GPU)"
note "GPU      : $GPU_NAME${GPU_CORES:+ ($GPU_CORES GPU cores)}${GPU_VRAM:+ VRAM $GPU_VRAM}"
note "Disk     : ${FREE_GB} GB free on the volume holding $REPO_ROOT"
UE_LINE="not installed"; [ -n "$ENGINE_ROOT" ] && UE_LINE="$ENGINE_VERSION_FOUND at $ENGINE_ROOT"
note "UE 5.8   : $UE_LINE"
note "Launcher : ${LAUNCHER:-not installed}"
note "Xcode    : ${XCODE_VERSION:-not installed}${XCODE_PATH:+ ($XCODE_PATH)}"
note "git      : ${GIT_VERSION:-not installed}"
note "Blender  : ${BLENDER:-not installed}"
note "Homebrew : ${BREW:-not installed}"
for r in "${REASONS[@]+"${REASONS[@]}"}"; do note "- $r"; done
note "Report   : $JSON_PATH"
[ "$PRINT_JSON" = "1" ] && cat "$JSON_PATH"

case "$VERDICT" in
    NOT_SUPPORTED) printf '\033[31mPREFLIGHT_VERDICT %s\033[0m\n' "$VERDICT" ;;
    *) printf '\033[33mPREFLIGHT_VERDICT %s\033[0m\n' "$VERDICT" ;;
esac
if [ "$VERDICT" = "NOT_SUPPORTED" ]; then
    result_line preflight false "\"verdict\": \"$VERDICT\", \"report\": \"$(json_escape "$JSON_PATH")\""
    exit 2
fi
result_line preflight true "\"verdict\": \"$VERDICT\", \"report\": \"$(json_escape "$JSON_PATH")\""
exit 0
