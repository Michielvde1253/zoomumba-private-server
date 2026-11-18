import time

from utils import shopUtils, dropUtils, questUtils, constantsUtils

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
    return int(json_data.get("pfObj", {}).get(str(field_id), {}).get("fType", 1)) == constantsUtils.OCEAN_FIELD_TYPE


def is_sick(cage):
    return 0 < cage.get("health", 0) <= now()


def food_left(cage, species):
    return max(0, cage.get("feed", 0) - now()) / max(1, species["feedTime"])


def cost_of(json_data, config_data, cage, action, field_id):
    species = species_config(config_data, cage)
    count = animal_count(cage)
    ocean = is_ocean(json_data, field_id)
    return {
        "feed": [(species["foodId"], species["foodPerAnimal"] * count)],
        "water": [(constantsUtils.WATER, species["waterPerAnimal"] * count)],
        "clean": [],
        "cuddle": [],
        "heal": [(constantsUtils.MEDICINE, count)],
        "superfeed": [(constantsUtils.OCEAN_SUPERFOOD if ocean else constantsUtils.SUPERFOOD, 1)],
        "powerfeed": [(constantsUtils.OCEAN_POWERFOOD if ocean else constantsUtils.POWERFOOD, 1)],
        "superheal": [(constantsUtils.SUPERMEDICINE, 1)],
    }[action]


# for assistants to check if a cage needs smth
def needs(config_data, cage, action):
    species = species_config(config_data, cage)
    if species is None or animal_count(cage) == 0 or cage.get("build", 0) > now():
        return False
    t = now()
    if action in ("feed", "water", "clean", "cuddle"):
        return cage.get(action, 0) <= t
    if action in ("superfeed", "powerfeed"):
        return food_left(cage, species) < constantsUtils.SUPER_ACTION_THRESHOLD
    if action in ("heal", "superheal"):
        return is_sick(cage)
    return False


def can_afford(json_data, costs):
    return all(json_data.get("res", {}).get(str(rid), {}).get("cnt", 0) >= amount for rid, amount in costs)


def perform(obj, json_data, config_data, cage, action, field_id, xp_bonus=0.0):
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
