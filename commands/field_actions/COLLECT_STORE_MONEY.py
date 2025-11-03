import time

def handle_collectStoreMoney(request, user_id, obj, json_data, config_data, current_field_id):
    # the fTime in player json seems to be unused?

    store = json_data["fObj"]["stores"][str(current_field_id)][str(request["id"])]
    store_id = store["stId"]
    
    config_data_for_store = config_data["gameItems"]["stores"][str(store_id)]

    if(int(time.time()) >= store["collect"]):
        store["collect"] = int(time.time()) + config_data_for_store["collectTime"]
        json_data["uObj"]["uCv"] += config_data_for_store["collectVirtual"]

    # Send objects to game
    obj["req"] = request["req:"] # typo by bigpoint lol
    obj["uObj"] = json_data["uObj"]
    obj["fObj"] = json_data["fObj"]