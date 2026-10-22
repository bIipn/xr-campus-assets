#!/usr/bin/env python3
"""Build the whole campus for one client from its pack (clients/<name>/campus.json): the words on the museum's
friezes, the app on the tablet and phone screens, the book's pages, the held props, the Wax Hall settees, the
reading room, the museum and the grounds, the data tables, and the Unreal-ready meshes. Then on the Unreal
machine: Tools/win/setup_project.ps1 (import_meshes, surfaces, data_tables, build_level, lighting, actors, ...).

    python3 build_client.py --client clients/xrlibraries            # everything (Blender's bpy must import)
    python3 build_client.py --client clients/acme --only screens,props,data

Steps, in order: textures (the friezes), screens, slides (the talks' slides), props, seats, library, museum,
exterior, data, prepare, voices (the talks read aloud; needs the Kokoro model, skipped when it is not there), ini.
A client pack is a copy of clients/xrlibraries with its own words and content folder (and its own talks.json for the
talks and classes); the campus is the same.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

STEPS = [
    ("textures", [PY, "bl/textures.py", "frieze"]),
    ("screens", [PY, "bl/screens.py"]),
    ("slides", [PY, "bl/slides.py"]),
    ("props", [PY, "bl/props.py"]),
    ("seats", [PY, "bl/seats.py"]),
    ("library", [PY, "bl/library.py", "--ue"]),
    ("library_export", [PY, "unreal/Pipeline/blender/export_reading_room.py"]),
    ("museum", [PY, "bl/museum.py"]),
    ("exterior", [PY, "bl/exterior.py"]),
    ("data", [PY, "unreal/Pipeline/data/build_data.py"]),
    ("prepare", [PY, "unreal/Pipeline/blender/prepare_for_unreal.py", "--", "HandProps", "Seats", "ReadingRoom", "Museum", "Outside"]),
    ("voices", [PY, "unreal/Tools/voice/make_talk_voices.py"]),
    ("ini", None),
]
OPTIONAL = {"voices"}      # a failure here does not stop the build (the slides still run on their own clock)


def write_ini(pack):
    """The client's and the campus's names into DefaultGame.ini's WTASettings section (idempotent)."""
    path = os.path.join(ROOT, "unreal", "WalkTheArchive", "Config", "DefaultGame.ini")
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    section = "[/Script/WalkTheArchive.WTASettings]"
    if section not in text:
        text += "\n" + section + "\n"
    for key, value in (("ClientName", pack.get("client", "")), ("CampusTitle", pack.get("campus", ""))):
        if not value:
            continue
        line = "%s=%s" % (key, value)
        pattern = re.compile(r"^%s=.*$" % re.escape(key), re.M)
        if pattern.search(text):
            text = pattern.sub(line, text, count=1)
        else:
            text = text.replace(section + "\n", section + "\n" + line + "\n", 1)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--client", default="clients/xrlibraries", help="the client pack folder (holds campus.json)")
    ap.add_argument("--only", default="", help="comma list of steps to run (default all)")
    args = ap.parse_args()
    folder = os.path.abspath(os.path.join(ROOT, args.client))
    with open(os.path.join(folder, "campus.json"), "r", encoding="utf-8") as fh:
        pack = json.load(fh)
    wanted = [s.strip() for s in args.only.split(",") if s.strip()] or [name for name, _ in STEPS]
    env = dict(os.environ, WTA_CLIENT=folder)
    print("client pack:", folder, "-", pack.get("client"), "/", pack.get("campus"), flush=True)
    results = []
    for name, cmd in STEPS:
        if name not in wanted and not (name == "library_export" and "library" in wanted):
            continue
        t0 = time.time()
        if cmd is None:
            path = write_ini(pack)
            results.append((name, True, "%s" % os.path.relpath(path, ROOT), time.time() - t0))
            continue
        log = os.path.join(ROOT, "assets", "build_%s.log" % name)
        os.makedirs(os.path.dirname(log), exist_ok=True)
        with open(log, "w", encoding="utf-8") as fh:
            proc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=fh, stderr=subprocess.STDOUT)
        ok = proc.returncode == 0
        results.append((name, ok or name in OPTIONAL, os.path.relpath(log, ROOT), time.time() - t0))
        print("%-15s %s  %5.0f s  %s" % (name, "ok " if ok else ("skipped" if name in OPTIONAL else "FAILED"), time.time() - t0, os.path.relpath(log, ROOT)), flush=True)
        if not ok and name not in OPTIONAL:
            break
    failed = [r for r in results if not r[1]]
    print("done:", "all %d steps ok" % len(results) if not failed else "%s failed, see its log" % failed[0][0], flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
