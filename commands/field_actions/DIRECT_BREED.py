from utils import shopUtils, fieldItemUtils as items


def handle_directBreed(request, user_id, obj, json_data, config_data, current_field_id):
    cage = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]
    
    cage["child"] += 1
    cage["breed"] = 0

    species_id = cage["sId"]
    config_data_for_species = config_data["gameItems"]["species"][str(species_id)]
    shopUtils.reduce_real_currency(config_data_for_species["directBreedReal"], json_data)

    # The baby needs its own animal record, or the client can't move it to the inventory
    items.sync_cage_animals(json_data, config_data, current_field_id, cage, user_id)

    # Send objects to game
    items.send_cage_with_animals(obj, json_data, current_field_id, cage)
    obj["uObj"] = json_data["uObj"]