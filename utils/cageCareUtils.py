"""
Caring for one cage: feed, water, clean, cuddle, heal, super/power feed and
super heal. Used by the manual actions and by the assistants, which run the
same thing over every cage of the zoo that needs it.

Timestamps on a cage are "good until": feed/water/clean/cuddle run out at
that time, and the animals get sick once `health` has passed. Heal and super
heal follow CageHealActionCommand / CageInstantHealActionCommand:
  heal:       sick = now + sickTime, health = now + healthTime + sickTime
  super heal: sick = 0,              health = now + healthTime + 2 * sickTime
Super and power feed cost one superfood / powerfood (super_fishfood /
power_fishfood in the ocean zoo) and refill `feed` with the normal feedTime;
the config has no superFeedTime/powerFeedTime, so the client uses feedTime too.
"""
import time

from utils import shopUtils, dropUtils, questUtils

# Resource ids (gameItems.resources)
WATER, MEDICINE, SUPERFOOD, SUPERMEDICINE, POWERFOOD = 1, 7, 8, 9, 10
OCEAN_SUPERFOOD, OCEAN_POWERFOOD = 21, 22
OCEAN_FIELD_TYPE = 6  # PlayFieldsTypes.FIELD_TYPE_OCEANWORLD_ZOO

# Super/power feed only once food is below this share (MainConfig.PERCENTAGE_FOR_SUPER_ACTIONS)
SUPER_ACTION_THRESHOLD = 0.8

# action -> (fia used for drops/quests, xp action name for shopUtils.get_cage_calculated_xp)
ACTION_INFO = {
    "feed": ("fAC", "feed"),
    "water": ("wAC", "water"),
    "clean": ("cAC", "clean"),
    "cuddle": ("cuAC", "cuddle"),
    "heal": ("hAC", None),
    "superfeed": ("sfAC", "superfeed"),
    "powerfeed": ("pfAC", "powerfeed"),
    "superheal": ("shAC", None),
}


def now():
    return int(time.time())


def animal_count(cage):
    return cage.get("male", 0) + cage.get("female", 0) + cage.get("child", 0)


def species_config(config_data, cage):
    return config_data["gameItems"]["animalsSpecies"].get(str(cage.get("sId", 0)))


def is_ocean(json_data, field_id):
    return int(json_data.get("pfObj", {}).get(str(field_id), {}).get("fType", 1)) == OCEAN_FIELD_TYPE


def is_sick(cage):
    return 0 < cage.get("health", 0) <= now()


def food_left(cage, species):
    return max(0, cage.get("feed", 0) - now()) / max(1, species["feedTime"])


def cost_of(json_data, config_data, cage, action, field_id):
    """[(resource id, amount)] the action uses on this cage."""
    species = species_config(config_data, cage)
    count = animal_count(cage)
    ocean = is_ocean(json_data, field_id)
    return {
        "feed": [(species["foodId"], species["foodPerAnimal"] * count)],
        "water": [(WATER, species["waterPerAnimal"] * count)],
        "clean": [],
        "cuddle": [],
        "heal": [(MEDICINE, count)],
        "superfeed": [(OCEAN_SUPERFOOD if ocean else SUPERFOOD, 1)],
        "powerfeed": [(OCEAN_POWERFOOD if ocean else POWERFOOD, 1)],
        "superheal": [(SUPERMEDICINE, 1)],
    }[action]


def needs(config_data, cage, action):
    """Does an assistant have anything to do on this cage?"""
    species = species_config(config_data, cage)
    if species is None or animal_count(cage) == 0 or cage.get("build", 0) > now():
        return False
    t = now()
    if action in ("feed", "water", "clean", "cuddle"):
        return cage.get(action, 0) <= t
    if action in ("superfeed", "powerfeed"):
        return food_left(cage, species) < SUPER_ACTION_THRESHOLD
    if action in ("heal", "superheal"):
        return is_sick(cage)
    return False


def can_afford(json_data, costs):
    return all(json_data.get("res", {}).get(str(rid), {}).get("cnt", 0) >= amount for rid, amount in costs)


def perform(obj, json_data, config_data, cage, action, field_id, xp_bonus=0.0):
    """Do `action` on the cage if the player has what it costs. Returns True if done."""
    species = species_config(config_data, cage)
    if species is None or animal_count(cage) == 0:
        return False
    costs = cost_of(json_data, config_data, cage, action, field_id)
    if not can_afford(json_data, costs):
        return False

    fia, xp_action = ACTION_INFO[action]
    if xp_action and json_data["uObj"].get("uTut", 0) == 0:  # no xp during the tutorial
        xp = shopUtils.get_cage_calculated_xp(cage, xp_action, config_data, json_data["uObj"]["uLvl"], animal_count(cage))
        json_data["uObj"]["uEp"] += int(xp * (1 + xp_bonus))
    for resource_id, amount in costs:
        json_data["res"][str(resource_id)]["cnt"] -= amount

    t = now()
    if action in ("feed", "superfeed", "powerfeed"):
        cage["feed"] = t + species["feedTime"]
    elif action in ("water", "clean", "cuddle"):
        cage[action] = t + species[f"{action}Time"]
    elif action == "heal":
        cage["sick"] = t + species["sickTime"]
        cage["health"] = t + species["healthTime"] + species["sickTime"]
    elif action == "superheal":
        cage["sick"] = 0
        cage["health"] = t + species["healthTime"] + 2 * species["sickTime"]

    dropUtils.pay_cage_action(json_data, config_data, cage, fia)
    questUtils.count_cage_action(obj, json_data, cage, fia)
    return True
