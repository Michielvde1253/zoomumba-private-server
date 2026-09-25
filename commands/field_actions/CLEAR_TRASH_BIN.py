import time
from utils import trashbinUtils
from utils.zooErrors import ZooError, INVALID_REQUEST

# field.fia "cTb": {"id": <trashbin uniqueId>, "cnt": <trash the client showed in that bin>}
# The client already added cnt XP and cnt trash resource locally.

def handle_clearTrashbin(request, user_id, obj, json_data, config_data, current_field_id):
    field_id = str(current_field_id)
    trashbin = trashbinUtils.get_trashbins(json_data, field_id).get(str(request["id"]))
    if trashbin is None:
        raise ZooError(INVALID_REQUEST, f"no trashbin {request['id']} on field {field_id}")

    # The client decides how the total bin trash is split over the bins, so we can only
    # check against the total (and never hand out more than there is)
    field = json_data["pfObj"][field_id]
    amount = max(0, min(int(request.get("cnt", 0)), field.get("trashbins", 0)))
    field["trashbins"] -= amount
    trashbin["clean"] = int(time.time())

    trashbinUtils.give_trash_rewards(json_data, amount)

    obj["uObj"] = json_data["uObj"]
    obj["res"] = json_data["res"]
    obj["pfObj"] = json_data["pfObj"]
