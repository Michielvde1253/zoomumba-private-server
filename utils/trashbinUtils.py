"""
Helpers for trashbins and trash.

How trash works in the client:
  * pfObj.<fieldId>.trashbins   = total trash sitting in all bins of that zoo.
    The client spreads it over the bins itself (TrashManager.distributeBinTrash),
    up to each bin's config "capacity".
  * pfObj.<fieldId>.trashroads  = trash lying on the roads.
  * Emptying a bin / clearing road trash gives 1 XP and 1 trash resource
    (res 13) per piece of trash (UserResourcesProxy.getItemCalculatedXP).
Placed trashbins live in fObj.trashbins.<fieldId>.<uniqueId>; inventory
trashbins live in fObj.trashbins."0".<uniqueId> (fId 0), like the real server.
"""

INVENTORY_FIELD = "0"
TRASH_RESOURCE_ID = "13"


def link_road(json_data, field_id, x, y, trashbin_id):
    """The original server stored the id of the trashbin standing on a road in road["trashbin"]
    (the client ignores it, but keep the data consistent). Pass x=y=None to only unlink."""
    for road in json_data["fObj"].get("roads", {}).get(str(field_id), {}).values():
        if x is not None and road.get("x") == x and road.get("y") == y:
            road["trashbin"] = trashbin_id
        elif road.get("trashbin") == trashbin_id:
            road["trashbin"] = 0


def get_trashbins(json_data, field_id):
    return json_data["fObj"].setdefault("trashbins", {}).setdefault(str(field_id), {})


def get_bin_capacity(json_data, config_data, field_id):
    """Total trash all trashbins on a field can hold."""
    total = 0
    for trashbin in get_trashbins(json_data, field_id).values():
        config_for_bin = config_data["gameItems"]["trashbins"].get(str(trashbin.get("tbId")), {})
        total += int(config_for_bin.get("capacity", 0))
    return total


def clamp_bin_trash(json_data, config_data, field_id):
    """Make sure the bins don't hold more trash than they can (e.g. after one is removed)."""
    field = json_data["pfObj"][str(field_id)]
    capacity = get_bin_capacity(json_data, config_data, field_id)
    field["trashbins"] = max(0, min(field.get("trashbins", 0), capacity))


def spawn_trash(json_data, config_data, field_id, amount):
    """New trash from visitors: fills the bins first, the rest lands on the roads."""
    field = json_data["pfObj"][str(field_id)]
    space = max(0, get_bin_capacity(json_data, config_data, field_id) - field.get("trashbins", 0))
    into_bins = min(amount, space)
    field["trashbins"] = field.get("trashbins", 0) + into_bins
    field["trashroads"] = field.get("trashroads", 0) + (amount - into_bins)


def give_trash_rewards(json_data, amount):
    """1 XP and 1 trash resource per piece of trash cleaned (capped at the resource's mCnt)."""
    json_data["uObj"]["uEp"] += amount
    trash = json_data.get("res", {}).get(TRASH_RESOURCE_ID)
    if trash is not None:
        trash["cnt"] = min(trash["cnt"] + amount, trash.get("mCnt", trash["cnt"] + amount))


def deleted_copy(item, to_inventory=False):
    """The item as the client needs it to remove it from the field (del=1, inv=1 = moved to inventory)."""
    item = dict(item)
    item["del"] = 1
    if to_inventory:
        item["inv"] = 1
    return item


def send_trashbin(obj, field_id, item):
    obj.setdefault("fObj", {}).setdefault("trashbins", {}).setdefault(field_id, {})[str(item["id"])] = item
