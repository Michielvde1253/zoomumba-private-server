import math
import time

def is_item_unlocked(config_data_for_item, user_level):
    if config_data_for_item["buyable"] != 1:
        return -1
    if config_data_for_item["onlyDev"] == 1:
        return -1
    if user_level >= config_data_for_item["userLevelRequired"] and config_data_for_item["buyVirtual"] != 0:
        return 1
    if config_data_for_item["buyReal"] != 0:
        return 0
    return -1

def buy_from_shop(config_data_for_item, user_level, json_data):
    is_unlocked = is_item_unlocked(config_data_for_item, user_level)
    if is_unlocked == 1:
        # Buy with virtual currency
        if (json_data["uObj"]["uCv"] - config_data_for_item["buyVirtual"]) >= 0:
            json_data["uObj"]["uCv"] -= config_data_for_item["buyVirtual"]
        else:
            # to-do: disconnect user
            print("Negative resources")
    elif is_unlocked == 0:
        # Buy with real currency
        if (json_data["uObj"]["uCr"] - config_data_for_item["buyReal"]) >= 0:
            json_data["uObj"]["uCr"] -= config_data_for_item["buyReal"]
        else:
            # to-do: disconnect user
            print("Negative resources")

def buy_multiple_from_shop(config_data_for_item, user_level, json_data, amount):
    is_unlocked = is_item_unlocked(config_data_for_item, user_level)
    if is_unlocked == 1:
        # Buy with virtual currency
        if (json_data["uObj"]["uCv"] - amount * config_data_for_item["buyVirtual"]) >= 0:
            json_data["uObj"]["uCv"] -= amount * config_data_for_item["buyVirtual"]
        else:
            # to-do: disconnect user
            print("Negative resources")
    elif is_unlocked == 0:
        # Buy with real currency
        if (json_data["uObj"]["uCr"] - amount * config_data_for_item["buyReal"]) >= 0:
            json_data["uObj"]["uCr"] -= amount * config_data_for_item["buyReal"]
        else:
            # to-do: disconnect user
            print("Negative resources")

def get_percentage(timestamp, total_time):
    # Calculates which percentage of the cuddle/feed/etc. bar is filled
    current_time = int(time.time())
    if timestamp >= current_time:
        return 1 - (timestamp - current_time) / total_time
    return 1

def get_exp_proportional_value(temp, percentage, input):
    res = 1
    for value in input:
        res += value
    print(input)
    print(temp)
    print(percentage)
    print(res)
    return int(temp * percentage * res)

def get_cage_calculated_xp(cage, action_type, config_data, user_level, count_animals):
    # Calculate the xp you get when feeding, cuddling, ... a cage.
    # https://github.com/Michielvde1253/zoomumba-client/blob/20248990cf91a0f12581a26079e8366331438748/com/bigpoint/zoomumba/model/app/gameEvents/UserResourcesProxy.as#L117
    cage_id = cage["cId"]
    species_id = cage["sId"]
    level = cage["level"]

    config_data_for_cage = config_data["gameItems"]["cages"][str(cage_id)]
    config_data_for_species = config_data["gameItems"]["animalsSpecies"][str(species_id)]
    upgrade_cage_config = config_data["main"]["ucObj"][str(level)]

    xp_bonus = upgrade_cage_config["xpBonus"]

    if config_data_for_species["cages"][str(cage_id)] == 2: # "Good" bonus
        attraction_cagebonus = 0.1
    else:
        attraction_cagebonus = 0

    level_frac = min(float(user_level) / float(config_data_for_cage["userLevelRequired"]), 1)

    result = 0

    match action_type:
        case "clean":
            temp = count_animals * config_data_for_species["cleanExpReward"] * level_frac
            result = get_exp_proportional_value(temp, get_percentage(cage["clean"], config_data_for_species["cleanTime"]), [xp_bonus, attraction_cagebonus])

        case "cuddle":
            temp = config_data_for_species["cuddleExpReward"]
            result = get_exp_proportional_value(temp, get_percentage(cage["cuddle"], config_data_for_species["cuddleTime"]), [xp_bonus, attraction_cagebonus])

        case "feed":
            temp = count_animals * config_data_for_species["feedExpReward"] * level_frac
            result = get_exp_proportional_value(temp, get_percentage(cage["feed"], config_data_for_species["feedTime"]), [xp_bonus, attraction_cagebonus])

        case "powerfeed":
            temp = count_animals * config_data_for_species["feedExpReward"] * level_frac
            result = get_exp_proportional_value(temp, 1, [xp_bonus, attraction_cagebonus])

        case "superfeed":
            temp = count_animals * config_data_for_species["feedExpReward"] * level_frac * 2
            result = get_exp_proportional_value(temp, 1, [xp_bonus, attraction_cagebonus])

        case "water":
            temp = count_animals * config_data_for_species["waterExpReward"] * level_frac
            result = get_exp_proportional_value(temp, get_percentage(cage["water"], config_data_for_species["waterTime"]), [xp_bonus, attraction_cagebonus])

        case "breed":
            result = math.floor(config_data_for_species["breedExp"] * (1 + xp_bonus + attraction_cagebonus))

    print(f"[DEBUG] Rewarded xp: {result}")
    return result