import random
import time
from utils import constantsUtils, fieldItemUtils, resourceUtils, rewardUtils
from utils.zooErrors import ZooError, INVALID_REQUEST
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
    # One spin per ticket (uTObj.t, bought with tombola.bTT). The client shows
    # the spin button while t > 0, so t has to go down, or it keeps spinning.
    tombola = json_data["uTObj"]
    if int(tombola.get("t", 0)) <= 0:
        raise ZooError(INVALID_REQUEST, "no fortune wheel ticket", resync=("uTObj", "uObj"))
    tombola["t"] = int(tombola["t"]) - 1

    result_slot = random.choices(SLOTS, weights=constantsUtils.TOMBOLA_WEIGHTS, k=1)[0]
    result = tombola["r"][result_slot]
    tombola["p"] = result

    # Every prize type the wheel offers (decos, cages, animals, resources,
    # user = coins/real/xp, powerUps, assists) goes through the shared reward
    # code: items land in the inventory, resources stop at the storage limit.
    rewardUtils.give_reward({"type": result["type"], "id": result["id"], "cnt": result.get("cnt", 1)},
                            user_id, obj, json_data, config_data)
    if result["type"] in ("resources", "resource"):
        obj["res"] = json_data["res"]
    obj["uObj"] = json_data["uObj"]

    reshuffle_tombola_rewards(json_data, config_data)

    # Send to game
    obj["uTObj"] = json_data["uTObj"]
    