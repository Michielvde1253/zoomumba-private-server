from utils import shopUtils, resourceUtils
from utils.zooErrors import ZooError, INVALID_REQUEST

def handle_buyResource(request, user_id, obj, json_data, config_data, current_field_id):
    # Buy item
    config_data_for_resource = config_data["gameItems"]["resources"][str(request["irId"])]
    count = int(request["cnt"])
    # Don't charge for units that wouldn't fit in storage
    if count <= 0 or count > resourceUtils.room_for(json_data, request["irId"]):
        raise ZooError(INVALID_REQUEST, f"{count} x resource {request['irId']} doesn't fit in storage", resync=("uObj", "res"))
    shopUtils.buy_multiple_from_shop(config_data_for_resource, json_data["uObj"]["uLvl"], json_data, count)
    resourceUtils.add_resource(json_data, request["irId"], count)

    # Send objects to game
    obj["uObj"] = json_data["uObj"]
    obj["res"] = json_data["res"]