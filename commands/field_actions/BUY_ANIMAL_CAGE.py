import time
from utils import shopUtils, constantsUtils

def handle_buyAnimalCage(request, user_id, obj, json_data, config_data, current_field_id):
    # Create field object if needed
    if str(current_field_id) not in json_data["animals"]:
        json_data["animals"][str(current_field_id)] = {}
    if str(request["id"]) not in json_data["animals"][str(current_field_id)]:
        json_data["animals"][str(current_field_id)][str(request["id"])] = {}

    # Initialize new animal
    new_animal = constantsUtils.get_empty_animal()
    new_animal["id"] = json_data["next_object_id"]
    new_animal["uId"] = user_id
    new_animal["fId"] = current_field_id
    new_animal["cId"] = request["id"]
    new_animal["aId"] = request["aId"]
    new_animal["sId"] = config_data["gameItems"]["animals"][str(request["aId"])]["speciesId"]

    json_data["next_object_id"] += 1

    json_data["animals"][str(current_field_id)][str(request["id"])][str(new_animal["id"])] = new_animal

    # Get cage
    cage = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]
    cage["sId"] = new_animal["sId"]

    current_time = int(time.time())

    # Get config data for animal + species
    config_data_for_animal = config_data["gameItems"]["animals"][str(request["aId"])]
    config_data_for_species = config_data["gameItems"]["animalsSpecies"][str(new_animal["sId"])]

    # Setup cage
    male = config_data_for_animal["male"]
    child = config_data_for_animal["child"]
    if male == 1:
        cage["male"] += 1
    elif child == 1:
        cage["child"] += 1
    else:
        cage["female"] += 1

    cage["clean"] = current_time + config_data_for_species["cleanTime"]
    cage["feed"] = current_time + config_data_for_species["feedTime"]
    cage["water"] = current_time + config_data_for_species["waterTime"]
    cage["cuddle"] = current_time + config_data_for_species["cuddleTime"]
    cage["sick"] = current_time
    cage["health"] = current_time + config_data_for_species["healthTime"]

    # Buy item
    shopUtils.buy_from_shop(config_data_for_animal, json_data["uObj"]["uLvl"], json_data)

    # Send objects to game
    if "fObj" not in obj:
        obj["fObj"] = {}
    if "cages" not in obj["fObj"]:
        obj["fObj"]["cages"] = {}
    if current_field_id not in obj["fObj"]["cages"]:
        obj["fObj"]["cages"][current_field_id] = {}
    obj["fObj"]["cages"][current_field_id][str(request["id"])] = cage
    obj["uObj"] = json_data["uObj"]
    obj["animals"] = json_data["animals"]