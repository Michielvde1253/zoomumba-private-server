def handle_breedEnd(request, user_id, obj, json_data, config_data, current_field_id):
    cage = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]

    cage["child"] += 1
    cage["breed"] = 0 

    if "fObj" not in obj:
        obj["fObj"] = {}
    if "cages" not in obj["fObj"]:
        obj["fObj"]["cages"] = {}
    if current_field_id not in obj["fObj"]["cages"]:
        obj["fObj"]["cages"][current_field_id] = {}
    obj["fObj"]["cages"][current_field_id][str(request["id"])] = cage