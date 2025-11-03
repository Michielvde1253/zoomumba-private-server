from utils import roadPathfindingUtils


def handle_moveRoad(request, user_id, obj, json_data, config_data, current_field_id):
    json_data["fObj"]["roads"][str(current_field_id)][str(request["id"])]["x"] = request["x"]
    json_data["fObj"]["roads"][str(current_field_id)][str(request["id"])]["y"] = request["y"]

    # Check all buildings around the road and change them to active if needed:
    roadPathfindingUtils.check_all_buildings_around_tile(json_data, config_data, request["x"], request["y"])

    # Send objects to game
    obj["req"] = request["req:"] # typo by bigpoint lol
    obj["fObj"] = json_data["fObj"]