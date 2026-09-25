import random
import time

from utils import rewardUtils, shopUtils
from utils.zooErrors import ZooError, INVALID_REQUEST, NOT_ENOUGH_MONEY

# Recycling centre: turns trash (resource 13) plus coins into materials.
# recyclingSlots.<slotId> = {uId, slotId, materialId, amount, finishTime, endTime}
#   slot 1 is free for good (freeSlots = 1, endTime 0); slots 2..maxSlots are
#   rented for slotRentDays and gone once endTime passes; materialId 0 = empty,
#   finishTime = when the recycling is done (RecyclingProxy).
# The client deducts nothing, so every answer carries the changed blocks.
#
#   grs  {}                                   the slots
#   brs  {"slotId", "days"}                   rent a slot: slotRentDays[days].rc real currency
#   srm  {"slotId", "materialId", "amount", "useBooster"}  start: per unit craftTrash trash and
#        craftVirtual coins (or craftReal real currency), takes amount * craftDuration;
#        the booster (resource 14) raises the rare drop chance by rareDropChanceBooster
#   crs  {"slotId"}                           collect: amount of the material, and with
#        rareDropChance[amount] % one of its rareDropId; shown with itemLayer
#   icrs {"slotId"}                           collect now for craftInstantReal * amount
# item.buySB {"id"}: a surprise box of materials for its buyReal. The client doesn't
#   say what's inside; the translations say random materials with a small chance
#   of rare ones, better for the bigger boxes - the amounts below are a guess.

TRASH, BOOSTER = "13", "14"
DAY = 86400
# box id -> (number of material stacks, units per stack, % chance each stack is the rare drop)
SURPRISE_BOXES = {1: (3, (1, 3), 5), 2: (4, (2, 4), 15), 3: (5, (3, 5), 25)}


def _config(config_data):
    return config_data.get("recyclingCenter", {})


def _slots(json_data):
    slots = json_data.get("recyclingSlots")
    if not isinstance(slots, dict):
        slots = json_data["recyclingSlots"] = {}
    now = int(time.time())
    for slot_id in list(slots):
        slot = slots[slot_id]
        # A rented slot goes back to "buy" once its time is up and it's empty
        if str(slot_id) != "1" and 0 < int(slot.get("endTime", 0)) <= now and int(slot.get("materialId", 0)) == 0:
            del slots[slot_id]
    if "1" not in slots:
        slots["1"] = {"uId": json_data["uObj"].get("uId", 0), "slotId": 1, "materialId": 0, "amount": 0, "finishTime": 0, "endTime": 0}
    return slots


def _slot(json_data, slot_id):
    slot = _slots(json_data).get(str(slot_id))
    if slot is None:
        raise ZooError(INVALID_REQUEST, f"no recycling slot {slot_id}", resync=("recyclingSlots",))
    return slot


def _material(config_data, material_id):
    material = config_data["gameItems"]["materials"].get(str(material_id))
    if material is None:
        raise ZooError(INVALID_REQUEST, f"unknown material {material_id}")
    return material


def _boosters(json_data):
    return json_data.setdefault("recyclingBoosters", {})  # server-only: slots started with a booster


def _give_materials(json_data, user_id, material_id, amount):
    materials = json_data.setdefault("mat", {})
    entry = materials.setdefault(str(material_id), {"uId": user_id, "id": int(material_id), "cnt": 0, "mCnt": 250})
    entry["cnt"] += amount  # materials aren't capped (MaterialProxy.increaseMaterial)


def _item_layer(kind, stacks):
    # ParserProxy: itemLayer.items is nested twice; the window shows material cards
    return {"type": kind, "items": {"0": {str(i): {"id": m, "count": c} for i, (m, c) in enumerate(stacks)}}}


def _send(obj, json_data):
    obj["recyclingSlots"] = _slots(json_data)


def handle_recyclingGetSlots(request, user_id, obj, json_data, config_data):
    _send(obj, json_data)


def handle_recyclingBookSlot(request, user_id, obj, json_data, config_data):
    slot_id, days = int(request["slotId"]), str(request["days"])
    config = _config(config_data)
    rent = config.get("slotRentDays", {}).get(days)
    if rent is None:
        raise ZooError(INVALID_REQUEST, f"slots can't be rented for {days} days")
    if not 1 < slot_id <= int(config.get("maxSlots", 3)):
        raise ZooError(INVALID_REQUEST, f"slot {slot_id} can't be rented")
    slots = _slots(json_data)
    if str(slot_id) in slots:
        raise ZooError(INVALID_REQUEST, f"slot {slot_id} is already rented", resync=("recyclingSlots",))
    shopUtils.reduce_real_currency(int(rent["rc"]), json_data)
    slots[str(slot_id)] = {"uId": user_id, "slotId": slot_id, "materialId": 0, "amount": 0, "finishTime": 0,
                           "endTime": int(time.time()) + int(rent["days"]) * DAY}
    _send(obj, json_data)
    obj["uObj"] = json_data["uObj"]


