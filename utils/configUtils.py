"""
Loads the global game configuration (data/global_config_data.json.def) once
and keeps it in memory. It used to be read and parsed from disk on every
ZooApi.php request (7.5 MB of JSON).

The returned dict is shared between requests: treat it as read-only.
"""
import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).parents[1] / "data" / "global_config_data.json.def"
_config = None


def get_config():
    global _config
    if _config is None:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _config = json.load(f)
    return _config
