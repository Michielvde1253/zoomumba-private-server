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
