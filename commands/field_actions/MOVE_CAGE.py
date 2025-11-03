from utils import roadPathfindingUtils

def handle_moveCage(request, user_id, obj, json_data, config_data, current_field_id):
    json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]["x"] = request["x"]
    json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]["y"] = request["y"]

    cage_id = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]["cId"]
    config_data_for_cage = config_data["gameItems"]["cages"][str(cage_id)]

    # Check for nearby roads and set to active if needed
    json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]["act"] = int(roadPathfindingUtils.is_building_active(json_data, request["x"], request["y"], config_data_for_cage["width"], config_data_for_cage["height"]))

    # Send objects to game
    obj["req"] = request["req:"] # typo by bigpoint lol
    obj["fObj"] = json_data["fObj"]