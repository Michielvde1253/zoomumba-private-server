from utils import trashbinUtils, fieldItemUtils as items
from utils.trashbinUtils import INVENTORY_FIELD
from utils.zooErrors import ZooError, INVALID_REQUEST, NOT_IMPLEMENTED

# inventory.iva: {"iva": <action>, "type": <Category id>, ...}
#   fti  field -> inventory   {"type", "id", "cnt": 1}          (cages, stores, decos, roads, specials, trashbins)
#                             {"type": 11, "p": [{"id", "aId", "cId", "sId"}, ...]}   (baby animals out of a cage)
#   itf  inventory -> field   {"type", "id", "x", "y", "r"}
#                             {"type": 11, "id", "cId"}          (animal into a cage)
#   sfi  sell from inventory  {"type", "ids": [...]}
# "gui" (request the inventory) is not implemented: the client gets the
# inventory from field "0" of fObj/animals already.

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


# ---- cages, stores, decos, roads, specials ----

def _key(request):
    return items.ITEM_TYPES[int(request["type"])][0]


def item_to_inventory(request, user_id, obj, json_data, config_data, current_field_id):
    key = _key(request)
    item = items.get_item(json_data, key, current_field_id, request["id"])
    del items.get_items(json_data, key, current_field_id)[str(item["id"])]

    if key == "cages":
        # The animals stay with the cage, hidden from the client, and the
        # cage's timers stop until it is placed again.
        field_animals = items.get_cage_animals(json_data, current_field_id, item["id"])
        stored = items.get_stored_cage_animals(json_data, item["id"])
        for animal_id, animal in list(field_animals.items()):
            items.send_animal(obj, current_field_id, item["id"], items.deleted_copy(animal))
            animal["fId"] = 0
            stored[animal_id] = animal
        del json_data["animals"][str(current_field_id)][str(item["id"])]
        json_data.setdefault("inventoryTimes", {})[str(item["id"])] = items.now()

    item["fId"] = 0
    item["act"] = 0
    items.get_items(json_data, key, INVENTORY_FIELD)[str(item["id"])] = item
    items.send_item(obj, key, current_field_id, items.deleted_copy(item, to_inventory=True))

    if key == "roads":
        items.refresh_activity(obj, json_data, config_data, current_field_id, item["x"], item["y"])


def item_to_field(request, user_id, obj, json_data, config_data, current_field_id):
    key = _key(request)
    item = items.get_item(json_data, key, INVENTORY_FIELD, request["id"])
    del items.get_items(json_data, key, INVENTORY_FIELD)[str(item["id"])]
    items.send_item(obj, key, INVENTORY_FIELD, items.deleted_copy(item))

    item.update({"fId": current_field_id, "x": request["x"], "y": request["y"], "r": request.get("r", 0)})
    items.get_items(json_data, key, current_field_id)[str(item["id"])] = item

    if key == "roads":
        item["act"] = 1
        items.refresh_activity(obj, json_data, config_data, current_field_id, item["x"], item["y"])
    else:
        item["act"] = items.building_active(json_data, items.item_config(config_data, key, item), item["x"], item["y"])

    if key == "cages":
        stored_at = json_data.get("inventoryTimes", {}).pop(str(item["id"]), None)
        if stored_at is not None:
            paused = items.now() - stored_at
            for timer in items.CAGE_TIMERS:
                if item.get(timer, 0) > stored_at:
                    item[timer] += paused
        stored = json_data.get("animals", {}).get(INVENTORY_FIELD, {})
        stored = stored.pop(str(item["id"]), {}) if isinstance(stored, dict) else {}
        field_animals = items.get_cage_animals(json_data, current_field_id, item["id"])
        for animal_id, animal in stored.items():
            animal["fId"] = current_field_id
            field_animals[animal_id] = animal
            items.send_animal(obj, current_field_id, item["id"], animal)

    items.send_item(obj, key, current_field_id, item)


def sell_items_from_inventory(request, user_id, obj, json_data, config_data, current_field_id):
    key = _key(request)
    inventory = items.get_items(json_data, key, INVENTORY_FIELD)
    ids = [str(i) for i in request.get("ids", [])]
    missing = [i for i in ids if i not in inventory]
    if not ids or missing:
        raise ZooError(INVALID_REQUEST, f"{key} not in the inventory: {missing or 'none given'}")

    for item_id in ids:
        item = inventory.pop(item_id)
        items.check_sellable(items.item_config(config_data, key, item), key)
        items.pay_out(json_data, *items.sell_price(config_data, key, item))
        if key == "cages":
            stored = json_data.get("animals", {}).get(INVENTORY_FIELD)
            if isinstance(stored, dict):
                stored.pop(item_id, None)
            json_data.get("inventoryTimes", {}).pop(item_id, None)
        items.send_item(obj, key, INVENTORY_FIELD, items.deleted_copy(item))

    obj["uObj"] = json_data["uObj"]


