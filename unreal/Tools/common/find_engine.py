#!/usr/bin/env python3
"""Locate an Unreal Engine 5.8 Launcher install and print its important paths.

Runs on any Python 3.8+ (stdlib only) because it is the one tool that has to work
before Unreal's bundled Python exists. Search order:

  1. UE_ROOT environment variable (or --root), if it points at an engine folder.
  2. The Epic Games Launcher manifest LauncherInstalled.dat (JSON) on Windows
     (%ProgramData%\\Epic\\UnrealEngineLauncher) and Mac (/Users/Shared/Epic Games/UnrealEngineLauncher).
  3. The default install folder: C:/Program Files/Epic Games/UE_5.8 or /Users/Shared/Epic Games/UE_5.8.
  4. Windows only, last resort: HKLM\\SOFTWARE\\EpicGames\\Unreal Engine\\5.8 InstalledDirectory.

Prints the engine root (or a JSON object with --json) and exits non-zero when nothing is found.
"""

import argparse
import json
import os
import sys

DEFAULT_VERSION = "5.8"


def platform_name(override=None):
    """Return 'win', 'mac' or 'linux'. --platform overrides the host (used by tests)."""
    if override:
        return override
    if sys.platform.startswith("win"):
        return "win"
    if sys.platform == "darwin":
        return "mac"
    return "linux"


def read_build_version(root):
    """Return (major, minor, patch) from Engine/Build/Build.version, or None."""
    path = os.path.join(root, "Engine", "Build", "Build.version")
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
        return (int(data.get("MajorVersion", 0)), int(data.get("MinorVersion", 0)), int(data.get("PatchVersion", 0)))
    except (OSError, ValueError, TypeError):
        return None


def looks_like_engine(root):
    """True when the folder has the Engine/Build and Engine/Binaries layout."""
    if not root:
        return False
    return os.path.isdir(os.path.join(root, "Engine", "Binaries")) and os.path.isdir(os.path.join(root, "Engine", "Build"))


def version_matches(root, wanted):
    """True when Build.version agrees with the wanted 'major.minor' string."""
    ver = read_build_version(root)
    if ver is None:
        return False
    major, minor = (int(x) for x in wanted.split(".")[:2])
    return ver[0] == major and ver[1] == minor


def launcher_dat_paths(plat, override=None):
    """Candidate LauncherInstalled.dat locations for the platform."""
    override = override or os.environ.get("WTA_LAUNCHER_DAT")
    if override:
        return [override]
    if plat == "win":
        program_data = os.environ.get("ProgramData", r"C:\ProgramData")
        return [os.path.join(program_data, "Epic", "UnrealEngineLauncher", "LauncherInstalled.dat")]
    if plat == "mac":
        return ["/Users/Shared/Epic Games/UnrealEngineLauncher/LauncherInstalled.dat"]
    return []


def default_roots(plat, wanted):
    """Default Launcher install folders for the platform."""
    if plat == "win":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        return [os.path.join(program_files, "Epic Games", "UE_" + wanted),
                os.path.join(r"C:\Program Files", "Epic Games", "UE_" + wanted)]
    if plat == "mac":
        return [os.path.join("/Users/Shared/Epic Games", "UE_" + wanted)]
    return []


def from_launcher_dat(path, wanted, checked):
    """Return the install location for UE_<wanted> listed in LauncherInstalled.dat, or None."""
    checked.append(path)
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    entries = data.get("InstallationList") or []
    wanted_app = "UE_" + wanted
    # Prefer an exact AppName match, then any entry whose Build.version agrees.
    for entry in entries:
        if str(entry.get("AppName", "")) == wanted_app:
            loc = entry.get("InstallLocation")
            if loc and looks_like_engine(loc):
                return os.path.normpath(loc)
    for entry in entries:
        loc = entry.get("InstallLocation")
        if loc and str(entry.get("NamespaceId", "")) == "ue" and looks_like_engine(loc) and version_matches(loc, wanted):
            return os.path.normpath(loc)
    return None


def from_registry(wanted, checked):
    """Windows only: read the Launcher's registry key for the engine version."""
    key_path = r"SOFTWARE\EpicGames\Unreal Engine\%s" % wanted
    checked.append("HKLM\\" + key_path)
    try:
        import winreg  # noqa: WPS433 (Windows only)
    except ImportError:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            value, _ = winreg.QueryValueEx(key, "InstalledDirectory")
        if value and looks_like_engine(value):
            return os.path.normpath(value)
    except OSError:
        return None
    return None


