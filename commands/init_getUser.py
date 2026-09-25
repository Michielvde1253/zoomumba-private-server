import time
from commands.push_get import handle_pushGet
from utils import fieldItemUtils, expansionUtils

def handle_getUser(request, user_id, obj, json_data, config_data):
    json_data["uObj"]["current_field"] = json_data["fIds"]["1"]
    json_data["actFId"] = json_data["fIds"]["1"]

    # Older saves have babies counted on cages without animal records
    fieldItemUtils.sync_all_cage_animals(json_data, config_data)

    # Grid bounds that don't match the zoo size, and missed level expansions
    expansionUtils.repair_fields(json_data, config_data)

    # Run push.get
    handle_pushGet(request, user_id, obj, json_data, config_data)

    obj.update(json_data)