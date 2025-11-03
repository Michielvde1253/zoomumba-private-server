import time
from utils import shopUtils

def handle_breedStart(request, user_id, obj, json_data, config_data, current_field_id):
    cage = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]
    species_id = cage["sId"]
    config_data_for_species = config_data["gameItems"]["species"][str(species_id)]
    
    cage["breed"] = int(time.time()) + config_data_for_species["breedTime"]

    shopUtils.reduce_virtual_currency(config_data_for_species["breedCostVirtual"], json_data)

    obj["uObj"] = json_data["uObj"]