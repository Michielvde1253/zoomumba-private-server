from utils import shopUtils

def handle_buyResource(request, user_id, obj, json_data, config_data, current_field_id):
    # Buy item
    config_data_for_resource = config_data["gameItems"]["resources"][str(request["irId"])]
    shopUtils.buy_multiple_from_shop(config_data_for_resource, json_data["uObj"]["uLvl"], json_data, request["cnt"])
    json_data["res"][str(request["irId"])]["cnt"] += request["cnt"]

    # Send objects to game
    obj["uObj"] = json_data["uObj"]
    obj["res"] = json_data["res"]