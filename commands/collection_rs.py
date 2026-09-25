from utils.rewardUtils import give_reward
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
