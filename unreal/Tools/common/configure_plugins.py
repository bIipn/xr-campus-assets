#!/usr/bin/env python3
"""Enable optional engine plugins in WalkTheArchive.uproject, but only the ones this engine has.

The .uproject commits only plugins whose names are certain (PythonScriptPlugin,
EditorScriptingUtilities). Everything optional is added here after checking that a matching
.uplugin exists under <Engine>/Plugins, so the project never references a plugin the
installed engine lacks. Each added reference also carries "Optional": true, so a machine
with a different engine build still opens the project.

Groups (use --only / --skip with these names):
  mcp         ModelContextProtocol (5.8 Experimental MCP server) plus its *Toolset* plugins
              (minus MCP_TOOLSET_EXCLUDE: AllToolsets and SemanticSearchToolset)
  metahuman   every MetaHuman*.uplugin (MetaHuman Creator / core plugins in 5.8)
  openxr      OpenXR
  pixelstreaming  PixelStreaming2
  water       Water
  niagara     Niagara (enabled by default in the engine; made explicit)
  procmesh    ProceduralMeshComponent
  geoscript   GeometryScripting

Idempotent: a second run reports "already enabled" and rewrites nothing.
Works with any Python 3.8+ (stdlib only); run it with Unreal's bundled Python when available.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import find_engine  # noqa: E402

DEFAULT_UPROJECT = os.path.normpath(os.path.join(HERE, "..", "..", "WalkTheArchive", "WalkTheArchive.uproject"))

# Group name -> list of exact plugin names, or a pattern rule handled in resolve_group().
GROUPS = {
    "mcp": {"exact": ["ModelContextProtocol"], "pattern": "mcp_toolsets"},
    "metahuman": {"exact": [], "pattern": "metahuman"},
    "openxr": {"exact": ["OpenXR"]},
    "pixelstreaming": {"exact": ["PixelStreaming2"]},
    "water": {"exact": ["Water"]},
    "niagara": {"exact": ["Niagara"]},
    "procmesh": {"exact": ["ProceduralMeshComponent"]},
    "geoscript": {"exact": ["GeometryScripting"]},
}
GROUP_ORDER = ["mcp", "metahuman", "openxr", "pixelstreaming", "water", "niagara", "procmesh", "geoscript"]

# Toolsets the mcp group leaves out on purpose. AllToolsets is a bundle that pulls every toolset in again,
# including SemanticSearchToolset, whose Experimental SemanticSearch plugin crashed UnrealEditor on exit in
# 5.8.3 (access violation in UnrealEditor-SemanticSearch.dll while cancelling its asset indexing).
MCP_TOOLSET_EXCLUDE = {"AllToolsets", "SemanticSearchToolset"}


def index_uplugins(engine_root):
    """Map plugin name -> .uplugin path for every plugin under <Engine>/Plugins."""
    plugins_dir = os.path.join(engine_root, "Engine", "Plugins")
    found = {}
    if not os.path.isdir(plugins_dir):
        return found, plugins_dir
    for dirpath, dirnames, filenames in os.walk(plugins_dir):
        # Plugins never nest their .uplugin inside Content, Source or Binaries; skip those trees.
        dirnames[:] = [d for d in dirnames if d not in ("Content", "Source", "Binaries", "Intermediate", "Resources", "Config", "Shaders")]
        for name in filenames:
            if name.endswith(".uplugin"):
                found.setdefault(name[:-len(".uplugin")], os.path.join(dirpath, name))
    return found, plugins_dir


def read_uplugin(path):
    """Parse a .uplugin JSON file; return {} when unreadable."""
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def depends_on(uplugin_data, plugin_name):
    """True when the .uplugin lists plugin_name in its Plugins dependency array."""
    for ref in uplugin_data.get("Plugins") or []:
        if isinstance(ref, dict) and ref.get("Name") == plugin_name:
            return True
    return False


def resolve_group(group, index):
    """Return a list of (plugin_name, reason) for the group given the engine's plugin index."""
    spec = GROUPS[group]
    chosen = []
    for name in spec.get("exact", []):
        if name in index:
            chosen.append((name, "exact name"))
    pattern = spec.get("pattern")
    if pattern == "metahuman":
        for name in sorted(index):
            if name.startswith("MetaHuman"):
                chosen.append((name, "name pattern MetaHuman*"))
    elif pattern == "mcp_toolsets" and "ModelContextProtocol" in index:
        mcp_dir = os.path.dirname(os.path.dirname(index["ModelContextProtocol"]))
        for name in sorted(index):
            if "Toolset" not in name or name in MCP_TOOLSET_EXCLUDE:
                continue
            path = index[name]
            data = read_uplugin(path)
            if depends_on(data, "ModelContextProtocol"):
                chosen.append((name, "*Toolset* depending on ModelContextProtocol"))
            elif "ModelContextProtocol" in name or "MCP" in name:
                chosen.append((name, "*Toolset* named after MCP"))
            elif os.path.normpath(path).startswith(os.path.normpath(mcp_dir) + os.sep):
                chosen.append((name, "*Toolset* beside ModelContextProtocol"))
    return chosen


