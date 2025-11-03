from utils import shopUtils


def handle_directBreed(request, user_id, obj, json_data, config_data, current_field_id):
    cage = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]
    
    cage["child"] += 1
    cage["breed"] = 0

    species_id = cage["sId"]
    config_data_for_species = config_data["gameItems"]["species"][str(species_id)]
    shopUtils.reduce_real_currency(config_data_for_species["directBreedReal"], json_data)