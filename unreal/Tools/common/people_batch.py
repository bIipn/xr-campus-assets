#!/usr/bin/env python3
"""Build many MetaHumans unattended: a fresh editor per small batch, because each MetaHuman being
edited holds a few GB and a 16 GB machine runs out of memory after a handful in one session.

Usage (engine Python):
  python Tools/common/people_batch.py --steps look --batch 3                 # every person in people.json
  python Tools/common/people_batch.py --steps rig,textures,save --batch 3 --skip margaret
  python Tools/common/people_batch.py --steps build,idle,save --batch 1 --ids margaret,rosa
  python Tools/common/people_batch.py --steps all --batch 1 --role wax

For each batch it writes Saved/Config/WindowsEditor/Engine.ini (Python Remote Execution, localhost
only), starts UnrealEditor on the project, waits for it to answer, runs wta_people.build.run(...)
through Remote Execution, saves, and closes the editor. Stops when a cloud step reports that the
Epic sign-in is needed. Progress: Saved/Logs/people_batch.log and one PEOPLE_BATCH line per batch.
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import find_engine  # noqa: E402

PROJECT_DIR = os.path.join(os.path.dirname(os.path.dirname(HERE)), "WalkTheArchive")
UPROJECT = os.path.join(PROJECT_DIR, "WalkTheArchive.uproject")
SPEC = os.path.join(PROJECT_DIR, "Content", "Python", "wta_people", "people.json")
RX_INI = os.path.join(PROJECT_DIR, "Saved", "Config", "WindowsEditor", "Engine.ini")
LOG = os.path.join(PROJECT_DIR, "Saved", "Logs", "people_batch.log")
RX_SECTION = ("[/Script/PythonScriptPlugin.PythonScriptPluginSettings]\r\nbRemoteExecution=True\r\n"
              "RemoteExecutionMulticastBindAddress=127.0.0.1\r\nRemoteExecutionMulticastTtl=0\r\n")


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def engine_paths():
    root, _, checked = find_engine.find_engine()
    if not root:
        raise SystemExit("Unreal Engine 5.8 not found (checked %s)" % checked)
    editor = os.path.join(root, "Engine", "Binaries", "Win64", "UnrealEditor.exe")
    rx_dir = os.path.join(root, "Engine", "Plugins", "Experimental", "PythonScriptPlugin", "Content", "Python")
    return editor, rx_dir


def ensure_remote_execution_ini():
    """The editor drops this file's section after it starts, so write it before every launch."""
    os.makedirs(os.path.dirname(RX_INI), exist_ok=True)
    text = ""
    if os.path.exists(RX_INI):
        with open(RX_INI, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    if "bRemoteExecution=True" not in text:
        with open(RX_INI, "a", encoding="utf-8", newline="") as fh:
            fh.write(("\r\n" if text and not text.endswith("\n") else "") + RX_SECTION)


def editor_running():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq UnrealEditor.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    return "UnrealEditor.exe" in out


def find_node(remote, wait_s, proc=None):
    """The editor's Remote Execution node; None after wait_s, or at once if the editor process has ended."""
    t0 = time.time()
    while time.time() - t0 < wait_s:
        for node in remote.remote_nodes:
            if "WalkTheArchive" in json.dumps(node):
                return node
        if proc is not None and proc.poll() is not None:
            return None
        time.sleep(1.0)
    return None


def run_batch(rx, editor, ids, steps, startup_timeout):
    ensure_remote_execution_ini()
    proc = subprocess.Popen([editor, UPROJECT], cwd=PROJECT_DIR)
    log("editor started (pid %d) for %s" % (proc.pid, ",".join(ids)))
    remote = rx.RemoteExecution(rx.RemoteExecutionConfig())
    remote.start()
    results, signin = {}, False
    try:
        node = find_node(remote, startup_timeout, proc)
        if node is None:
            if proc.poll() is not None:
                log("editor exited during startup (exit code %s)" % proc.returncode)
            else:
                log("editor did not answer within %ds" % startup_timeout)
            return results, False, proc
        remote.open_command_connection(node["node_id"])
        cmd = ("import importlib, json, wta_people.build as b; importlib.reload(b); "
               "r = b.run(%s, steps=%r); print('BATCH_RESULT ' + json.dumps(r))" % (json.dumps(ids), steps))
        res = remote.run_command(cmd, unattended=True, exec_mode=rx.MODE_EXEC_STATEMENT, raise_on_failure=False)
        for entry in res.get("output", []) or []:
            text = str(entry.get("output", "")).rstrip()
            if text.startswith("WTA_PEOPLE") or text.startswith("BATCH_RESULT"):
                log("  " + text[:400])
            if text.startswith("BATCH_RESULT "):
                results = json.loads(text[len("BATCH_RESULT "):])
            if "Epic sign-in needed" in text:
                signin = True
        remote.run_command("unreal.SystemLibrary.quit_editor()", unattended=True,
                           exec_mode=rx.MODE_EXEC_STATEMENT, raise_on_failure=False)
    finally:
        remote.stop()
    return results, signin, proc


def close_editor(proc, wait_s=45):
    try:
        proc.wait(timeout=wait_s)
    except subprocess.TimeoutExpired:
        log("editor still open after %ds; ending it (everything was saved)" % wait_s)
        proc.kill()
        proc.wait(timeout=30)
    # a crash leaves the crash reporter open; it holds nothing we need
    subprocess.run(["taskkill", "/F", "/IM", "CrashReportClientEditor.exe"], capture_output=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", default="look")
    ap.add_argument("--batch", type=int, default=3)
    ap.add_argument("--ids", default="")
    ap.add_argument("--role", default="")
    ap.add_argument("--skip", default="", help="ids to leave out")
    ap.add_argument("--startup-timeout", type=int, default=600)
    a = ap.parse_args()
    if editor_running():
        raise SystemExit("Close the Unreal Editor first (this tool starts its own).")
    with open(SPEC, encoding="utf-8") as fh:
        people = json.load(fh)["people"]
    all_ids = [p["id"] for p in people]
    ids = [p["id"] for p in people if (not a.role or p.get("role") == a.role)]
    if a.ids:
        ids = [s.strip() for s in a.ids.split(",") if s.strip() in all_ids]
    skip = {s.strip() for s in a.skip.split(",") if s.strip()}
    ids = [i for i in ids if i not in skip]
    editor, rx_dir = engine_paths()
    sys.path.insert(0, rx_dir)
    import remote_execution as rx  # noqa: E402
    done, failed = [], []
    log("people_batch: %d people, steps=%s, batch=%d" % (len(ids), a.steps, a.batch))
    for i in range(0, len(ids), a.batch):
        chunk = ids[i:i + a.batch]
        results, signin, proc = run_batch(rx, editor, chunk, a.steps, a.startup_timeout)
        close_editor(proc)
        if not results and not signin:
            # no result at all: the editor crashed (5.8 sometimes asserts while starting); one more try
            log("no result for %s; starting a fresh editor once more" % ",".join(chunk))
            results, signin, proc = run_batch(rx, editor, chunk, a.steps, a.startup_timeout)
            close_editor(proc)
        for pid in chunk:
            (done if results.get(pid) else failed).append(pid)
        log("PEOPLE_BATCH %s" % json.dumps({"batch": chunk, "results": results}))
        if signin:
            log("STOPPED: the Epic sign-in is needed (open the editor, sign in, then rerun)")
            break
    log("people_batch done: ok=%d failed=%d %s" % (len(done), len(failed), ",".join(failed)))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
