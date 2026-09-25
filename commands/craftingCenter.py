import time

from utils import rewardUtils, shopUtils
from utils.zooErrors import ZooError, INVALID_REQUEST, NOT_ENOUGH_MONEY, NOT_ENOUGH_RESOURCES

# Crafting centre: turns an owned blueprint (bp.<id>.active = 1) plus materials
# and paws into its reward item (always a placeable: decos/cages/stores/road/
# trashbin, into the inventory) and xp. One craft at a time, in
# crafting = {uId, blueprintId, startTime, endTime, active}; the client shows
# it as running while endTime is in the future and ready once it has passed.
# The client deducts nothing and never adds the item, so every answer
# carries the blocks it changed.
#
#   sbc  {"blueprintId"}  start: blueprint's materials [{id, count}] and craftPaws
#   cbc  {}               collect a finished craft -> craftingReward {xp, item}
#   icbc {}               finish now for craftInstantReal (collect with cbc)
#   dbct {}               one crafting booster (resource 15) halves the time left
#                         (the client and config don't say by how much - guess)
#   gac  {}               never sent by the client; same as cbc

CRAFTING_BOOSTER = "15"


def _state(json_data):
    crafting = json_data.get("crafting")
    if not isinstance(crafting, dict):
        crafting = json_data["crafting"] = {"active": 0}
    return crafting


def _blueprint(config_data, blueprint_id):
    blueprint = config_data["gameItems"]["blueprints"].get(str(blueprint_id))
    if blueprint is None:
        raise ZooError(INVALID_REQUEST, f"unknown blueprint {blueprint_id}")
    return blueprint


def _running(json_data):
    crafting = _state(json_data)
    if int(crafting.get("active", 0)) != 1:
        raise ZooError(INVALID_REQUEST, "nothing is being crafted", resync=("crafting",))
    return crafting


def handle_craftingStart(request, user_id, obj, json_data, config_data):
    crafting = _state(json_data)
    if int(crafting.get("active", 0)) == 1:
        raise ZooError(INVALID_REQUEST, "the crafting centre is busy", resync=("crafting",))
    blueprint_id = int(request["blueprintId"])
    owned = json_data.get("bp", {}).get(str(blueprint_id))
    if not owned or int(owned.get("active", 0)) != 1:
        raise ZooError(INVALID_REQUEST, f"blueprint {blueprint_id} isn't owned")
    blueprint = _blueprint(config_data, blueprint_id)
    if json_data["uObj"]["uLvl"] < int(blueprint.get("userLevelRequired", 0)):
        raise ZooError(INVALID_REQUEST, "level too low for this blueprint")

    materials = json_data.setdefault("mat", {})
    for need in blueprint.get("materials", []):
        if materials.get(str(need["id"]), {}).get("cnt", 0) < int(need["count"]):
            raise ZooError(NOT_ENOUGH_RESOURCES, f"not enough of material {need['id']}", resync=("mat", "uObj"))
    paws = int(blueprint.get("craftPaws", 0))
    if json_data["uObj"].get("pPaw", 0) < paws:
        raise ZooError(NOT_ENOUGH_MONEY, resync=("mat", "uObj"))

    for need in blueprint.get("materials", []):
        materials[str(need["id"])]["cnt"] -= int(need["count"])
    json_data["uObj"]["pPaw"] -= paws
    now = int(time.time())
    json_data["crafting"] = {"uId": user_id, "blueprintId": blueprint_id, "startTime": now,
                             "endTime": now + int(blueprint.get("craftDuration", 0)), "active": 1}

    obj["crafting"] = json_data["crafting"]
    obj["mat"] = materials
    obj["uObj"] = json_data["uObj"]


def handle_craftingCollect(request, user_id, obj, json_data, config_data):
    crafting = _running(json_data)
    if int(crafting.get("endTime", 0)) > int(time.time()):
        raise ZooError(INVALID_REQUEST, "the craft isn't finished", resync=("crafting",))
    blueprint = _blueprint(config_data, crafting["blueprintId"])
    reward = blueprint.get("reward", {})

    json_data["uObj"]["uEp"] += int(reward.get("xp", 0))
    item = reward.get("item")
    if item:
        rewardUtils.give_reward({"type": item["type"], "id": item["id"], "cnt": 1}, user_id, obj, json_data, config_data)

    json_data["crafting"] = {"active": 0}
    obj["craftingReward"] = {"xp": int(reward.get("xp", 0)), "item": item or {}}
    obj["crafting"] = json_data["crafting"]
    obj["uObj"] = json_data["uObj"]


def handle_craftingCollectInstant(request, user_id, obj, json_data, config_data):
    crafting = _running(json_data)
    now = int(time.time())
    if int(crafting.get("endTime", 0)) > now:
        shopUtils.reduce_real_currency(int(_blueprint(config_data, crafting["blueprintId"]).get("craftInstantReal", 0)), json_data)
        crafting["endTime"] = now
    obj["crafting"] = crafting
    obj["uObj"] = json_data["uObj"]


def handle_craftingTimeDecrease(request, user_id, obj, json_data, config_data):
    crafting = _running(json_data)
    now = int(time.time())
    if int(crafting.get("endTime", 0)) <= now:
        raise ZooError(INVALID_REQUEST, "the craft is already finished", resync=("crafting",))
    rewardUtils.take_resource(json_data, CRAFTING_BOOSTER, 1)
    crafting["endTime"] = now + (int(crafting["endTime"]) - now) // 2
    obj["crafting"] = crafting
    obj["res"] = json_data["res"]
