"""Step 4: create /Game/WTA/Data/DT_<Table> for every row struct in contract/structs.json and fill it from
WalkTheArchive/Data/<File>.json. Existing tables are refilled in place (whole-table replace), so the step
is idempotent. Reports row counts against the JSON row counts.
"""
import json
import os

import unreal

from . import log
from . import paths
from . import util

STEP = "data_tables"


def row_tables():
    """[(struct_name, table_name, json_file), ...] from structs.json, in file order."""
    structs = paths.read_json(paths.STRUCTS_JSON).get("structs", {})
    out = []
    for struct_name, spec in structs.items():
        if spec.get("row") and spec.get("table") and spec.get("file"):
            out.append((struct_name, spec["table"], spec["file"]))
    return out


def get_or_create_table(table_name, row_struct):
    assets = util.assets()
    path = paths.table_asset_path(table_name)
    if assets.exists(path):
        dt = assets.load(path)
        if dt is not None:
            return dt, "existed"
    factory = unreal.DataTableFactory()
    factory.set_editor_property("struct", row_struct)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    dt = tools.create_asset(table_name, paths.DATA_PATH, unreal.DataTable, factory)
    if dt is None:
        raise RuntimeError("create_asset failed for " + path)
    return dt, "created"


def fill_from_json(dt, json_text):
    """Returns (ok, problems). Handles both return conventions: bool, or a list of problem strings."""
    res = unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(dt, json_text)
    if isinstance(res, bool):
        return res, []
    if res is None:
        return True, []
    try:
        problems = [str(p) for p in list(res)]
        return len(problems) == 0, problems
    except TypeError:
        return bool(res), []


def row_names(dt):
    try:
        return [str(n) for n in unreal.DataTableFunctionLibrary.get_data_table_row_names(dt)]
    except Exception:
        pass
    try:
        return [str(n) for n in dt.get_row_names()]
    except Exception:
        return []


def run():
    util.wait_for_asset_registry()
    assets = util.assets()
    if not assets.directory_exists(paths.DATA_PATH):
        assets.make_directory(paths.DATA_PATH)
    report = {"tables": {}, "created": 0, "existed": 0, "errors": []}

    for struct_name, table_name, json_file in row_tables():
        entry = {"struct": struct_name, "file": json_file, "asset": paths.table_asset_path(table_name)}
        report["tables"][table_name] = entry
        json_path = os.path.join(paths.DATA_DIR, json_file)
        try:
            rows = paths.read_json(json_path)
        except Exception as exc:
            entry["error"] = "json unreadable: %s" % exc
            report["errors"].append("%s: %s" % (table_name, entry["error"]))
            continue
        if not isinstance(rows, list):
            entry["error"] = "json is not a list of rows"
            report["errors"].append("%s: %s" % (table_name, entry["error"]))
            continue
        entry["json_rows"] = len(rows)

        row_struct = util.load_wta_struct(struct_name)
        if row_struct is None:
            entry["error"] = "struct %s not found in the C++ module" % paths.script_struct(struct_name)
            report["errors"].append("%s: %s" % (table_name, entry["error"]))
            continue
        try:
            dt, state = get_or_create_table(table_name, row_struct)
        except Exception as exc:
            entry["error"] = "create failed: %s" % exc
            report["errors"].append("%s: %s" % (table_name, entry["error"]))
            continue
        entry["status"] = state
        report[state] += 1

        try:
            ok, problems = fill_from_json(dt, json.dumps(rows, ensure_ascii=False))
        except Exception as exc:
            ok, problems = False, [str(exc)]
        names = row_names(dt)
        entry["table_rows"] = len(names)
        if problems:
            entry["problems"] = problems[:20]
        if not ok and len(names) == len(rows) and len(rows) > 0:
            # The fill reported problems but every row landed: keep going, surface the messages.
            ok = True
            entry["warning"] = "fill reported problems but all rows are present"
        if not ok:
            entry["error"] = "fill failed: %s" % ("; ".join(problems)[:300] or "returned False")
            report["errors"].append("%s: %s" % (table_name, entry["error"]))
        elif len(names) != len(rows):
            entry["error"] = "row count %d != json rows %d" % (len(names), len(rows))
            report["errors"].append("%s: %s" % (table_name, entry["error"]))
        assets.save(dt)

    assets.save_directory(paths.DATA_PATH, only_if_dirty=True, recursive=True)
    report["ok"] = not report["errors"] and bool(report["tables"])
    if report["errors"]:
        report["error"] = "; ".join(report["errors"])[:1000]
    elif not report["tables"]:
        report["error"] = "no row structs found in " + paths.STRUCTS_JSON
    return report
