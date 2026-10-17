"""Runs the whole wta_setup pipeline against the fake 'unreal' module (Tests/mock_unreal).

This catches Python errors (NameError, bad JSON keys, path bugs) without Unreal. It does not prove that
the real UE 5.8 API names are right; the probe step on the target machine does that.

  python unreal/Tests/test_setup_mock.py            (or: python -m unittest unreal/Tests/test_setup_mock.py)
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
UNREAL_DIR = os.path.dirname(HERE)
PROJECT_DIR = os.path.join(UNREAL_DIR, "WalkTheArchive")
MOCK_DIR = os.path.join(HERE, "mock_unreal")
PYTHON_DIR = os.path.join(PROJECT_DIR, "Content", "Python")
ENTRY = os.path.join(PROJECT_DIR, "Scripts", "setup_project.py")
STEPS = ["probe", "import_meshes", "import_art", "data_tables", "build_level", "lighting", "actors",
         "navmesh", "project_settings", "verify"]


def make_scratch_project():
    """A throw-away project folder with a copy of Data/ so no run touches the real Config or Content."""
    root = tempfile.mkdtemp(prefix="wta_mock_")
    proj = os.path.join(root, "WalkTheArchive")
    os.makedirs(os.path.join(proj, "Data"))
    for src in glob.glob(os.path.join(PROJECT_DIR, "Data", "*.json")):
        shutil.copy(src, os.path.join(proj, "Data", os.path.basename(src)))
    return root, proj


def parse_results(stdout):
    results = []
    for line in stdout.splitlines():
        if line.startswith("WTA_RESULT "):
            results.append(json.loads(line[len("WTA_RESULT "):]))
    return results


def real_content_snapshot():
    """(file count, newest mtime) under the real Content/WTA; None before the first real setup run."""
    root = os.path.join(PROJECT_DIR, "Content", "WTA")
    if not os.path.isdir(root):
        return None
    count, newest = 0, 0.0
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            count += 1
            newest = max(newest, os.path.getmtime(os.path.join(dirpath, name)))
    return count, newest


class SetupPipelineMockTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root, cls.proj = make_scratch_project()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def run_entry(self, extra_env=None):
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([MOCK_DIR, PYTHON_DIR])
        env["WTA_PROJECT_DIR"] = self.proj
        env.pop("WTA_STEPS", None)
        env.pop("WTA_MOCK_NO_CPP", None)
        env.update(extra_env or {})
        proc = subprocess.run([sys.executable, "-B", ENTRY], env=env, capture_output=True, text=True)
        return proc, parse_results(proc.stdout)

    def test_1_all_steps_ok(self):
        before = real_content_snapshot()
        proc, results = self.run_entry()
        self.assertEqual([r["step"] for r in results], STEPS, "one WTA_RESULT line per step, in contract order\n" + proc.stdout + proc.stderr)
        self.assertEqual(proc.stdout.count("WTA_RESULT "), len(STEPS), "exactly one WTA_RESULT per step")
        for r in results:
            self.assertTrue(r["ok"], "step %s failed: %s\n%s" % (r["step"], r.get("error"), r.get("traceback", "")))
        self.assertEqual(proc.returncode, 0, proc.stderr[-3000:])
        by_step = {r["step"]: r for r in results}
        # The mock imports one StaticMesh per GLB mesh, so the counts must match the manifest.
        with open(os.path.join(UNREAL_DIR, "Pipeline", "out", "ue", "manifest.json")) as fh:
            manifest = json.load(fh)
        for asset, spec in manifest["assets"].items():
            self.assertEqual(by_step["import_meshes"]["assets"][asset]["meshes"], spec["meshes"], asset)
        self.assertEqual(by_step["import_art"]["imported"], 16)
        self.assertEqual(len(by_step["data_tables"]["tables"]), 17)
        for name, entry in by_step["data_tables"]["tables"].items():
            self.assertEqual(entry["table_rows"], entry["json_rows"], name)
        self.assertEqual(by_step["actors"]["exhibits"], 28)
        self.assertEqual(by_step["actors"]["rooms"], 15)
        self.assertEqual(by_step["actors"]["books"], 15, by_step["actors"].get("books_skipped"))
        self.assertEqual(by_step["actors"]["tokens_from_mesh"], 11)
        self.assertEqual(by_step["lighting"]["art_spots"], 16)
        self.assertEqual(by_step["lighting"]["stage_spots"], 12)
        self.assertTrue(by_step["verify"]["level_umap"])
        token_check = by_step["verify"]["token_check"]
        self.assertEqual(len(token_check), 11, token_check)
        for name, chk in token_check.items():
            self.assertIn("distance_cm", chk, name)
            if not chk["gated"]:
                self.assertLess(chk["distance_cm"], 1.0, name)   # static tokens match the rows exactly
        self.assertTrue(token_check["t-coaster"]["gated"])
        # The ini edits landed in the scratch project, not the real one.
        with open(os.path.join(self.proj, "Config", "DefaultEngine.ini")) as fh:
            ini = fh.read()
        self.assertIn("GameDefaultMap=/Game/WTA/Maps/L_Campus.L_Campus", ini)
        self.assertIn("GlobalDefaultGameMode=/Script/WalkTheArchive.WTAGameMode", ini)
        self.assertIn("RuntimeGeneration=Dynamic", ini)
        with open(os.path.join(self.proj, "Config", "DefaultGame.ini")) as fh:
            game_ini = fh.read()
        self.assertIn("Exhibits=/Game/WTA/Data/DT_Exhibits.DT_Exhibits", game_ini)
        # The mock writes only to the scratch project; a real setup run may already have filled Content/WTA.
        self.assertEqual(real_content_snapshot(), before, "real Content folder untouched")

    def test_2_step_subset_and_failure_semantics(self):
        proc, results = self.run_entry({"WTA_STEPS": "probe, project_settings"})
        self.assertEqual([r["step"] for r in results], ["probe", "project_settings"])
        self.assertTrue(all(r["ok"] for r in results))
        self.assertEqual(proc.returncode, 0)

        # Without the C++ module the probe fails, dependants are skipped and the script exits non-zero.
        proc, results = self.run_entry({"WTA_MOCK_NO_CPP": "1", "WTA_STEPS": "probe,data_tables,project_settings"})
        by_step = {r["step"]: r for r in results}
        self.assertFalse(by_step["probe"]["ok"])
        self.assertFalse(by_step["data_tables"]["ok"])
        self.assertTrue(by_step["data_tables"].get("skipped"))
        self.assertTrue(by_step["project_settings"]["ok"])
        self.assertNotEqual(proc.returncode, 0)

        proc, results = self.run_entry({"WTA_STEPS": "nonsense"})
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("unknown steps", proc.stdout)

    def test_3_idempotent_in_process(self):
        """Running every step twice in one editor session spawns nothing twice."""
        os.environ["WTA_PROJECT_DIR"] = self.proj
        os.environ["WTA_SHOTS"] = "0"
        for p in (MOCK_DIR, PYTHON_DIR):
            if p not in sys.path:
                sys.path.insert(0, p)
        import unreal  # the mock
        unreal._reset()
        import io
        import contextlib
        from wta_setup import pipeline

        def run_all():
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                pipeline.run(STEPS)
            return parse_results(buf.getvalue())

        first = run_all()
        second = run_all()
        for r in first + second:
            self.assertTrue(r["ok"], "%s: %s\n%s" % (r["step"], r.get("error"), r.get("traceback", "")))
        a1 = {r["step"]: r for r in first}["verify"]["actors"]
        a2 = {r["step"]: r for r in second}["verify"]["actors"]
        self.assertEqual(a1, a2, "actor counts changed on the second run")
        self.assertEqual(a2["StaticMeshActor"]["actual"], 798)
        self.assertEqual({r["step"]: r for r in second}["import_meshes"]["skipped"], 9)
        self.assertGreater({r["step"]: r for r in second}["build_level"]["removed_previous"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
