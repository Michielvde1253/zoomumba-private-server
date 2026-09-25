from utils import fieldItemUtils as items


def handle_breedEnd(request, user_id, obj, json_data, config_data, current_field_id):
    cage = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]

    cage["child"] += 1
    cage["breed"] = 0

    # The baby needs its own animal record, or the client can't move it to the inventory
    items.sync_cage_animals(json_data, config_data, current_field_id, cage, user_id)
    items.send_cage_with_animals(obj, json_data, current_field_id, cage)
