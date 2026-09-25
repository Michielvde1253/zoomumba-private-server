from utils import trashbinUtils
from utils.trashbinUtils import INVENTORY_FIELD
from utils.zooErrors import ZooError, INVALID_REQUEST, NOT_IMPLEMENTED

# inventory.iva: {"iva": <action>, "type": <Category id>, ...}
#   fti  field -> inventory   {"type", "id", "cnt": 1}
#   itf  inventory -> field   {"type", "id", "x", "y", "r"}
#   sfi  sell from inventory  {"type", "ids": [...]}
# Only trashbins (Category 4) are implemented so far; everything else keeps
# answering "not implemented".

CATEGORY_TRASHBIN = 4


def handle_inventoryIva(request, user_id, obj, json_data, config_data):
    action = request.get("iva")
    category = int(request.get("type", -1))
    handler = HANDLERS.get((action, category))
    if handler is None:
        raise ZooError(NOT_IMPLEMENTED, f"inventory.iva {action} type {category}")
    handler(request, user_id, obj, json_data, config_data, json_data["uObj"]["current_field"])


def trashbin_to_inventory(request, user_id, obj, json_data, config_data, current_field_id):
    field_id = str(current_field_id)
    trashbins = trashbinUtils.get_trashbins(json_data, field_id)
    trashbin = trashbins.pop(str(request["id"]), None)
    if trashbin is None:
        raise ZooError(INVALID_REQUEST, f"no trashbin {request['id']} on field {field_id}")

    trashbinUtils.link_road(json_data, field_id, None, None, trashbin["id"])
    trashbin["fId"] = 0
    trashbinUtils.get_trashbins(json_data, INVENTORY_FIELD)[str(trashbin["id"])] = trashbin
    trashbinUtils.clamp_bin_trash(json_data, config_data, field_id)  # its trash is lost

    # del=1 removes it from the field, inv=1 makes the client put it in the inventory
    trashbinUtils.send_trashbin(obj, current_field_id, trashbinUtils.deleted_copy(trashbin, to_inventory=True))
    obj["pfObj"] = json_data["pfObj"]


def trashbin_to_field(request, user_id, obj, json_data, config_data, current_field_id):
    field_id = str(current_field_id)
    inventory = trashbinUtils.get_trashbins(json_data, INVENTORY_FIELD)
    trashbin = inventory.pop(str(request["id"]), None)
    if trashbin is None:
        raise ZooError(INVALID_REQUEST, f"no trashbin {request['id']} in the inventory")

    trashbin.update({"fId": current_field_id, "x": request["x"], "y": request["y"], "r": request.get("r", 0), "act": 1})
    trashbinUtils.get_trashbins(json_data, field_id)[str(trashbin["id"])] = trashbin
    trashbinUtils.link_road(json_data, field_id, request["x"], request["y"], trashbin["id"])

    # Remove it from the inventory ("0") and add it to the field
    trashbinUtils.send_trashbin(obj, INVENTORY_FIELD, trashbinUtils.deleted_copy(dict(trashbin, fId=0)))
    trashbinUtils.send_trashbin(obj, current_field_id, trashbin)


def sell_trashbins_from_inventory(request, user_id, obj, json_data, config_data, current_field_id):
    inventory = trashbinUtils.get_trashbins(json_data, INVENTORY_FIELD)
    ids = [str(i) for i in request.get("ids", [])]
    missing = [i for i in ids if i not in inventory]
    if not ids or missing:
        raise ZooError(INVALID_REQUEST, f"trashbins not in the inventory: {missing or 'none given'}")

    for item_id in ids:
        trashbin = inventory.pop(item_id)
        config_for_bin = config_data["gameItems"]["trashbins"].get(str(trashbin["tbId"]), {})
        if config_for_bin.get("sellable", 1) != 1:
            raise ZooError(INVALID_REQUEST, f"trashbin {trashbin['tbId']} is not sellable")
        json_data["uObj"]["uCv"] += int(config_for_bin.get("sellVirtual", 0))
        json_data["uObj"]["uCr"] += int(config_for_bin.get("sellReal", 0))
        trashbinUtils.send_trashbin(obj, INVENTORY_FIELD, trashbinUtils.deleted_copy(trashbin))

    obj["uObj"] = json_data["uObj"]


HANDLERS = {
    ("fti", CATEGORY_TRASHBIN): trashbin_to_inventory,
    ("itf", CATEGORY_TRASHBIN): trashbin_to_field,
    ("sfi", CATEGORY_TRASHBIN): sell_trashbins_from_inventory,
}
