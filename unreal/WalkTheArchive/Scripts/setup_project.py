"""Entry point for the Walk the Archive editor setup (contract section 6).

Run inside UnrealEditor-Cmd with the project loaded:
  UnrealEditor-Cmd <uproject> -ExecutePythonScript=<abs path to this file> -unattended -nopause -nosplash
                   -stdout -FullStdOutLogOutput -ScriptErrorsAreFatal

Environment:
  WTA_STEPS   comma list of steps to run, default all, in contract order:
              probe, import_meshes, import_art, data_tables, build_level, lighting, actors, navmesh,
              project_settings, verify
  WTA_FORCE   1 = re-import meshes and art that already exist
  WTA_SHOTS   0 = skip the verify screenshots

Every step prints one line 'WTA_RESULT {json}'. If any step failed this script raises at the end, which
-ScriptErrorsAreFatal turns into a non-zero exit code.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(HERE)
PYTHON_DIR = os.path.join(PROJECT_DIR, "Content", "Python")
if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)


def main():
    try:
        import unreal  # noqa: F401
    except ImportError:
        print("WTA_RESULT " + json.dumps({"step": "setup_project", "ok": False,
                                          "error": "the unreal module is missing: run this inside UnrealEditor-Cmd"}))
        raise

    from wta_setup import pipeline

    try:
        steps = pipeline.parse_steps(os.environ.get("WTA_STEPS", ""))
    except ValueError as exc:
        print("WTA_RESULT " + json.dumps({"step": "setup_project", "ok": False, "error": str(exc)}))
        raise

    results = pipeline.run(steps)
    failed = [r["step"] for r in results if not r.get("ok")]
    summary = {"steps": [r["step"] for r in results], "failed": failed, "ok": not failed}
    print("WTA_SUMMARY " + json.dumps(summary))
    sys.stdout.flush()
    if failed:
        raise RuntimeError("Walk the Archive setup failed in step(s): " + ", ".join(failed))


if __name__ == "__main__":
    main()
