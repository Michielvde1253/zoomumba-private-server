import time
from utils import shopUtils

def handle_feedWaterAnimalCage(request, user_id, obj, json_data, config_data, current_field_id):
    current_time = int(time.time())

    cage = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]

    species_id = cage["sId"]
    config_data_for_species = config_data["gameItems"]["animalsSpecies"][str(species_id)]

    # To-do: is there a better way to count the animals?
    count_males = cage["male"]
    count_females = cage["female"]
    count_childs = cage["child"]
    count_total = count_males + count_females + count_childs

    if request["fia"] == "fAC":
        food_id = config_data_for_species["foodId"]
        food_per_animal = config_data_for_species["foodPerAnimal"]
    elif request["fia"] == "wAC":
        food_id = 1
        food_per_animal = config_data_for_species["waterPerAnimal"]

    total_food_cost = food_per_animal * count_total

    if json_data["res"][str(food_id)]["cnt"] >= total_food_cost:

        if request["fia"] == "fAC":
            if json_data["uObj"]["uTut"] == 0: # During tutorial no exp is given
                json_data["uObj"]["uEp"] += shopUtils.get_cage_calculated_xp(cage, "feed", config_data, json_data["uObj"]["uLvl"], count_total)

            cage["feed"] = current_time + config_data_for_species["feedTime"]

        elif request["fia"] == "wAC":
            if json_data["uObj"]["uTut"] == 0: # During tutorial no exp is given
                json_data["uObj"]["uEp"] += shopUtils.get_cage_calculated_xp(cage, "water", config_data, json_data["uObj"]["uLvl"], count_total)

            cage["water"] = current_time + config_data_for_species["waterTime"]

        json_data["res"][str(food_id)]["cnt"] -= total_food_cost

    obj["uObj"] = json_data["uObj"]
    obj["fObj"] = json_data["fObj"]
    obj["res"] = json_data["res"]