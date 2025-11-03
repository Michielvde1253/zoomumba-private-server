from field_actions import *

available_field_actions = {
    "bC": handle_buyCage,
    "bAC": handle_buyAnimalCage,
    "bR": handle_buyRoad,
    "bD": handle_buyDeco,
    "bIr": handle_buyResource,
    "bSt": handle_buyStore,
    "fAC": handle_feedWaterAnimalCage,
    "wAC": handle_feedWaterAnimalCage,
    "cAC": handle_cleanCuddleAnimalCage,
    "cuAC": handle_cleanCuddleAnimalCage,
    "bdAC": handle_directBreed,
    "bsAC": handle_breedStart,
    "beAC": handle_breedEnd,
    "cEf": handle_collectEntranceFee,
    "cSt": handle_collectStoreMoney,
    "mC": handle_moveCage,
    "mR": handle_moveRoad
}

def handle_fieldFia(request, user_id, obj, json_data, config_data):
    current_field_id = json_data["uObj"]["current_field"]
    
    fia_type = request["fia"]
    if fia_type in available_field_actions:
        handler = available_field_actions[fia_type]
        handler(request, user_id, obj, json_data, config_data, current_field_id)
    else:
        print(f"field.fia case {fia_type} not handled")