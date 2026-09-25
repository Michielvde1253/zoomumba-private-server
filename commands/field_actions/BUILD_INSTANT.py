from utils import shopUtils, fieldItemUtils as items
from utils.zooErrors import ZooError, INVALID_REQUEST

# field.fia bdC / bdD / bdSt: {"id": <uniqueId>} - finish building a cage /
# deco / store right away for its directBuildReal (the client takes the real
# currency and sets the build time to 0 itself).

KEYS = {"bdC": "cages", "bdD": "decos", "bdSt": "stores"}


def handle_buildInstant(request, user_id, obj, json_data, config_data, current_field_id):
    key = KEYS[request["fia"]]
    item = items.get_item(json_data, key, current_field_id, request["id"])
    if item.get("build", 0) <= items.now():
        raise ZooError(INVALID_REQUEST, f"{key} {request['id']} is already built")
    config = items.item_config(config_data, key, item)
    shopUtils.reduce_real_currency(int(config.get("directBuildReal", 0)), json_data)
    item["build"] = items.now()

    items.send_item(obj, key, current_field_id, item)
    obj["uObj"] = json_data["uObj"]
