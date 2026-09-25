from utils.zooErrors import ZooError, INVALID_REQUEST
from utils.trashbinUtils import link_road

# field.fia "mTb": {"id": <trashbin uniqueId>, "x", "y", "r"}

def handle_moveTrashbin(request, user_id, obj, json_data, config_data, current_field_id):
    field_id = str(current_field_id)
    trashbin = json_data["fObj"].get("trashbins", {}).get(field_id, {}).get(str(request["id"]))
    if trashbin is None:
        raise ZooError(INVALID_REQUEST, f"no trashbin {request['id']} on field {field_id}")

    trashbin["x"] = request["x"]
    trashbin["y"] = request["y"]
    trashbin["r"] = request.get("r", 0)
    link_road(json_data, field_id, request["x"], request["y"], trashbin["id"])

    obj.setdefault("fObj", {}).setdefault("trashbins", {}).setdefault(current_field_id, {})[str(request["id"])] = trashbin
