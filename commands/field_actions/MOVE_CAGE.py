from utils import roadPathfindingUtils

def handle_moveCage(request, user_id, obj, json_data, config_data, current_field_id):
    cage = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]
    cage["x"] = request["x"]
    cage["y"] = request["y"]

    cage_id = cage["cId"]
    config_data_for_cage = config_data["gameItems"]["cages"][str(cage_id)]

    # Check for nearby roads and set to active if needed
    cage["act"] = int(roadPathfindingUtils.is_building_active(json_data, request["x"], request["y"], config_data_for_cage["width"], config_data_for_cage["height"]))

    # Send objects to game
    if "fObj" not in obj:
        obj["fObj"] = {}
    if "cages" not in obj["fObj"]:
        obj["fObj"]["cages"] = {}
    if current_field_id not in obj["fObj"]["cages"]:
        obj["fObj"]["cages"][current_field_id] = {}
    obj["fObj"]["cages"][current_field_id][str(request["id"])] = cage