def load_uproject(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def save_uproject(path, data):
    # Unreal writes .uproject files with tabs and a trailing newline; keep that shape.
    text = json.dumps(data, indent="\t", ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def apply(uproject, wanted, dry_run=False):
    """Add or enable plugin references. Returns (changed, enabled, already, report)."""
    data = load_uproject(uproject)
    plugins = data.setdefault("Plugins", [])
    by_name = {}
    for ref in plugins:
        if isinstance(ref, dict) and "Name" in ref:
            by_name[ref["Name"]] = ref
    enabled, already = [], []
    for name, reason in wanted:
        ref = by_name.get(name)
        if ref is None:
            plugins.append({"Name": name, "Enabled": True, "Optional": True})
            enabled.append((name, reason))
        elif not ref.get("Enabled", False):
            ref["Enabled"] = True
            enabled.append((name, "re-enabled; " + reason))
        else:
            already.append((name, reason))
    changed = bool(enabled)
    if changed and not dry_run:
        save_uproject(uproject, data)
    return changed, enabled, already, data


def main(argv=None):
    parser = argparse.ArgumentParser(description="Enable optional plugins that exist in the installed engine.")
    parser.add_argument("--uproject", default=DEFAULT_UPROJECT, help="path to WalkTheArchive.uproject")
    parser.add_argument("--engine", help="engine root (default: find_engine.py / UE_ROOT)")
    parser.add_argument("--only", help="comma list of groups to process: " + ",".join(GROUP_ORDER))
    parser.add_argument("--skip", help="comma list of groups to leave alone")
    parser.add_argument("--dry-run", action="store_true", help="report without writing the .uproject")
    parser.add_argument("--json", action="store_true", help="print the report as JSON as well")
    parser.add_argument("--platform", choices=["win", "mac", "linux"], help="passed to find_engine (tests)")
    args = parser.parse_args(argv)

    if not os.path.isfile(args.uproject):
        sys.stderr.write("configure_plugins: no .uproject at %s\n" % args.uproject)
        return 2

    engine_root = args.engine or os.environ.get("UE_ROOT")
    if not engine_root:
        engine_root, _via, _checked = find_engine.find_engine(plat=args.platform)
    if not engine_root or not find_engine.looks_like_engine(engine_root):
        sys.stderr.write("configure_plugins: engine not found; pass --engine <root> or set UE_ROOT\n")
        return 1

    groups = list(GROUP_ORDER)
    if args.only:
        only = [g.strip() for g in args.only.split(",") if g.strip()]
        bad = [g for g in only if g not in GROUPS]
        if bad:
            sys.stderr.write("configure_plugins: unknown group(s): %s\n" % ", ".join(bad))
            return 2
        groups = [g for g in GROUP_ORDER if g in only]
    if args.skip:
        skip = [g.strip() for g in args.skip.split(",") if g.strip()]
        groups = [g for g in groups if g not in skip]

    index, plugins_dir = index_uplugins(engine_root)
    print("configure_plugins: engine %s (%d plugins under %s)" % (engine_root, len(index), plugins_dir))

    wanted, absent = [], []
    for group in groups:
        chosen = resolve_group(group, index)
        if chosen:
            wanted.extend(chosen)
        else:
            absent.append(group)

    changed, enabled, already, _data = apply(args.uproject, wanted, args.dry_run)

    for name, reason in enabled:
        print("  enabled  %-40s (%s)" % (name, reason))
    for name, reason in already:
        print("  present  %-40s (%s)" % (name, reason))
    for group in absent:
        print("  absent   %-40s (no matching .uplugin in this engine; skipped)" % group)
    if args.dry_run and changed:
        print("configure_plugins: dry run, .uproject not written")
    elif changed:
        print("configure_plugins: wrote %s" % args.uproject)
    else:
        print("configure_plugins: nothing to change")

    report = {
        "step": "configure_plugins",
        "ok": True,
        "engine": engine_root,
        "enabled": [n for n, _ in enabled],
        "already": [n for n, _ in already],
        "absent_groups": absent,
        "changed": changed and not args.dry_run,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    # One machine-checkable line in the same shape as the editor setup steps.
    print("WTA_RESULT " + json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
