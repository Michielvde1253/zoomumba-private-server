"""
Handing out rewards given as {"type", "id", "amount"} (collection sets) or
{"type", "id", "cnt"} (breeding lab, quests...), and charging costs given the
same way. Types: user (id 0 coins, 1 real, 2 xp, 3 paws, 4 pearls), resource,
material, collectionItem, decor, store, assist (hours), powerUps.
"""
import time

from utils import constantsUtils, resourceUtils, fieldItemUtils as items
from utils.zooErrors import ZooError, INVALID_REQUEST, NOT_ENOUGH_MONEY, NOT_ENOUGH_RESOURCES

# uObj field for each "user" reward id (UserResources.as; ocean coins (5) are uCv too)
USER_FIELDS = {0: "uCv", 1: "uCr", 2: "uEp", 3: "pPaw", 4: "pearls", 5: "uCv"}


def amount_of(entry):
    return int(entry.get("amount", entry.get("cnt", 1)))


def pay_cost(json_data, cost):
    """Charge a {"type": "user"|"resource", "id", "cnt"} cost."""
    kind, cost_id, amount = cost.get("type"), int(cost["id"]), amount_of(cost)
    if kind == "user":
        field = USER_FIELDS[cost_id]
        if json_data["uObj"].get(field, 0) < amount:
            raise ZooError(NOT_ENOUGH_MONEY)
        json_data["uObj"][field] -= amount
    elif kind in ("resource", "resources", 13):
        take_resource(json_data, cost_id, amount)
    else:
        raise ZooError(INVALID_REQUEST, f"unknown cost type {kind}")


def take_resource(json_data, resource_id, amount):
    resource = json_data.get("res", {}).get(str(resource_id))
    if resource is None or resource["cnt"] < amount:
        raise ZooError(NOT_ENOUGH_RESOURCES, resync=("res", "uObj"))
    resource["cnt"] -= amount


def give_reward(reward, user_id, obj, json_data, config_data):
    kind, reward_id, amount = reward["type"], reward["id"], amount_of(reward)

    if kind == "user":
        field = USER_FIELDS.get(int(reward_id))
        if field is None:
            raise ZooError(INVALID_REQUEST, f"unknown user reward {reward_id}")
        json_data["uObj"][field] = json_data["uObj"].get(field, 0) + amount
        obj["uObj"] = json_data["uObj"]

    elif kind in ("resource", "resources", 13):
        resourceUtils.add_resource(json_data, reward_id, amount, user_id)  # over the storage limit is lost
        obj["res"] = json_data["res"]

    elif kind == "material":
        store = json_data.setdefault("mat", {})
        entry = store.setdefault(str(reward_id), {"uId": user_id, "id": int(reward_id), "cnt": 0, "mCnt": 250})
        entry["cnt"] += amount  # the client doesn't cap materials either
        obj["mat"] = store

    elif kind in ("collectionItem", "collectionItems", 18):
        entry = json_data.setdefault("collItems", {}).setdefault(str(reward_id), {"uId": user_id, "id": int(reward_id), "cnt": 0})
        entry["cnt"] += amount

    elif kind in ("decor", "store"):
        key, id_field = ("decos", "dId") if kind == "decor" else ("stores", "stId")
        template = constantsUtils.get_empty_deco if kind == "decor" else constantsUtils.get_empty_store
        inventory = items.get_items(json_data, key, items.INVENTORY_FIELD)
        for _ in range(amount):
            item = template()
            item.update({"id": json_data["next_object_id"], "uId": user_id, "fId": 0, id_field: int(reward_id),
                         "x": 0, "y": 0, "r": 0, "act": 0, "build": 0})
            json_data["next_object_id"] += 1
            inventory[str(item["id"])] = item
            items.send_item(obj, key, items.INVENTORY_FIELD, item)

    elif kind == "assist":
        # amount is hours (CollectionSetRewordWindowMediator shows count * 3600 s)
        now = int(time.time())
        assistants = json_data.setdefault("asObj", {})
        entry = assistants.setdefault(str(reward_id), {"asId": str(reward_id), "end": "0", "nL": "1"})
        entry["end"] = str(max(now, int(entry.get("end") or 0)) + amount * 3600)
        obj["asObj"] = assistants

    elif kind == "powerUps":
        give_powerup(int(reward_id), user_id, json_data, config_data)
        obj["pwrUp"] = json_data["pwrUp"]

    else:
        raise ZooError(INVALID_REQUEST, f"unknown reward type {kind}")


def give_powerup(powerup_id, user_id, json_data, config_data):
    """Start the powerup, or extend it if it's already running (as tombola.rTT does)."""
    now = int(time.time())
    duration = config_data["gameItems"]["pwrUpConf"][str(powerup_id)]["time"]
    powerups = json_data.setdefault("pwrUp", [])
    for powerup in powerups:
        if powerup["pId"] == powerup_id and powerup["endTime"] > now:
            powerup["lastActivated"] = now
            powerup["endTime"] += duration
            return
    powerup = constantsUtils.get_empty_powerup()
    powerup.update({"id": json_data["next_object_id"], "uId": user_id, "pId": powerup_id,
                    "inUse": 0, "lastActivated": now, "endTime": now + duration})
    json_data["next_object_id"] += 1
    powerups.append(powerup)