def engine_paths(root, plat):
    """Every path a script needs, with an exists flag for each."""
    eng = os.path.join(root, "Engine")
    if plat == "win":
        paths = {
            "python": os.path.join(eng, "Binaries", "ThirdParty", "Python3", "Win64", "python.exe"),
            "editor": os.path.join(eng, "Binaries", "Win64", "UnrealEditor.exe"),
            "editor_cmd": os.path.join(eng, "Binaries", "Win64", "UnrealEditor-Cmd.exe"),
            "build": os.path.join(eng, "Build", "BatchFiles", "Build.bat"),
            "run_uat": os.path.join(eng, "Build", "BatchFiles", "RunUAT.bat"),
            "run_ubt": os.path.join(eng, "Build", "BatchFiles", "RunUBT.bat"),
            "ubt": os.path.join(eng, "Binaries", "DotNET", "UnrealBuildTool", "UnrealBuildTool.exe"),
            "version_selector": os.path.join(eng, "Binaries", "Win64", "UnrealVersionSelector.exe"),
        }
    elif plat == "mac":
        app_binary = os.path.join(eng, "Binaries", "Mac", "UnrealEditor.app", "Contents", "MacOS", "UnrealEditor")
        cmd = os.path.join(eng, "Binaries", "Mac", "UnrealEditor-Cmd")
        paths = {
            "python": os.path.join(eng, "Binaries", "ThirdParty", "Python3", "Mac", "bin", "python3"),
            "editor_app": os.path.join(eng, "Binaries", "Mac", "UnrealEditor.app"),
            "editor": app_binary,
            # UnrealEditor-Cmd may not ship on Mac; the .app binary accepts the same arguments.
            "editor_cmd": cmd if os.path.isfile(cmd) else app_binary,
            "build": os.path.join(eng, "Build", "BatchFiles", "Mac", "Build.sh"),
            "run_uat": os.path.join(eng, "Build", "BatchFiles", "RunUAT.sh"),
            "run_ubt": os.path.join(eng, "Build", "BatchFiles", "RunUBT.sh"),
        }
    else:
        paths = {
            "python": os.path.join(eng, "Binaries", "ThirdParty", "Python3", "Linux", "bin", "python3"),
            "editor": os.path.join(eng, "Binaries", "Linux", "UnrealEditor"),
            "editor_cmd": os.path.join(eng, "Binaries", "Linux", "UnrealEditor-Cmd"),
            "build": os.path.join(eng, "Build", "BatchFiles", "Linux", "Build.sh"),
            "run_uat": os.path.join(eng, "Build", "BatchFiles", "RunUAT.sh"),
            "run_ubt": os.path.join(eng, "Build", "BatchFiles", "RunUBT.sh"),
        }
    exists = {name: os.path.exists(path) for name, path in paths.items()}
    return paths, exists


def find_engine(wanted=DEFAULT_VERSION, plat=None, root_override=None, launcher_dat=None):
    """Return (root, found_via, checked_locations). root is None when nothing matched."""
    plat = platform_name(plat)
    checked = []

    env_root = root_override or os.environ.get("UE_ROOT")
    if env_root:
        checked.append(env_root)
        if looks_like_engine(env_root):
            return os.path.normpath(env_root), "UE_ROOT", checked

    for dat in launcher_dat_paths(plat, launcher_dat):
        root = from_launcher_dat(dat, wanted, checked)
        if root:
            return root, "LauncherInstalled.dat", checked

    for root in default_roots(plat, wanted):
        if root in checked:
            continue
        checked.append(root)
        if looks_like_engine(root):
            return os.path.normpath(root), "default path", checked

    if plat == "win":
        root = from_registry(wanted, checked)
        if root:
            return root, "registry", checked

    return None, None, checked


def main(argv=None):
    parser = argparse.ArgumentParser(description="Find an Unreal Engine 5.8 Launcher install.")
    parser.add_argument("--version", default=DEFAULT_VERSION, help="engine major.minor to look for (default 5.8)")
    parser.add_argument("--json", action="store_true", help="print a JSON object with every path")
    parser.add_argument("--get", metavar="KEY", help="print one value only: root, version, python, editor, editor_cmd, build, run_uat, run_ubt, ubt")
    parser.add_argument("--require", metavar="KEYS", help="comma list of path keys that must exist, else exit 3")
    parser.add_argument("--platform", choices=["win", "mac", "linux"], help="override the host platform (tests)")
    parser.add_argument("--root", help="use this engine root instead of searching (same as UE_ROOT)")
    parser.add_argument("--launcher-dat", help="path to a LauncherInstalled.dat to read instead of the default (tests)")
    args = parser.parse_args(argv)

    plat = platform_name(args.platform)
    root, via, checked = find_engine(args.version, plat, args.root, args.launcher_dat)
    if root is None:
        sys.stderr.write("find_engine: Unreal Engine %s not found. Looked at:\n" % args.version)
        for loc in checked:
            sys.stderr.write("  - %s\n" % loc)
        sys.stderr.write("Install UE %s from the Epic Games Launcher (Unreal Engine > Library > + > %s.x > Install)\n"
                         "or set UE_ROOT to the engine folder (the one that contains Engine/).\n" % (args.version, args.version))
        return 1

    ver = read_build_version(root)
    version_str = "%d.%d.%d" % ver if ver else "unknown"
    paths, exists = engine_paths(root, plat)
    result = {
        "root": root,
        "version": version_str,
        "version_matches": version_matches(root, args.version),
        "platform": plat,
        "found_via": via,
        "paths": paths,
        "exists": exists,
    }
    # Flatten the common keys so callers can read them directly.
    for key, value in paths.items():
        result[key] = value

    if args.require:
        missing = [k.strip() for k in args.require.split(",") if k.strip() and not exists.get(k.strip(), False)]
        if missing:
            sys.stderr.write("find_engine: engine at %s is missing: %s\n" % (root, ", ".join(missing)))
            for k in missing:
                sys.stderr.write("  - %s -> %s\n" % (k, paths.get(k, "(unknown key)")))
            return 3

    if not result["version_matches"]:
        sys.stderr.write("find_engine: warning: %s reports version %s, not %s\n" % (root, version_str, args.version))

    if args.get:
        if args.get == "root":
            print(root)
        elif args.get == "version":
            print(version_str)
        elif args.get in paths:
            print(paths[args.get])
        else:
            sys.stderr.write("find_engine: unknown key %r\n" % args.get)
            return 2
        return 0

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
