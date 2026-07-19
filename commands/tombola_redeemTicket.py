import random
import time
from utils import constantsUtils
from utils.shopUtils import reduce_real_currency
from utils.constantsUtils import TOMBOLA_TICKET_PRICE

SLOTS = ["1", "2", "3", "4", "5", "6", "7", "8"]
RARE_REWARDS = None

def collect_rare_rewards(config_data):
    global RARE_REWARDS
    RARE_REWARDS = []
    for item_type in ["animals", "decos", "cages"]:
        for item_id, item in config_data["gameItems"][item_type].items():
            if "inTombola" in item and item["inTombola"] == 1 and item["buyVirtual"] == 0:
                RARE_REWARDS.append({"type": item_type, "id": item_id})

def reshuffle_tombola_rewards(json_data, config_data):
    # Yellow slots (1 and 5): Special items (the ones with "inTombola": 1)
    # Green slot 2: Basic resources
    # Blue slot 3: "Super" resources + blueprints
    # Red slot 4: Coins + xp
    # Green slot 6: Powerups + coins, xp, event tokens, paws + common cages (assuming the ones with silver coins)
    # Blue slot 7: "Super" resources + blueprints + common animals (silver coins)
    # Red slot 8: coins, xp, event tokens, paws + assistants

    if RARE_REWARDS is None:
        collect_rare_rewards(config_data)
    
    # Slots 1 and 5
    for slot in ["1", "5"]:
        reward = random.choice(RARE_REWARDS)
        json_data["uTObj"]["r"][slot] = {"type": reward["type"], "id": reward["id"], "cnt": 1}

    # Slot 2
    random_id = random.randint(1, 7)
    max_count = json_data["res"][str(random_id)]["mCnt"]
    percentage_of_max = random.uniform(0.1, 0.2) # Random percentage between 10% and 20%
    json_data["uTObj"]["r"]["2"] = {"type": "resources", "id": random_id, "cnt": max(1, int(max_count * percentage_of_max))}

def handle_tombolaRedeemTicket(request, user_id, obj, json_data, config_data):
    result_slot = random.choices(SLOTS, weights=constantsUtils.TOMBOLA_WEIGHTS, k=1)[0]
    result = json_data["uTObj"]["r"][result_slot]
    
    json_data["uTObj"]["p"] = result

    # Give rewards
    if result["type"] == "resources":
        json_data["res"][str(result["id"])]["cnt"] += result["cnt"]
        obj["res"] = json_data["res"]

    elif result["type"] == "decos":
        new_deco = constantsUtils.get_empty_deco()
        new_deco["id"] = json_data["next_object_id"]
        new_deco["uId"] = user_id
        new_deco["fId"] = 0 # Inventory
        new_deco["dId"] = result["id"]
        new_deco["x"] = 0
        new_deco["y"] = 0
        new_deco["r"] = 0
        new_deco["build"] = 0
    
        json_data["next_object_id"] += 1
        json_data["fObj"]["decos"]["0"][str(new_deco["id"])] = new_deco
        obj["fObj"] = json_data["fObj"]

    elif result["type"] == "user":
        if result["id"] == "0": # Virtual currency
            json_data["uObj"]["uCv"] += result["cnt"]
        elif result["id"] == "1": # Real currency
            json_data["uObj"]["uCr"] += result["cnt"]
        elif result["id"] == "2": # XP
            json_data["uObj"]["uEp"] += result["cnt"]
        obj["uObj"] = json_data["uObj"]

    elif result["type"] == "animals":
        new_animal = constantsUtils.get_empty_animal()
        new_animal["id"] = json_data["next_object_id"]
        new_animal["uId"] = user_id
        new_animal["fId"] = 0 # Inventory
        new_animal["cId"] = 0
        new_animal["aId"] = result["id"]
        new_animal["sId"] = config_data["gameItems"]["animals"][str(result["id"])]["speciesId"]

        json_data["next_object_id"] += 1
        json_data["animals"]["0"][str(new_animal["id"])] = new_animal
        obj["fObj"] = json_data["fObj"]

    elif result["type"] == "powerUps":
        current_time = time.time()
        found = False
        for p in json_data["pwrUp"]:
            if p["pId"] == result["id"] and p["endTime"] > current_time:
                # If user already has this powerup and it's still active, extend the time
                found = True
                p["lastActivated"] = current_time
                p["endTime"] += config_data["gameItems"]["pwrUpConf"][str(result["id"])]["time"]
                break

        if not found:
            new_powerup = constantsUtils.get_empty_powerup()
            new_powerup["id"] = json_data["next_object_id"]
            new_powerup["uId"] = user_id
            new_powerup["pId"] = result["id"]
            new_powerup["inUse"] = 0
            new_powerup["lastActivated"] = current_time
            new_powerup["endTime"] = current_time + config_data["gameItems"]["pwrUpConf"][str(result["id"])]["time"]

            json_data["next_object_id"] += 1
            json_data["pwrUp"].append(new_powerup)
            
        obj["pwrUp"] = json_data["pwrUp"]

    reshuffle_tombola_rewards(json_data, config_data)

    # Send to game
    obj["uTObj"] = json_data["uTObj"]
    