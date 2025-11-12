import time
from utils import constantsUtils, roadPathfindingUtils, shopUtils

def handle_buyCage(request, user_id, obj, json_data, config_data, current_field_id):
    # Create field object if needed
    if str(current_field_id) not in json_data["fObj"]["cages"]:
        json_data["fObj"]["cages"][str(current_field_id)] = {}

    # Initialize new cage
    new_cage = constantsUtils.get_empty_cage()
    new_cage["id"] = json_data["next_object_id"]
    new_cage["uId"] = user_id
    new_cage["fId"] = current_field_id
    new_cage["cId"] = request["cId"]
    new_cage["x"] = request["x"]
    new_cage["y"] = request["y"]
    new_cage["r"] = request["r"]
    new_cage["build"] = int(time.time()) + 10

    json_data["next_object_id"] += 1
    json_data["fObj"]["cages"][str(current_field_id)][str(new_cage["id"])] = new_cage

    # Buy item
    config_data_for_cage = config_data["gameItems"]["cages"][str(request["cId"])]
    shopUtils.buy_from_shop(config_data_for_cage, json_data["uObj"]["uLvl"], json_data)

    # Check for nearby roads and set to active if needed
    json_data["fObj"]["cages"][str(current_field_id)][str(new_cage["id"])]["act"] = int(roadPathfindingUtils.is_building_active(json_data, request["x"], request["y"], config_data_for_cage["width"], config_data_for_cage["height"]))

    # Send objects to game
    if "fObj" not in obj:
        obj["fObj"] = {}
    if "cages" not in obj["fObj"]:
        obj["fObj"]["cages"] = {}
    if current_field_id not in obj["fObj"]["cages"]:
        obj["fObj"]["cages"][current_field_id] = {}
    obj["fObj"]["cages"][current_field_id][str(new_cage["id"])] = json_data["fObj"]["cages"][str(current_field_id)][str(new_cage["id"])]
    obj["uObj"] = json_data["uObj"]