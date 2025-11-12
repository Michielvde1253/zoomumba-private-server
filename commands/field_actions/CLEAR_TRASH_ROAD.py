def handle_clearTrashRoad(request, user_id, obj, json_data, config_data, current_field_id):
    json_data["pfObj"][current_field_id]["trashroads"] -= request["cnt"]
    if json_data["pfObj"][current_field_id]["trashroads"] < 0:
        # To-do: disconnect for cheat
        pass