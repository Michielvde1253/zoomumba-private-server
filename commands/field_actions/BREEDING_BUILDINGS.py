import math
import random

from utils import rewardUtils, fieldItemUtils as items
from utils.zooErrors import ZooError, INVALID_REQUEST

# Breeding lab (specials sbId 1) and nursery (sbId 2). The client deducts
# nothing and never picks a result; it reads the special's `end` (0 = idle,
# future = running, past = finished) and usedItemType/Id1..5, and shows
# bAdvObj.r / raiseObj.r from the collect answers.
#
# Breeding lab
#   bsASB {"id", "aIdM", "aIdF", "items": [{"type", "id"}, ...]}  start: two adult
#         inventory animals (uniqueIds) of the same genus plus up to 3 of the genus'
#         breedAdvanceResources as chance items; everything is used up. Costs the
#         average breedAdvanceCost of both species, takes the average breedAdvanceTime.
#   bdASB {"id"}  elixir (resource 11): halves the time left
#   beASB {"id"}  collect: a baby of one of the parents' tiers - or one tier higher,
#         likelier with more chance items - goes to the inventory, plus the baby
#         species' breedAdvanceReward. Answer: bAdvObj.r = [{type, aId}, {type, id, cnt}]
# Nursery
#   rsASB {"id", "aId"}  start raising an inventory baby (uniqueId) with raisable=1
#         for raisingCost over raisingTime
#   arASB {"id"}  raising potion (resource 12): halves the time left
#   reASB {"id"}  collect: the grown animal (male with the species' breedMale %)
#         goes to the inventory. Answer: raiseObj.r["0"] = {aId}
#   rdASB {"id", "aId"}  finish raising now for raisingDirectCost (the client never
#         sends this one)

BREEDING_LAB, NURSERY = 1, 2
ANIMAL_CATEGORY = 11
ELIXIR, RAISING_POTION = 11, 12
# Chance of a baby one tier above the best parent: base + per point of item "chance"
TIER_UP_BASE, TIER_UP_PER_CHANCE = 0.1, 0.05


def _building(json_data, field_id, special_id, kind):
    special = items.get_item(json_data, "specials", field_id, special_id)
    if int(special.get("sbId", 0)) != kind:
        raise ZooError(INVALID_REQUEST, f"special {special_id} is not a {'breeding lab' if kind == BREEDING_LAB else 'nursery'}")
    return special


def _reset(special):
    special["end"] = 0
    for slot in range(1, 6):
        special[f"usedItemType{slot}"] = 0
        special[f"usedItemId{slot}"] = 0


def _running(special):
    return int(special.get("end", 0)) > items.now()


def _finished(special):
    return 0 < int(special.get("end", 0)) <= items.now()


def _species(config_data, species_id):
    return config_data["gameItems"]["animalsSpecies"][str(species_id)]


def _inventory_animal(json_data, config_data, unique_id):
    animal = items.get_inventory_animals(json_data).get(str(unique_id))
    if animal is None:
        raise ZooError(INVALID_REQUEST, f"no animal {unique_id} in the inventory", resync=("animals",))
    return animal, config_data["gameItems"]["animals"][str(animal["aId"])]


def _new_inventory_animal(obj, json_data, config_data, user_id, animal_id):
    config = config_data["gameItems"]["animals"][str(animal_id)]
    animal = {"id": json_data["next_object_id"], "uId": user_id, "aId": int(animal_id), "sId": config["speciesId"],
              "cId": 0, "fId": 0, "fTime": items.now(), "act": 0}
    json_data["next_object_id"] += 1
    items.get_inventory_animals(json_data)[str(animal["id"])] = animal
    items.send_animal(obj, items.INVENTORY_FIELD, "0", animal)
    return animal


def _speed_up(obj, json_data, special, resource_id, field_id):
    if not _running(special):
        raise ZooError(INVALID_REQUEST, "nothing is running there")
    rewardUtils.take_resource(json_data, resource_id, 1)
    special["end"] = items.now() + (int(special["end"]) - items.now()) // 2
    items.send_item(obj, "specials", field_id, special)
    obj["res"] = json_data["res"]


