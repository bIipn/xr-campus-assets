"""The client pack the builders draw their words from: the folder WTA_CLIENT names (a campus.json in it), else
clients/xrlibraries. pack() returns the json; get(path, default) walks it ('app.title')."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_PACK = None


def folder():
    return os.environ.get('WTA_CLIENT') or os.path.join(ROOT, 'clients', 'xrlibraries')


def pack():
    global _PACK
    if _PACK is None:
        path = os.path.join(folder(), 'campus.json')
        with open(path, 'r', encoding='utf-8') as fh:
            _PACK = json.load(fh)
    return _PACK


def get(path, default=None):
    node = pack()
    for key in path.split('.'):
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node
