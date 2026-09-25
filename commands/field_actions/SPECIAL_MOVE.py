from utils import fieldItemUtils as items
from utils.zooErrors import ZooError, INVALID_REQUEST

# field.fia mSB: {"id", "x", "y", "r"} - move or rotate the breeding lab / nursery.
# field.fia sEb: {"id": <entranceBuildings id>, "fId"} - pick the zoo's entrance
#   building (MainBuildingSelectionWindowMediator); stored as pfObj.<fId>.eBuildingId.


def handle_moveSpecial(request, user_id, obj, json_data, config_data, current_field_id):
    special = items.get_item(json_data, "specials", current_field_id, request["id"])
    special.update({"x": request["x"], "y": request["y"], "r": request.get("r", 0)})
    special["act"] = items.building_active(json_data, items.item_config(config_data, "specials", special), special["x"], special["y"])
    items.send_item(obj, "specials", current_field_id, special)


def handle_selectEntranceBuilding(request, user_id, obj, json_data, config_data, current_field_id):
    field_id = str(request.get("fId") or current_field_id)
    field = json_data.get("pfObj", {}).get(field_id)
    building = config_data.get("entranceBuildings", {}).get(str(request["id"]))
    if field is None or building is None:
        raise ZooError(INVALID_REQUEST, f"no entrance building {request['id']} / field {field_id}", resync=("pfObj",))
    if int(building.get("levelRequired", 1)) > json_data["uObj"]["uLvl"]:
        raise ZooError(INVALID_REQUEST, "entrance building needs a higher level", resync=("pfObj",))
    if int(building.get("fType", field.get("fType", 1))) != int(field.get("fType", 1)):
        raise ZooError(INVALID_REQUEST, "entrance building is for another kind of zoo", resync=("pfObj",))
    field["eBuildingId"] = int(request["id"])
    obj["pfObj"] = json_data["pfObj"]