# ---- animals ----

def animals_to_inventory(request, user_id, obj, json_data, config_data, current_field_id):
    moves = request.get("p") or []
    if not moves:
        raise ZooError(INVALID_REQUEST, "no animals given")
    inventory = items.get_inventory_animals(json_data)
    touched_cages = set()

    for move in moves:
        cage = items.get_item(json_data, "cages", current_field_id, move["cId"])
        cage_animals = items.get_cage_animals(json_data, current_field_id, cage["id"])
        animal = cage_animals.pop(str(move["id"]), None)
        if animal is None:
            raise ZooError(INVALID_REQUEST, f"no animal {move['id']} in cage {cage['id']}")

        count_field = items.cage_count_field(config_data["gameItems"]["animals"][str(animal["aId"])])
        cage[count_field] = max(0, cage[count_field] - 1)
        if cage["male"] + cage["female"] + cage["child"] == 0:
            cage["sId"] = 0
        touched_cages.add(str(cage["id"]))

        # inv=1: the client moves it from the cage into its inventory itself
        items.send_animal(obj, current_field_id, cage["id"], items.deleted_copy(animal, to_inventory=True))
        animal.update({"fId": 0, "cId": 0})
        inventory[str(animal["id"])] = animal

    for cage_id in touched_cages:
        items.send_item(obj, "cages", current_field_id, items.get_item(json_data, "cages", current_field_id, cage_id))


def animal_to_cage(request, user_id, obj, json_data, config_data, current_field_id):
    inventory = items.get_inventory_animals(json_data)
    animal = inventory.get(str(request["id"]))
    if animal is None:
        raise ZooError(INVALID_REQUEST, f"no animal {request['id']} in the inventory")
    cage = items.get_item(json_data, "cages", current_field_id, request["cId"])
    animal_config = config_data["gameItems"]["animals"][str(animal["aId"])]
    cage_config = items.item_config(config_data, "cages", cage)

    empty = cage["male"] + cage["female"] + cage["child"] == 0
    if not empty and cage["sId"] != animal["sId"]:
        raise ZooError(INVALID_REQUEST, "a cage can only hold one species")
    if cage_config.get("type") not in animal_config.get("cageTypesPlaceable", [cage_config.get("type")]):
        raise ZooError(INVALID_REQUEST, "this animal can't live in this cage")

    del inventory[str(animal["id"])]
    items.send_animal(obj, INVENTORY_FIELD, "0", items.deleted_copy(animal))

    animal.update({"fId": current_field_id, "cId": cage["id"]})
    items.get_cage_animals(json_data, current_field_id, cage["id"])[str(animal["id"])] = animal
    cage[items.cage_count_field(animal_config)] += 1
    cage["sId"] = animal["sId"]
    if empty:
        species = config_data["gameItems"]["animalsSpecies"][str(animal["sId"])]
        t = items.now()
        cage.update({"clean": t + species["cleanTime"], "feed": t + species["feedTime"],
                     "water": t + species["waterTime"], "cuddle": t + species["cuddleTime"],
                     "sick": t, "health": t + species["healthTime"]})

    items.send_animal(obj, current_field_id, cage["id"], animal)
    items.send_item(obj, "cages", current_field_id, cage)


def sell_animals_from_inventory(request, user_id, obj, json_data, config_data, current_field_id):
    inventory = items.get_inventory_animals(json_data)
    ids = [str(i) for i in request.get("ids", [])]
    missing = [i for i in ids if i not in inventory]
    if not ids or missing:
        raise ZooError(INVALID_REQUEST, f"animals not in the inventory: {missing or 'none given'}")

    for animal_id in ids:
        animal = inventory.pop(animal_id)
        config = config_data["gameItems"]["animals"][str(animal["aId"])]
        items.check_sellable(config, "animal")
        items.pay_out(json_data, int(config.get("sellVirtual", 0)), int(config.get("sellReal", 0)))
        items.send_animal(obj, INVENTORY_FIELD, "0", items.deleted_copy(animal))

    obj["uObj"] = json_data["uObj"]


HANDLERS = {
    ("fti", items.ANIMAL): animals_to_inventory,
    ("itf", items.ANIMAL): animal_to_cage,
    ("sfi", items.ANIMAL): sell_animals_from_inventory,
    ("fti", CATEGORY_TRASHBIN): trashbin_to_inventory,
    ("itf", CATEGORY_TRASHBIN): trashbin_to_field,
    ("sfi", CATEGORY_TRASHBIN): sell_trashbins_from_inventory,
}
for _category in (items.CAGE, items.STORE, items.DECOR, items.SPECIALS, items.BREEDING_LAB, items.NURSERY, items.ROAD):
    HANDLERS[("fti", _category)] = item_to_inventory
    HANDLERS[("itf", _category)] = item_to_field
    HANDLERS[("sfi", _category)] = sell_items_from_inventory