def _send(obj, json_data, special, field_id):
    items.send_item(obj, "specials", field_id, special)
    obj["uObj"] = json_data["uObj"]


# ---- breeding lab ----

def handle_startAdvancedBreeding(request, user_id, obj, json_data, config_data, current_field_id):
    lab = _building(json_data, current_field_id, request["id"], BREEDING_LAB)
    if int(lab.get("end", 0)) != 0:
        raise ZooError(INVALID_REQUEST, "the breeding lab is busy")

    male, male_config = _inventory_animal(json_data, config_data, request["aIdM"])
    female, female_config = _inventory_animal(json_data, config_data, request["aIdF"])
    if male_config["male"] != 1 or male_config["child"] == 1 or female_config["male"] == 1 or female_config["child"] == 1:
        raise ZooError(INVALID_REQUEST, "needs an adult male and an adult female")
    male_species, female_species = _species(config_data, male["sId"]), _species(config_data, female["sId"])
    if male_species["genusId"] != female_species["genusId"] or not (male_species.get("breedableAdvance") and female_species.get("breedableAdvance")):
        raise ZooError(INVALID_REQUEST, "these animals can't be bred together")
    genus = config_data["gameItems"]["genus"][str(male_species["genusId"])]

    chance_items = (request.get("items") or [])[:3]
    allowed = {(int(i["type"]), int(i["id"])): i for i in genus.get("breedAdvanceResources", [])}
    for item in chance_items:
        entry = allowed.get((int(item["type"]), int(item["id"])))
        if entry is None:
            raise ZooError(INVALID_REQUEST, f"{item} can't be used with this genus")
        if entry["type"] == 13:
            rewardUtils.take_resource(json_data, entry["id"], int(entry.get("cnt", 1)))
        else:
            owned = json_data.setdefault("collItems", {}).get(str(entry["id"]))
            if owned is None or owned["cnt"] < int(entry.get("cnt", 1)):
                raise ZooError(INVALID_REQUEST, f"not enough of collection item {entry['id']}", resync=("collItems",))
            owned["cnt"] -= int(entry.get("cnt", 1))

    costs = [s["breedAdvanceCost"][0] for s in (male_species, female_species)]
    rewardUtils.pay_cost(json_data, dict(costs[0], cnt=math.ceil(sum(c["cnt"] for c in costs) / 2)))
    duration = math.ceil((male_species["breedAdvanceTime"] + female_species["breedAdvanceTime"]) / 2)

    inventory = items.get_inventory_animals(json_data)
    for parent in (male, female):
        del inventory[str(parent["id"])]
        items.send_animal(obj, items.INVENTORY_FIELD, "0", items.deleted_copy(parent))

    lab["end"] = items.now() + duration
    lab.update({"usedItemType1": ANIMAL_CATEGORY, "usedItemId1": male["sId"],
                "usedItemType2": ANIMAL_CATEGORY, "usedItemId2": female["sId"]})
    for slot in range(3, 6):
        item = chance_items[slot - 3] if slot - 3 < len(chance_items) else None
        lab[f"usedItemType{slot}"] = int(item["type"]) if item else 0
        lab[f"usedItemId{slot}"] = int(item["id"]) if item else 0

    _send(obj, json_data, lab, current_field_id)
    if "res" in json_data:
        obj["res"] = json_data["res"]
    obj["collItems"] = json_data.get("collItems", {})


def handle_useElixir(request, user_id, obj, json_data, config_data, current_field_id):
    lab = _building(json_data, current_field_id, request["id"], BREEDING_LAB)
    _speed_up(obj, json_data, lab, ELIXIR, current_field_id)


