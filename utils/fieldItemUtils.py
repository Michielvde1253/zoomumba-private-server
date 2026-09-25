"""
Shared helpers for placed field items (cages, stores, decos, roads, specials,
animals): looking them up, pricing them, and sending them to the client.

Layout in the player document (same as the original server):
  fObj.<type>.<fieldId>.<uniqueId>        field "0" is the inventory
  animals.<fieldId>.<cageId>.<uniqueId>   animals in a cage
  animals."0"."0".<uniqueId>              animals in the inventory

PHP sent an array with only index 0 as a JSON list, so new_player.json has
fObj.specials == [{...}] and animals."0" == [{...}]. The client iterates both
with for-in, so a list and {"0": ...} look the same to it; we normalise to
dicts before touching them so other field ids can be added.
"""
import time

from utils import roadPathfindingUtils
from utils.zooErrors import ZooError, INVALID_REQUEST

INVENTORY_FIELD = "0"

# Categories.as
CAGE, STORE, DECOR, TRASHBIN, SPECIALS, ANIMAL, ROAD = 1, 2, 3, 4, 5, 11, 14
BREEDING_LAB, NURSERY = 25, 26

# fObj key and catalogue-id field for each placeable category
ITEM_TYPES = {
    CAGE: ("cages", "cId"),
    STORE: ("stores", "stId"),
    DECOR: ("decos", "dId"),
    TRASHBIN: ("trashbins", "tbId"),
    SPECIALS: ("specials", "sbId"),
    BREEDING_LAB: ("specials", "sbId"),
    NURSERY: ("specials", "sbId"),
    ROAD: ("roads", "rId"),
}
CONFIG_ID_FIELD = {key: id_field for key, id_field in ITEM_TYPES.values()}

# Cage timers that keep running while a cage sits in the inventory; shifted by
# the time it was stored so a cage comes back in the state it was put away in.
CAGE_TIMERS = ("clean", "feed", "water", "cuddle", "health", "sick", "breed")


def _as_dict(value):
    if isinstance(value, list):
        return {str(i): v for i, v in enumerate(value) if v is not None}
    return value if isinstance(value, dict) else {}


def get_items(json_data, key, field_id):
    """fObj.<key>.<field_id>, created if missing."""
    fobj = json_data.setdefault("fObj", {})
    fobj[key] = _as_dict(fobj.get(key))
    fobj[key][str(field_id)] = _as_dict(fobj[key].get(str(field_id)))
    return fobj[key][str(field_id)]


def get_item(json_data, key, field_id, item_id):
    item = get_items(json_data, key, field_id).get(str(item_id))
    if item is None:
        where = "the inventory" if str(field_id) == INVENTORY_FIELD else f"field {field_id}"
        raise ZooError(INVALID_REQUEST, f"no {key} {item_id} in {where}")
    return item


def item_config(config_data, key, item):
    config = config_data["gameItems"][key].get(str(item[CONFIG_ID_FIELD[key]]))
    if config is None:
        raise ZooError(INVALID_REQUEST, f"unknown {key} id {item[CONFIG_ID_FIELD[key]]}")
    return config


def check_sellable(config, key):
    if config.get("sellable", 1) != 1:
        raise ZooError(INVALID_REQUEST, f"{key} is not sellable")


def deleted_copy(item, to_inventory=False):
    """The item as the client needs it to drop it (del=1; inv=1 = moved to the inventory)."""
    item = dict(item)
    item["del"] = 1
    if to_inventory:
        item["inv"] = 1
    return item


def send_item(obj, key, field_id, item):
    obj.setdefault("fObj", {}).setdefault(key, {}).setdefault(str(field_id), {})[str(item["id"])] = item


# ---- animals ----

def get_cage_animals(json_data, field_id, cage_id):
    animals = json_data.setdefault("animals", {})
    field = animals[str(field_id)] = _as_dict(animals.get(str(field_id)))
    field[str(cage_id)] = _as_dict(field.get(str(cage_id)))
    return field[str(cage_id)]


def get_inventory_animals(json_data):
    return get_cage_animals(json_data, INVENTORY_FIELD, "0")


def get_stored_cage_animals(json_data, cage_id):
    """Animals of a cage that is in the inventory. The client only reads
    animals."0"."0", so keeping them under animals."0".<cageId> hides them."""
    return get_cage_animals(json_data, INVENTORY_FIELD, cage_id)


def send_animal(obj, field_id, cage_id, animal):
    obj.setdefault("animals", {}).setdefault(str(field_id), {}).setdefault(str(cage_id), {})[str(animal["id"])] = animal


def animal_config_for(config_data, species_id, kind):
    """The male/female/child entry of a species (ItemConfigProxy.get*AnimalData)."""
    for animal in config_data["gameItems"]["animals"].values():
        if animal["speciesId"] != species_id:
            continue
        if kind == "child" and animal["child"] == 1:
            return animal
        if kind == "male" and animal["male"] == 1 and animal["child"] != 1:
            return animal
        if kind == "female" and animal["male"] != 1 and animal["child"] != 1:
            return animal
    return None


def cage_count_field(animal_config):
    if animal_config["child"] == 1:
        return "child"
    return "male" if animal_config["male"] == 1 else "female"


# ---- selling ----

def sell_price(config_data, key, item):
    """(virtual, real) the player gets for a placed item; same as BuildingHelper.getSellPrice."""
    config = item_config(config_data, key, item)
    virtual, real = int(config.get("sellVirtual", 0)), int(config.get("sellReal", 0))
    if key == "cages" and item.get("male", 0) + item.get("female", 0) > 0:
        # The client only counts the animals when there is at least one adult
        for kind in ("child", "male", "female"):
            count = item.get(kind, 0)
            animal = animal_config_for(config_data, item.get("sId", 0), kind) if count else None
            if animal:
                virtual += count * int(animal.get("sellVirtual", 0))
                real += count * int(animal.get("sellReal", 0))
    return virtual, real


def pay_out(json_data, virtual, real):
    json_data["uObj"]["uCv"] += virtual
    json_data["uObj"]["uCr"] += real


# ---- road connection ----

def building_active(json_data, config, x, y):
    return int(roadPathfindingUtils.is_building_active(json_data, x, y, config["width"], config["height"]))


def refresh_activity(obj, json_data, config_data, field_id, x, y):
    """A road appeared or vanished at (x, y): recompute which buildings are
    connected and send the current field's buildings to the client."""
    for key in ("stores", "cages", "decos", "trashbins"):
        get_items(json_data, key, field_id)
    roadPathfindingUtils.check_all_buildings_around_tile(json_data, config_data, x, y)
    for key in ("stores", "cages", "decos", "trashbins"):
        for item in get_items(json_data, key, field_id).values():
            send_item(obj, key, field_id, item)


def now():
    return int(time.time())
