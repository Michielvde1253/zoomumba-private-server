import time
from utils import shopUtils
from utils.trashbinUtils import link_road
from utils.zooErrors import ZooError, INVALID_REQUEST

# field.fia "bTb": {"tbId": <trashbin item id>, "x", "y", "r", "cR"}
# Trashbins are 1x1 items the client only lets you drop on a road tile.
# Wire format (from the zoomumba.com capture):
#   {"id", "uId", "fId", "tbId", "act", "x", "y", "r", "clean"}   (no "build")

def handle_buyTrashbin(request, user_id, obj, json_data, config_data, current_field_id):
    field_id = str(current_field_id)
    config_data_for_trashbin = config_data["gameItems"]["trashbins"].get(str(request["tbId"]))
    if config_data_for_trashbin is None:
        raise ZooError(INVALID_REQUEST, f"unknown trashbin {request['tbId']}")

    # Pay first (raises ZooError if the player can't afford it)
    shopUtils.buy_from_shop(config_data_for_trashbin, json_data["uObj"]["uLvl"], json_data)

    new_trashbin = {
        "id": json_data["next_object_id"],
        "uId": user_id,
        "fId": current_field_id,
        "tbId": request["tbId"],
        "act": 1,
        "x": request["x"],
        "y": request["y"],
        "r": request.get("r", 0),
        "clean": int(time.time()),
    }
    json_data["next_object_id"] += 1
    trashbins = json_data["fObj"].setdefault("trashbins", {}).setdefault(field_id, {})
    trashbins[str(new_trashbin["id"])] = new_trashbin

    link_road(json_data, field_id, request["x"], request["y"], new_trashbin["id"])

    # Send the new trashbin to the game (fObj.trashbins.<fieldId>.<uniqueId>)
    obj.setdefault("fObj", {}).setdefault("trashbins", {}).setdefault(current_field_id, {})[str(new_trashbin["id"])] = new_trashbin
    obj["uObj"] = json_data["uObj"]

