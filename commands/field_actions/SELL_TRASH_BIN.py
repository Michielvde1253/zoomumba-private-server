from utils import trashbinUtils
from utils.zooErrors import ZooError, INVALID_REQUEST

# field.fia "sTb": {"id": <trashbin uniqueId>, "cnt": <trash currently in that bin>}
# The client doesn't add the sell price itself, so uObj has to come back.

def handle_sellTrashbin(request, user_id, obj, json_data, config_data, current_field_id):
    field_id = str(current_field_id)
    trashbins = trashbinUtils.get_trashbins(json_data, field_id)
    trashbin = trashbins.get(str(request["id"]))
    if trashbin is None:
        raise ZooError(INVALID_REQUEST, f"no trashbin {request['id']} on field {field_id}")
    config_for_bin = config_data["gameItems"]["trashbins"].get(str(trashbin["tbId"]), {})
    if config_for_bin.get("sellable", 1) != 1:
        raise ZooError(INVALID_REQUEST, f"trashbin {trashbin['tbId']} is not sellable")

    del trashbins[str(request["id"])]
    trashbinUtils.link_road(json_data, field_id, None, None, trashbin["id"])
    json_data["uObj"]["uCv"] += int(config_for_bin.get("sellVirtual", 0))
    json_data["uObj"]["uCr"] += int(config_for_bin.get("sellReal", 0))

    # The trash inside the sold bin is gone
    field = json_data["pfObj"][field_id]
    field["trashbins"] = max(0, field.get("trashbins", 0) - int(request.get("cnt", 0)))
    trashbinUtils.clamp_bin_trash(json_data, config_data, field_id)

    trashbinUtils.send_trashbin(obj, current_field_id, trashbinUtils.deleted_copy(trashbin))
    obj["uObj"] = json_data["uObj"]
    obj["pfObj"] = json_data["pfObj"]
