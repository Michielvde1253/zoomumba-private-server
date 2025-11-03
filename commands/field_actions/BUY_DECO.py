import time
from utils import roadPathfindingUtils, shopUtils, constantsUtils


def handle_buyDeco(request, user_id, obj, json_data, config_data, current_field_id):
    # Create field object if needed
    if str(current_field_id) not in json_data["fObj"]["decos"]:
        json_data["fObj"]["decos"][str(current_field_id)] = {}

    # Initialize new road
    new_deco = constantsUtils.get_empty_deco()
    new_deco["id"] = json_data["next_object_id"]
    new_deco["uId"] = user_id
    new_deco["fId"] = current_field_id
    new_deco["dId"] = request["dId"]
    new_deco["x"] = request["x"]
    new_deco["y"] = request["y"]
    new_deco["r"] = request["r"]
    new_deco["build"] = int(time.time()) + 10

    json_data["next_object_id"] += 1
    json_data["fObj"]["decos"][str(current_field_id)][str(new_deco["id"])] = new_deco

    # Buy item
    config_data_for_deco = config_data["gameItems"]["decos"][str(request["dId"])]
    shopUtils.buy_from_shop(config_data_for_deco, json_data["uObj"]["uLvl"], json_data)

    # Check for nearby roads and set to active if needed
    json_data["fObj"]["decos"][str(current_field_id)][str(new_deco["id"])]["act"] = int(roadPathfindingUtils.is_building_active(json_data, request["x"], request["y"], config_data_for_deco["width"], config_data_for_deco["height"]))

    # Send objects to game
    obj["fObj"] = json_data["fObj"]
    obj["req"] = request["req:"] # typo by bigpoint lol
    obj["uObj"] = json_data["uObj"]