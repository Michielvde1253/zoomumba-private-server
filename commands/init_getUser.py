import time
from commands.push_get import handle_pushGet

def handle_getUser(request, user_id, obj, json_data, config_data):
    json_data["uObj"]["current_field"] = json_data["fIds"]["1"]

    # Run push.get
    handle_pushGet(request, user_id, obj, json_data, config_data)

    obj.update(json_data)