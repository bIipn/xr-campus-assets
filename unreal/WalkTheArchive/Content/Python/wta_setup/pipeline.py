"""Runs the setup steps in contract order and prints one WTA_RESULT line per step.

run(steps) imports wta_setup.<step>, calls its run() and reports. An exception inside a step becomes
ok=false with the traceback text, and the pipeline carries on with the next step unless that step needs
one that failed in this run (actors and data_tables need the C++ module the probe checks for).
"""
import importlib
import time
import traceback

from . import STEPS
from . import log

# A step is skipped when one of these earlier steps failed in the same run. A partial mesh import still
# lets build_level place what exists; a failed probe (no C++) or a failed level creation blocks the rest.
DEPENDS_ON = {
    "data_tables": ["probe"],
    "lighting": ["build_level"],
    "actors": ["probe", "build_level"],
    "navmesh": ["build_level"],
}


def parse_steps(text):
    """'probe, import_meshes' -> ['probe', 'import_meshes'] in contract order; empty -> all."""
    if not text or not text.strip():
        return list(STEPS)
    wanted = [s.strip() for s in text.replace(";", ",").split(",") if s.strip()]
    unknown = [s for s in wanted if s not in STEPS]
    if unknown:
        raise ValueError("unknown steps %s (valid: %s)" % (unknown, ", ".join(STEPS)))
    return [s for s in STEPS if s in wanted]


def run_step(step):
    module = importlib.import_module("wta_setup." + step)
    data = module.run()
    if not isinstance(data, dict):
        raise TypeError("step %s returned %r instead of a dict" % (step, type(data).__name__))
    ok = bool(data.pop("ok", False))
    return ok, data


def run(steps=None):
    """Returns the list of result payloads (one per step)."""
    steps = steps if steps is not None else list(STEPS)
    results = []
    failed = set()
    for step in steps:
        blockers = [d for d in DEPENDS_ON.get(step, []) if d in failed]
        if blockers:
            payload = log.result(step, False, skipped=True,
                                 error="skipped because %s failed in this run" % ", ".join(blockers))
            results.append(payload)
            failed.add(step)
            continue
        started = time.time()
        log.info("step %s starting" % step)
        try:
            ok, data = run_step(step)
        except Exception as exc:
            ok = False
            data = {"error": "%s: %s" % (type(exc).__name__, exc), "traceback": traceback.format_exc()}
        data["seconds"] = round(time.time() - started, 2)
        payload = log.result(step, ok, **data)
        results.append(payload)
        if not ok:
            failed.add(step)
    return results


def all_ok(results):
    return all(r.get("ok") for r in results)
