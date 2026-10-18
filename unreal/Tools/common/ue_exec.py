#!/usr/bin/env python3
"""Run Python inside an open Unreal Editor through Python Remote Execution.

Used for editor work that needs a live, signed-in editor (MetaHuman auto-rig and texture
downloads go through Epic's servers), which the headless setup run cannot do.

Usage (any Python 3.8+, e.g. the engine's bundled python.exe):
  python ue_exec.py file <script.py> [args...]   run a file (sys.argv = [script, args...])
  python ue_exec.py stmt "<statement>"           exec one statement (use ; for several)
  python ue_exec.py eval "<expression>"          print the value of one expression

The editor must have Remote Execution on: Project Settings > Plugins > Python > Enable Remote
Execution, or in Saved/Config/WindowsEditor/Engine.ini (local only, bind 127.0.0.1, TTL 0):
  [/Script/PythonScriptPlugin.PythonScriptPluginSettings]
  bRemoteExecution=True
  RemoteExecutionMulticastBindAddress=127.0.0.1
  RemoteExecutionMulticastTtl=0

Prints the editor's log lines, then one line: UE_EXEC_RESULT {"success", "result", "seconds",
"project"}. Exit codes: 0 ok, 1 the command raised, 2 bad usage, 3 no editor answered.
The call blocks until the command finishes (the editor UI is busy meanwhile).
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import find_engine  # noqa: E402

PROJECT = "WalkTheArchive"


def load_remote_execution():
    root, _, checked = find_engine.find_engine()
    if not root:
        raise SystemExit("UE_EXEC_NO_ENGINE: Unreal Engine 5.8 not found (checked %s)" % checked)
    rx_dir = os.path.join(root, "Engine", "Plugins", "Experimental", "PythonScriptPlugin", "Content", "Python")
    sys.path.insert(0, rx_dir)
    import remote_execution  # noqa: E402
    return remote_execution


def find_node(remote, wait_s=15.0):
    """The editor node whose project is WalkTheArchive, else the first editor that answers."""
    t0 = time.time()
    while time.time() - t0 < wait_s:
        for node in remote.remote_nodes:
            if PROJECT in json.dumps(node):
                return node
        time.sleep(0.25)
    nodes = remote.remote_nodes
    return nodes[0] if nodes else None


def main(argv):
    if len(argv) < 3 or argv[1] not in ("file", "stmt", "eval"):
        print(__doc__)
        return 2
    rx = load_remote_execution()
    mode, payload = argv[1], argv[2]
    if mode == "file":
        script = os.path.abspath(payload)
        extra = " ".join('"%s"' % a for a in argv[3:])
        payload = ('"%s" %s' % (script, extra)).strip()
        exec_mode = rx.MODE_EXEC_FILE
    elif mode == "stmt":
        exec_mode = rx.MODE_EXEC_STATEMENT
    else:
        exec_mode = rx.MODE_EVAL_STATEMENT

    remote = rx.RemoteExecution(rx.RemoteExecutionConfig())
    remote.start()
    try:
        node = find_node(remote)
        if node is None:
            print("UE_EXEC_NO_EDITOR: no editor answered (is it open with Remote Execution enabled?)")
            return 3
        remote.open_command_connection(node["node_id"])
        t0 = time.time()
        result = remote.run_command(payload, unattended=True, exec_mode=exec_mode, raise_on_failure=False)
        for entry in result.get("output", []) or []:
            text = str(entry.get("output", "")).rstrip()
            if text:
                print("[%s] %s" % (entry.get("type", "?"), text))
        print("UE_EXEC_RESULT " + json.dumps({
            "success": bool(result.get("success")),
            "result": result.get("result"),
            "seconds": round(time.time() - t0, 1),
            "project": node.get("project_name"),
        }))
        return 0 if result.get("success") else 1
    finally:
        remote.stop()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
