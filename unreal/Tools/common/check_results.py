#!/usr/bin/env python3
"""Read an Unreal log (or captured stdout), extract the WTA_RESULT lines and judge them.

Every setup step prints exactly one line "WTA_RESULT {json}" with at least "step" and "ok"
(contract section 6). This tool prints a table of those lines and exits non-zero when any
step reports ok=false or a required step never reported at all.

Usage:
  check_results.py <logfile> [--steps probe,import_meshes,...] [--required none] [--strict] [--json]

Required steps default to the contract's ten steps; --steps (or the WTA_STEPS environment
variable) narrows them to the steps that were requested. --required none only checks the ok
flags. --strict also fails on engine "Fatal error" / "Critical error" lines.

Works with any Python 3.8+ (stdlib only).
"""

import argparse
import json
import os
import re
import sys

CONTRACT_STEPS = ["probe", "import_meshes", "import_art", "data_tables", "build_level",
                  "lighting", "actors", "navmesh", "project_settings", "verify"]

RESULT_RE = re.compile(r"WTA_RESULT\s+(\{.*\})\s*$")
FATAL_RE = re.compile(r"(Fatal error|=== Critical error ===|Assertion failed|LogPython: Error: .*Traceback)", re.IGNORECASE)
PY_ERROR_RE = re.compile(r"LogPython: Error:")


def parse_line(line):
    """Return the JSON object from a WTA_RESULT line, or None."""
    match = RESULT_RE.search(line)
    if not match:
        return None
    text = match.group(1)
    try:
        return json.loads(text)
    except ValueError:
        # Trailing log decorations can follow the JSON; cut at the last closing brace.
        end = text.rfind("}")
        if end > 0:
            try:
                return json.loads(text[:end + 1])
            except ValueError:
                return None
    return None


def read_lines(path):
    if path == "-":
        return sys.stdin.read().splitlines()
    # UE logs are UTF-8 (with -stdout) but may contain odd bytes; never crash on them.
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read().splitlines()


def summarise(obj):
    """Render the keys other than step/ok/errors as 'key=value' pairs."""
    parts = []
    for key in sorted(obj):
        if key in ("step", "ok", "errors"):
            continue
        value = obj[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, separators=(",", ":"))
        parts.append("%s=%s" % (key, value))
    return " ".join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check WTA_RESULT lines in an Unreal log.")
    parser.add_argument("logfile", help="log file to read, or - for stdin")
    parser.add_argument("--steps", help="comma list of steps that were requested (default: WTA_STEPS env or all)")
    parser.add_argument("--required", help="comma list of required steps, or 'none' to only check ok flags")
    parser.add_argument("--strict", action="store_true", help="also fail on engine fatal/critical error lines")
    parser.add_argument("--json", action="store_true", help="print a JSON summary after the table")
    args = parser.parse_args(argv)

    if args.logfile != "-" and not os.path.isfile(args.logfile):
        sys.stderr.write("check_results: no such file: %s\n" % args.logfile)
        return 2

    if args.required:
        required = [] if args.required.strip().lower() == "none" else [s.strip() for s in args.required.split(",") if s.strip()]
    else:
        steps = args.steps or os.environ.get("WTA_STEPS", "")
        if steps.strip() and steps.strip().lower() != "all":
            required = [s.strip() for s in steps.split(",") if s.strip()]
        else:
            required = list(CONTRACT_STEPS)

    lines = read_lines(args.logfile)
    results = {}
    order = []
    duplicates = 0
    bad_lines = 0
    fatal = []
    py_errors = 0
    for line in lines:
        if "WTA_RESULT" in line:
            obj = parse_line(line)
            if obj is None or not isinstance(obj, dict) or "step" not in obj:
                bad_lines += 1
                continue
            step = str(obj["step"])
            if step in results:
                duplicates += 1
            else:
                order.append(step)
            results[step] = obj
        if FATAL_RE.search(line):
            fatal.append(line.strip()[:200])
        if PY_ERROR_RE.search(line):
            py_errors += 1

    failed = [s for s in order if not results[s].get("ok", False)]
    missing = [s for s in required if s not in results]

    print("%-18s %-5s %s" % ("step", "ok", "details"))
    print("-" * 72)
    for step in order:
        obj = results[step]
        ok = obj.get("ok", False)
        print("%-18s %-5s %s" % (step, "yes" if ok else "NO", summarise(obj)))
        for err in obj.get("errors") or []:
            print("%-18s %-5s   error: %s" % ("", "", err))
    for step in missing:
        print("%-18s %-5s %s" % (step, "--", "MISSING (no WTA_RESULT line)"))
    print("-" * 72)
    if bad_lines:
        print("warning: %d WTA_RESULT line(s) could not be parsed" % bad_lines)
    if duplicates:
        print("warning: %d step(s) reported more than once; the last line counts" % duplicates)
    if py_errors:
        print("warning: %d 'LogPython: Error' line(s) in the log" % py_errors)
    for line in fatal[:5]:
        print("engine error: %s" % line)

    ok = not failed and not missing and not (args.strict and fatal)
    print("check_results: %s (%d reported, %d failed, %d missing)" % ("PASS" if ok else "FAIL", len(order), len(failed), len(missing)))

    if args.json:
        print(json.dumps({"ok": ok, "reported": order, "failed": failed, "missing": missing,
                          "fatal_lines": len(fatal), "python_errors": py_errors, "results": results}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
