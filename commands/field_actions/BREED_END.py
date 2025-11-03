def handle_breedEnd(request, user_id, obj, json_data, config_data, current_field_id):
    cage = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]

    cage["child"] += 1
    cage["breed"] = 0 

    obj["fObj"] = json_data["fObj"]