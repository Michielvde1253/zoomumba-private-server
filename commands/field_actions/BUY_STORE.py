import time
from utils import roadPathfindingUtils, shopUtils, constantsUtils

def handle_buyStore(request, user_id, obj, json_data, config_data, current_field_id):
    # Create field object if needed
    if str(current_field_id) not in json_data["fObj"]["stores"]:
        json_data["fObj"]["stores"][str(current_field_id)] = {}

    # Initialize new store
    new_store = constantsUtils.get_empty_store()
    new_store["id"] = json_data["next_object_id"]
    new_store["uId"] = user_id
    new_store["fId"] = current_field_id
    new_store["stId"] = request["stId"]
    new_store["x"] = request["x"]
    new_store["y"] = request["y"]
    new_store["r"] = request["r"]
    new_store["build"] = int(time.time()) + 10
    new_store["collect"] = int(time.time()) + 10

    json_data["next_object_id"] += 1
    json_data["fObj"]["stores"][str(current_field_id)][str(new_store["id"])] = new_store

    # Buy item
    config_data_for_store = config_data["gameItems"]["stores"][str(request["stId"])]
    shopUtils.buy_from_shop(config_data_for_store, json_data["uObj"]["uLvl"], json_data)

    # Check for nearby roads and set to active if needed
    json_data["fObj"]["stores"][str(current_field_id)][str(new_store["id"])]["act"] = int(roadPathfindingUtils.is_building_active(json_data, request["x"], request["y"], config_data_for_store["width"], config_data_for_store["height"]))

    # Send objects to game
    if "fObj" not in obj:
        obj["fObj"] = {}
    if "stores" not in obj["fObj"]:
        obj["fObj"]["stores"] = {}
    if current_field_id not in obj["fObj"]["stores"]:
        obj["fObj"]["stores"][current_field_id] = {}
    obj["fObj"]["stores"][current_field_id][str(new_store["id"])] = json_data["fObj"]["stores"][str(current_field_id)][str(new_store["id"])]
    obj["uObj"] = json_data["uObj"]