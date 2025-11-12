import time
from utils import shopUtils

def handle_cleanCuddleAnimalCage(request, user_id, obj, json_data, config_data, current_field_id):
    current_time = int(time.time())

    cage = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]

    species_id = cage["sId"]
    config_data_for_species = config_data["gameItems"]["animalsSpecies"][str(species_id)]

    # To-do: is there a better way to count the animals?
    count_males = cage["male"]
    count_females = cage["female"]
    count_childs = cage["child"]
    count_total = count_males + count_females + count_childs

    if request["fia"] == "cAC":
        if json_data["uObj"]["uTut"] == 0: # During tutorial no exp is given
            json_data["uObj"]["uEp"] += shopUtils.get_cage_calculated_xp(cage, "clean", config_data, json_data["uObj"]["uLvl"], count_total)

        cage["clean"] = current_time + config_data_for_species["cleanTime"]

    elif request["fia"] == "cuAC":
        if json_data["uObj"]["uTut"] == 0: # During tutorial no exp is given
            json_data["uObj"]["uEp"] += shopUtils.get_cage_calculated_xp(cage, "cuddle", config_data, json_data["uObj"]["uLvl"], count_total)

        cage["cuddle"] = current_time + config_data_for_species["cuddleTime"]

    obj["uObj"] = json_data["uObj"]
    if "fObj" not in obj:
        obj["fObj"] = {}
    if "cages" not in obj["fObj"]:
        obj["fObj"]["cages"] = {}
    if current_field_id not in obj["fObj"]["cages"]:
        obj["fObj"]["cages"][current_field_id] = {}
    obj["fObj"]["cages"][current_field_id][str(request["id"])] = cage
    obj["res"] = json_data["res"]