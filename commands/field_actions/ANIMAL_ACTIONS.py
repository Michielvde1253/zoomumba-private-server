from utils import shopUtils, fieldItemUtils as items
from utils.zooErrors import ZooError, INVALID_REQUEST

# These three are in NET.as but this client never sends them (animals move
# through inventory.iva instead); implemented from their names and the
# neighbouring commands.
#   sAC   {"id": <cage uniqueId>, "aId": <animal uniqueId>}   sell an animal out of a cage
#   mAC   {"aId": <animal uniqueId>, "idf": <from cage>, "idt": <to cage>}   move it between cages
#   bAInv {"aId": <catalogue animal id>, "cR": 0|1}          buy an animal into the inventory


def _find_animal(json_data, field_id, cage_id, animal_id):
    animals = items.get_cage_animals(json_data, field_id, cage_id)
    animal = animals.get(str(animal_id))
    if animal is None:  # maybe a catalogue id after all
        animal = next((a for a in animals.values() if int(a.get("aId", -1)) == int(animal_id)), None)
    if animal is None:
        raise ZooError(INVALID_REQUEST, f"no animal {animal_id} in cage {cage_id}")
    return animal


def _take_out(obj, json_data, config_data, field_id, cage, animal):
    del items.get_cage_animals(json_data, field_id, cage["id"])[str(animal["id"])]
    kind = items.cage_count_field(config_data["gameItems"]["animals"][str(animal["aId"])])
    cage[kind] = max(0, cage[kind] - 1)
    if cage["male"] + cage["female"] + cage["child"] == 0:
        cage["sId"] = 0
    items.send_animal(obj, field_id, cage["id"], items.deleted_copy(animal))


def handle_sellAnimalCage(request, user_id, obj, json_data, config_data, current_field_id):
    cage = items.get_item(json_data, "cages", current_field_id, request["id"])
    animal = _find_animal(json_data, current_field_id, cage["id"], request["aId"])
    config = config_data["gameItems"]["animals"][str(animal["aId"])]
    items.check_sellable(config, "animal")
    _take_out(obj, json_data, config_data, current_field_id, cage, animal)
    items.pay_out(json_data, int(config.get("sellVirtual", 0)), int(config.get("sellReal", 0)))

    items.send_item(obj, "cages", current_field_id, cage)
    obj["uObj"] = json_data["uObj"]


def handle_moveAnimalCage(request, user_id, obj, json_data, config_data, current_field_id):
    source = items.get_item(json_data, "cages", current_field_id, request["idf"])
    target = items.get_item(json_data, "cages", current_field_id, request["idt"])
    animal = _find_animal(json_data, current_field_id, source["id"], request["aId"])
    config = config_data["gameItems"]["animals"][str(animal["aId"])]

    kind = items.cage_count_field(config)
    adults = target["male"] + target["female"]
    if adults + target["child"] > 0 and target["sId"] != animal["sId"]:
        raise ZooError(INVALID_REQUEST, "a cage can only hold one species")
    limits = config_data["gameItems"]["cagesSpecies"].get(str(target["cId"]), {}).get(str(animal["sId"]))
    if limits is None:
        raise ZooError(INVALID_REQUEST, "this animal can't live in that cage")
    if (kind == "child" and target["child"] >= limits["maxChild"]) or (kind != "child" and adults >= limits["maxAdult"]):
        raise ZooError(INVALID_REQUEST, "no room in that cage")

    _take_out(obj, json_data, config_data, current_field_id, source, animal)
    animal["cId"] = target["id"]
    items.get_cage_animals(json_data, current_field_id, target["id"])[str(animal["id"])] = animal
    target[kind] += 1
    target["sId"] = animal["sId"]

    items.send_animal(obj, current_field_id, target["id"], animal)
    items.send_item(obj, "cages", current_field_id, source)
    items.send_item(obj, "cages", current_field_id, target)


def handle_buyAnimalToInventory(request, user_id, obj, json_data, config_data, current_field_id):
    config = config_data["gameItems"]["animals"].get(str(request["aId"]))
    if config is None or config.get("buyable", 1) != 1:
        raise ZooError(INVALID_REQUEST, f"animal {request['aId']} can't be bought")
    if int(request.get("cR", 0)) == 1:
        shopUtils.reduce_real_currency(int(config.get("buyReal", 0)), json_data)
    else:
        shopUtils.buy_from_shop(config, json_data["uObj"]["uLvl"], json_data)

    animal = {"id": json_data["next_object_id"], "uId": user_id, "aId": int(request["aId"]),
              "sId": config["speciesId"], "cId": 0, "fId": 0, "fTime": items.now(), "act": 0}
    json_data["next_object_id"] += 1
    items.get_inventory_animals(json_data)[str(animal["id"])] = animal

    items.send_animal(obj, items.INVENTORY_FIELD, "0", animal)
    obj["uObj"] = json_data["uObj"]