def handle_recyclingStart(request, user_id, obj, json_data, config_data):
    slot = _slot(json_data, request["slotId"])
    if int(slot.get("materialId", 0)) != 0:
        raise ZooError(INVALID_REQUEST, "that slot is busy", resync=("recyclingSlots",))
    material_id, amount = int(request["materialId"]), int(request["amount"])
    material = _material(config_data, material_id)
    if material.get("isRecyclable") != 1:
        raise ZooError(INVALID_REQUEST, f"material {material_id} can't be recycled")
    if not 1 <= amount <= int(_config(config_data).get("maxStack", 5)):
        raise ZooError(INVALID_REQUEST, f"can't recycle {amount} at once")
    use_booster = bool(request.get("useBooster"))

    rewardUtils.take_resource(json_data, TRASH, int(material.get("craftTrash", 0)) * amount)
    if int(material.get("craftVirtual", 0)) > 0:
        shopUtils.reduce_virtual_currency(int(material["craftVirtual"]) * amount, json_data)
    else:
        shopUtils.reduce_real_currency(int(material.get("craftReal", 0)) * amount, json_data)
    if use_booster:
        rewardUtils.take_resource(json_data, BOOSTER, 1)

    slot.update({"materialId": material_id, "amount": amount,
                 "finishTime": int(time.time()) + int(material.get("craftDuration", 0)) * amount})
    _boosters(json_data)[str(slot["slotId"])] = use_booster
    _send(obj, json_data)
    obj["res"] = json_data["res"]
    obj["uObj"] = json_data["uObj"]


def _collect(obj, json_data, config_data, user_id, slot):
    material = _material(config_data, slot["materialId"])
    amount = int(slot["amount"])
    stacks = [(int(slot["materialId"]), amount)]
    _give_materials(json_data, user_id, slot["materialId"], amount)

    config = _config(config_data)
    chance = int(config.get("rareDropChance", {}).get(str(amount), 0))
    if _boosters(json_data).pop(str(slot["slotId"]), False):
        chance += int(config.get("rareDropChanceBooster", 0))
    if material.get("rareDropId") and random.randint(1, 100) <= chance:
        _give_materials(json_data, user_id, material["rareDropId"], 1)
        stacks.append((int(material["rareDropId"]), 1))

    slot.update({"materialId": 0, "amount": 0, "finishTime": 0})
    _send(obj, json_data)
    obj["mat"] = json_data["mat"]
    obj["itemLayer"] = _item_layer("recycling", stacks)


def handle_recyclingCollect(request, user_id, obj, json_data, config_data):
    slot = _slot(json_data, request["slotId"])
    if int(slot.get("materialId", 0)) == 0 or int(slot.get("finishTime", 0)) > int(time.time()):
        raise ZooError(INVALID_REQUEST, "nothing to collect there", resync=("recyclingSlots",))
    _collect(obj, json_data, config_data, user_id, slot)


def handle_recyclingCollectInstant(request, user_id, obj, json_data, config_data):
    slot = _slot(json_data, request["slotId"])
    if int(slot.get("materialId", 0)) == 0:
        raise ZooError(INVALID_REQUEST, "nothing is recycled there", resync=("recyclingSlots",))
    if int(slot.get("finishTime", 0)) > int(time.time()):
        material = _material(config_data, slot["materialId"])
        shopUtils.reduce_real_currency(int(material.get("craftInstantReal", 0)) * int(slot["amount"]), json_data)
    _collect(obj, json_data, config_data, user_id, slot)
    obj["uObj"] = json_data["uObj"]


def handle_buySurpriseBox(request, user_id, obj, json_data, config_data):
    box_id = int(request["id"])
    box = config_data["gameItems"].get("surpriseBoxes", {}).get(str(box_id))
    if box is None or box.get("buyable", 1) != 1 or box_id not in SURPRISE_BOXES:
        raise ZooError(INVALID_REQUEST, f"no surprise box {box_id}")
    shopUtils.reduce_real_currency(int(box.get("buyReal", 0)), json_data)

    recyclable = [m for m in config_data["gameItems"]["materials"].values() if m.get("isRecyclable") == 1]
    count, (low, high), rare_chance = SURPRISE_BOXES[box_id]
    stacks = []
    for _ in range(count):
        material = random.choice(recyclable)
        if material.get("rareDropId") and random.randint(1, 100) <= rare_chance:
            stacks.append((int(material["rareDropId"]), 1))
        else:
            stacks.append((int(material["materialId"]), random.randint(low, high)))
    for material_id, amount in stacks:
        _give_materials(json_data, user_id, material_id, amount)

    obj["mat"] = json_data["mat"]
    obj["uObj"] = json_data["uObj"]
    obj["itemLayer"] = _item_layer("surpriseBox", stacks)
