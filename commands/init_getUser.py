import time
from commands.push_get import handle_pushGet
from utils import fieldItemUtils

def handle_getUser(request, user_id, obj, json_data, config_data):
    json_data["uObj"]["current_field"] = json_data["fIds"]["1"]

    # Older saves have babies counted on cages without animal records
    fieldItemUtils.sync_all_cage_animals(json_data, config_data)

    # Run push.get
    handle_pushGet(request, user_id, obj, json_data, config_data)

    obj.update(json_data)