import time
from utils.zooErrors import ZooError, INVALID_REQUEST, NOT_ENOUGH_RESOURCES

MEDICINE_RESOURCE_ID = "7"

# field.fia hAC: {"id": <cage uniqueId>} - one medicine per animal in the cage.

def handle_healAnimalCage(request, user_id, obj, json_data, config_data, current_field_id):
    current_time = int(time.time())

    cage = json_data["fObj"]["cages"].get(str(current_field_id), {}).get(str(request["id"]))
    if cage is None:
        raise ZooError(INVALID_REQUEST, f"no cage {request['id']} on field {current_field_id}")

    count_total = cage["male"] + cage["female"] + cage["child"]
    medicine = json_data["res"].get(MEDICINE_RESOURCE_ID)
    if medicine is None or medicine["cnt"] < count_total:
        raise ZooError(NOT_ENOUGH_RESOURCES, resync=("res",))
    medicine["cnt"] -= count_total

    cage["sick"] = current_time

    if "fObj" not in obj:
        obj["fObj"] = {}
    if "cages" not in obj["fObj"]:
        obj["fObj"]["cages"] = {}
    if current_field_id not in obj["fObj"]["cages"]:
        obj["fObj"]["cages"][current_field_id] = {}
    obj["fObj"]["cages"][current_field_id][str(request["id"])] = cage
    obj["res"] = json_data["res"]
