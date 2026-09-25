import time

from utils import constantsUtils, fieldItemUtils as items
from utils.zooErrors import ZooError, INVALID_REQUEST

# collection.rs: {"type": "species" | "cages" | "assists" | "events", "id": <set id>, "rId": 1 | 2}
# Turns in one of each item of a completed collection set for one of its two
# rewards (collSetConf.<type>.<id>.rewards.<rId>).
#
# The client already took the items off its own counts and added a user or
# resource reward (GetCollectionRewardCommand); decos, stores, materials,
# assistants and powerups only show up when the server sends them. We always
# send back what changed so the server's numbers win.

# The client already changed these optimistically; resend them if we refuse
RESYNC = ("collItems", "uObj", "res")

# uObj field for each "user" reward id (UserResources.as)
USER_FIELDS = {0: "uCv", 1: "uCr", 2: "uEp", 3: "pPaw", 4: "pearls"}


def find_set(config_data, set_type, set_id):
    sets = config_data.get("collSetConf", {})
    if set_type == "events":
        # collSetConf.specials.events: the client files these under Categories.EVENTS
        return sets.get("specials", {}).get("events", {}).get(str(set_id))
    if set_type in ("species", "cages", "assists"):
        return sets.get(set_type, {}).get(str(set_id))
    return None


def handle_collectionRs(request, user_id, obj, json_data, config_data):
    collection_set = find_set(config_data, request.get("type"), request.get("id"))
    if collection_set is None:
        raise ZooError(INVALID_REQUEST, f"no collection set {request.get('type')} {request.get('id')}", resync=RESYNC)
    reward = collection_set.get("rewards", {}).get(str(request.get("rId")))
    if reward is None:
        raise ZooError(INVALID_REQUEST, f"collection set has no reward {request.get('rId')}", resync=RESYNC)

    owned = json_data.setdefault("collItems", {})
    missing = [i for i in collection_set["items"] if owned.get(str(i), {}).get("cnt", 0) < 1]
    if missing:
        raise ZooError(INVALID_REQUEST, f"collection set not complete, missing {missing}", resync=RESYNC)

    for item_id in collection_set["items"]:
        owned[str(item_id)]["cnt"] -= 1

    give_reward(reward, user_id, obj, json_data, config_data)
    obj["collItems"] = owned


def give_reward(reward, user_id, obj, json_data, config_data):
    kind, reward_id, amount = reward["type"], reward["id"], int(reward.get("amount", 1))

    if kind == "user":
        field = USER_FIELDS.get(int(reward_id))
        if field is None:
            raise ZooError(INVALID_REQUEST, f"unknown user reward {reward_id}")
        json_data["uObj"][field] = json_data["uObj"].get(field, 0) + amount
        obj["uObj"] = json_data["uObj"]

    elif kind in ("resource", "material"):
        key = "res" if kind == "resource" else "mat"
        store = json_data.setdefault(key, {})
        entry = store.setdefault(str(reward_id), {"uId": user_id, "id": int(reward_id), "cnt": 0, "mCnt": 250})
        entry["cnt"] += amount
        obj[key] = store

    elif kind == "collectionItem":
        entry = json_data["collItems"].setdefault(str(reward_id), {"uId": user_id, "id": int(reward_id), "cnt": 0})
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