def _pick_baby_species(config_data, lab):
    parents = [_species(config_data, lab["usedItemId1"]), _species(config_data, lab["usedItemId2"])]
    genus = config_data["gameItems"]["genus"][str(parents[0]["genusId"])]
    tiers = {int(t): s for t, s in genus["speciesId"].items()}
    tier = random.choice([p["tier"] for p in parents])
    best = max(p["tier"] for p in parents)
    chances = {(int(i["type"]), int(i["id"])): int(i.get("chance", 0)) for i in genus.get("breedAdvanceResources", [])}
    bonus = sum(chances.get((int(lab[f"usedItemType{s}"]), int(lab[f"usedItemId{s}"])), 0) for s in range(3, 6))
    if best + 1 in tiers and random.random() < TIER_UP_BASE + TIER_UP_PER_CHANCE * bonus:
        tier = best + 1
    return tiers.get(tier, lab["usedItemId1"])


def handle_endAdvancedBreeding(request, user_id, obj, json_data, config_data, current_field_id):
    lab = _building(json_data, current_field_id, request["id"], BREEDING_LAB)
    if not _finished(lab):
        raise ZooError(INVALID_REQUEST, "the breeding isn't finished")

    species_id = _pick_baby_species(config_data, lab)
    species = _species(config_data, species_id)
    baby = _new_inventory_animal(obj, json_data, config_data, user_id, species["animalIds"][2])
    result = [{"type": "animals", "aId": baby["aId"]}]
    for reward in species.get("breedAdvanceReward", [])[:1]:
        rewardUtils.give_reward(reward, user_id, obj, json_data, config_data)
        result.append({"type": reward["type"], "id": reward["id"], "cnt": reward.get("cnt", 1)})

    _reset(lab)
    obj["bAdvObj"] = {"r": result}
    _send(obj, json_data, lab, current_field_id)


# ---- nursery ----

def handle_startNurseryBreeding(request, user_id, obj, json_data, config_data, current_field_id):
    nursery = _building(json_data, current_field_id, request["id"], NURSERY)
    if int(nursery.get("end", 0)) != 0:
        raise ZooError(INVALID_REQUEST, "the nursery is busy")
    baby, baby_config = _inventory_animal(json_data, config_data, request["aId"])
    species = _species(config_data, baby["sId"])
    if baby_config["child"] != 1 or species.get("raisable") != 1:
        raise ZooError(INVALID_REQUEST, "only babies that can be raised go into the nursery")
    rewardUtils.pay_cost(json_data, species["raisingCost"][0])

    del items.get_inventory_animals(json_data)[str(baby["id"])]
    items.send_animal(obj, items.INVENTORY_FIELD, "0", items.deleted_copy(baby))
    _reset(nursery)
    nursery.update({"end": items.now() + int(species["raisingTime"]),
                    "usedItemType1": ANIMAL_CATEGORY, "usedItemId1": baby["sId"]})
    _send(obj, json_data, nursery, current_field_id)


def handle_useRaisingPotion(request, user_id, obj, json_data, config_data, current_field_id):
    nursery = _building(json_data, current_field_id, request["id"], NURSERY)
    _speed_up(obj, json_data, nursery, RAISING_POTION, current_field_id)


def handle_instantNurseryBreeding(request, user_id, obj, json_data, config_data, current_field_id):
    nursery = _building(json_data, current_field_id, request["id"], NURSERY)
    if not _running(nursery):
        raise ZooError(INVALID_REQUEST, "nothing is being raised")
    rewardUtils.pay_cost(json_data, _species(config_data, nursery["usedItemId1"])["raisingDirectCost"][0])
    nursery["end"] = items.now()
    _send(obj, json_data, nursery, current_field_id)


def handle_endNurseryBreeding(request, user_id, obj, json_data, config_data, current_field_id):
    nursery = _building(json_data, current_field_id, request["id"], NURSERY)
    if not _finished(nursery):
        raise ZooError(INVALID_REQUEST, "the raising isn't finished")
    species = _species(config_data, nursery["usedItemId1"])
    male = random.randint(1, 100) <= int(species.get("breedMale", 50))
    adult = _new_inventory_animal(obj, json_data, config_data, user_id, species["animalIds"][0 if male else 1])

    _reset(nursery)
    obj["raiseObj"] = {"r": {"0": {"aId": adult["aId"]}}}
    _send(obj, json_data, nursery, current_field_id)
