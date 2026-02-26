import random
import time
from utils import constantsUtils
from utils.shopUtils import reduce_real_currency
from utils.constantsUtils import TOMBOLA_TICKET_PRICE

def handle_tombolaRedeemTicket(request, user_id, obj, json_data, config_data):
    slots = ["1", "2", "3", "4", "5", "6", "7", "8"]
    weights = [1, 49, 49, 28, 1, 49, 49, 28]
    result_slot = random.choices(slots, weights=weights, k=1)[0]
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
    # Send to game
    obj["uTObj"] = json_data["uTObj"]
    