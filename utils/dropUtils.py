"""
Paws (uObj.pPaw), pearls (uObj.pearls) and collection items (collItems)
from cage actions.

Every cage carries pre-rolled rewards per action in cage.drops.<key>
("pp" = paws, "pl" = pearls). When the player acts on a cage the client shows
a paw drop worth that amount straight away (GenerateDropsCommand), but it
never adds it to its paw counter itself: the counter only changes when the
server sends uObj.pPaw. So the server has to pay out the same amount and roll
the next one, which reaches the client with the cage.
"""
import math
import random
import time

# field.fia action -> (cage.drops key, action multiplier from GenerateDropsCommand)
CAGE_ACTION_DROPS = {
    "fAC": ("fe", 1),
    "wAC": ("wa", 1),
    "cAC": ("cl", 1),
    "cuAC": ("cu", 1),
    "hAC": ("hl", 1),
    "beAC": ("eb", 1),
    "bdAC": ("db", 2),   # instant breed counts as SUPERBREAD
    "sfAC": ("sf", 1),
    "pfAC": ("pf", 4),   # power feed
    "shAC": ("sh", 2),   # super heal
}

# UserResources.as
PET_PAWS, PEARLS = 3, 4

# Chance that an action's next drop carries a collection item. Rough rates
# from the HAR capture (57 cages): clean ~19%, the others 2-9%.
COLLECTABLE_CHANCE = {"cl": 0.2, "cu": 0.05, "fe": 0.05, "wa": 0.05, "sf": 0.05, "pf": 0.08}

# New paw amount rolled after each payout. The config has no per-species
# range, so this matches what the original server handed out (HAR: mostly 5-12).
PAW_ROLL = (5, 12)


def powerup_bonus(json_data, config_data, resource_id):
    """Sum of 'mod' of the running powerups that boost this user resource
    (PowerupProxy.getMultiplierByAffectedProperty)."""
    bonus, now = 0.0, time.time()
    for powerup in json_data.get("pwrUp") or []:
        if powerup.get("endTime", 0) <= now:
            continue
        affects = config_data["gameItems"]["pwrUpConf"].get(str(powerup.get("pId")), {}).get("affects")
        if isinstance(affects, dict) and affects.get("type") == "user" and resource_id in affects.get("id", []) \
                and affects.get("mod", 0) > 0:
            bonus += affects["mod"]
    return bonus


def pay_cage_action(json_data, config_data, cage, fia):
    """Give the paws, pearls and collection item this cage action shows, then
    roll the next ones. Returns (paws, pearls, collItems entry or None)."""
    key, multiplier = CAGE_ACTION_DROPS.get(fia, (None, 1))
    drop = (cage.get("drops") or {}).get(key) if key else None
    if not isinstance(drop, dict):
        return 0, 0, None

    paws = pearls = 0
    if drop.get("pp"):
        paws = math.ceil(int(drop["pp"]) * multiplier * (1 + powerup_bonus(json_data, config_data, PET_PAWS)))
        json_data["uObj"]["pPaw"] = json_data["uObj"].get("pPaw", 0) + paws
    if drop.get("pl"):
        pearls = math.ceil(int(drop["pl"]) * multiplier * (1 + powerup_bonus(json_data, config_data, PEARLS)))
        json_data["uObj"]["pearls"] = json_data["uObj"].get("pearls", 0) + pearls

    collected = None
    if isinstance(drop.get("col"), dict) and drop["col"].get("id"):
        collected = give_collectable(json_data, drop["col"]["id"], int(drop["col"].get("amount", 1)))

    if "pp" in drop and drop["pp"]:
        drop["pp"] = random.randint(*PAW_ROLL)
    if key in COLLECTABLE_CHANCE:
        drop["col"] = roll_collectable(config_data, cage, key)
    return paws, pearls, collected


# ---- collection items (drops.<key>.col) ----

def collectable_pool(config_data, cage):
    """Collection items a cage can drop: its species' set and its cage type's
    set (collSetConf.species / .cages; every col drop in the HAR is from one)."""
    sets = config_data.get("collSetConf", {})
    pool = list(sets.get("cages", {}).get(str(cage.get("cId")), {}).get("items", []))
    if cage.get("sId"):
        pool += sets.get("species", {}).get(str(cage["sId"]), {}).get("items", [])
    return pool


def roll_collectable(config_data, cage, key):
    pool = collectable_pool(config_data, cage)
    if pool and random.random() < COLLECTABLE_CHANCE.get(key, 0):
        return {"id": random.choice(pool), "amount": 1}
    return 0


def roll_collectables(config_data, cage):
    """Re-roll every action's collection item, e.g. when a cage gets its species."""
    for key in COLLECTABLE_CHANCE:
        drop = (cage.get("drops") or {}).get(key)
        if isinstance(drop, dict):
            drop["col"] = roll_collectable(config_data, cage, key)


def give_collectable(json_data, item_id, amount):
    """Add to collItems. The client adds the drop to its own count when the
    drop flies into the collection panel, and push.get resends collItems, so
    the action's response doesn't carry it (that would count it twice)."""
    items = json_data.setdefault("collItems", {})
    entry = items.setdefault(str(item_id), {"uId": json_data["uObj"].get("uId", 0), "id": int(item_id), "cnt": 0})
    entry["cnt"] += amount
    return entry
