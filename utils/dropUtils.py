"""
Paws (uObj.pPaw) and pearls (uObj.pearls) from cage actions.

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
    """Give the paws/pearls this cage action shows, then roll the next paw drop.
    Returns (paws, pearls) paid."""
    key, multiplier = CAGE_ACTION_DROPS.get(fia, (None, 1))
    drop = (cage.get("drops") or {}).get(key) if key else None
    if not isinstance(drop, dict):
        return 0, 0

    paws = pearls = 0
    if drop.get("pp"):
        paws = math.ceil(int(drop["pp"]) * multiplier * (1 + powerup_bonus(json_data, config_data, PET_PAWS)))
        json_data["uObj"]["pPaw"] = json_data["uObj"].get("pPaw", 0) + paws
    if drop.get("pl"):
        pearls = math.ceil(int(drop["pl"]) * multiplier * (1 + powerup_bonus(json_data, config_data, PEARLS)))
        json_data["uObj"]["pearls"] = json_data["uObj"].get("pearls", 0) + pearls

    if "pp" in drop and drop["pp"]:
        drop["pp"] = random.randint(*PAW_ROLL)
    return paws, pearls
