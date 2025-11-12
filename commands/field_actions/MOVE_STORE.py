from utils import roadPathfindingUtils

def handle_moveStore(request, user_id, obj, json_data, config_data, current_field_id):
    store = json_data["fObj"]["stores"][str(current_field_id)][str(request["id"])]
    store["x"] = request["x"]
    store["y"] = request["y"]

    store_id = store["stId"]
    config_data_for_store = config_data["gameItems"]["stores"][str(store_id)]

    # Check for nearby roads and set to active if needed
    store["act"] = int(roadPathfindingUtils.is_building_active(json_data, request["x"], request["y"], config_data_for_store["width"], config_data_for_store["height"]))

    # Send objects to game
    if "fObj" not in obj:
        obj["fObj"] = {}
    if "stores" not in obj["fObj"]:
        obj["fObj"]["stores"] = {}
    if current_field_id not in obj["fObj"]["stores"]:
        obj["fObj"]["stores"][current_field_id] = {}
    obj["fObj"]["stores"][current_field_id][str(request["id"])] = store