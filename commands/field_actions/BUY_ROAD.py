import time
from utils import roadPathfindingUtils, shopUtils, constantsUtils


def handle_buyRoad(request, user_id, obj, json_data, config_data, current_field_id):
    # Create field object if needed
    if str(current_field_id) not in json_data["fObj"]["roads"]:
        json_data["fObj"]["roads"][str(current_field_id)] = {}

    # Initialize new road
    new_road = constantsUtils.get_empty_road()
    new_road["id"] = json_data["next_object_id"]
    new_road["uId"] = user_id
    new_road["fId"] = current_field_id
    new_road["rId"] = request["rId"]
    new_road["x"] = request["x"]
    new_road["y"] = request["y"]
    new_road["r"] = request["r"]
    new_road["trashbin"] = int(time.time())

    json_data["next_object_id"] += 1
    json_data["fObj"]["roads"][str(current_field_id)][str(new_road["id"])] = new_road

    # Buy item
    config_data_for_road = config_data["gameItems"]["roads"][str(request["rId"])]
    shopUtils.buy_from_shop(config_data_for_road, json_data["uObj"]["uLvl"], json_data)

    # Check all buildings around the road and change them to active if needed:
    roadPathfindingUtils.check_all_buildings_around_tile(json_data, config_data, request["x"], request["y"])

    # Send objects to game
    obj["fObj"] = json_data["fObj"] # To-do: send only modified buildings
    obj["uObj"] = json_data["uObj"]