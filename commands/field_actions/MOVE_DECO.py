from utils import roadPathfindingUtils

def handle_moveDeco(request, user_id, obj, json_data, config_data, current_field_id):
    deco = json_data["fObj"]["decos"][str(current_field_id)][str(request["id"])]
    deco["x"] = request["x"]
    deco["y"] = request["y"]

    deco_id = deco["dId"]
    config_data_for_deco = config_data["gameItems"]["decos"][str(deco_id)]

    # Check for nearby roads and set to active if needed
    deco["act"] = int(roadPathfindingUtils.is_building_active(json_data, request["x"], request["y"], config_data_for_deco["width"], config_data_for_deco["height"]))

    # Send objects to game
    if "fObj" not in obj:
        obj["fObj"] = {}
    if "decos" not in obj["fObj"]:
        obj["fObj"]["decos"] = {}
    if current_field_id not in obj["fObj"]["decos"]:
        obj["fObj"]["decos"][current_field_id] = {}
    obj["fObj"]["decos"][current_field_id][str(request["id"])] = deco