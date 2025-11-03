def handle_collectEntranceFee(request, user_id, obj, json_data, config_data, current_field_id):
    json_data["uObj"]["uCv"] += json_data["uObj"]["entranceFee"]
    json_data["uObj"]["entranceFee"] = 0

    # Send objects to game
    obj["req"] = request["req:"] # typo by bigpoint lol
    obj["uObj"] = json_data["uObj"]