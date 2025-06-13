import time
from pathlib import Path
import os
import json

def handle_managementCenterGet(request, user_id, obj, json_data, config_data):
    # Config data can be moved to global_config_data instead of player data?
    obj["managementCenterData"] = json_data["managementCenterData"]
    obj["managementCenterConfig"] = json_data["managementCenterConfig"]