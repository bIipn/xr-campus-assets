"""Logging for the setup steps.

result(step, ok, **data) prints exactly one line 'WTA_RESULT {json}' to stdout (which Unreal routes to
LogPython), and writes a short summary through unreal.log so the editor log shows it too. The summary line
deliberately does not contain 'WTA_RESULT' so a log parser sees each step once.
"""
import json
import sys

try:
    import unreal  # noqa: F401
    _HAVE_UNREAL = True
except ImportError:  # running outside the editor (unit tests)
    _HAVE_UNREAL = False


def _json_default(obj):
    # unreal objects, Names, Vectors: fall back to their string form.
    try:
        return str(obj)
    except Exception:
        return "<unprintable>"


def info(msg):
    text = "[WTA] " + str(msg)
    if _HAVE_UNREAL:
        try:
            unreal.log(text)
            return
        except Exception:
            pass
    print(text)
    sys.stdout.flush()


def warn(msg):
    text = "[WTA] warning: " + str(msg)
    if _HAVE_UNREAL:
        try:
            unreal.log_warning(text)
            return
        except Exception:
            pass
    print(text)
    sys.stdout.flush()


def error(msg):
    text = "[WTA] error: " + str(msg)
    if _HAVE_UNREAL:
        try:
            unreal.log_error(text)
            return
        except Exception:
            pass
    print(text)
    sys.stdout.flush()


def result(step, ok, **data):
    """Print the single machine-readable line for a step and return the payload dict."""
    payload = {"step": step, "ok": bool(ok)}
    payload.update(data)
    line = "WTA_RESULT " + json.dumps(payload, default=_json_default)
    print(line)
    sys.stdout.flush()
    summary = "step %s %s" % (step, "ok" if ok else "FAILED")
    if not ok and data.get("error"):
        summary += ": " + str(data.get("error"))[:300]
    if ok:
        info(summary)
    else:
        error(summary)
    return payload
