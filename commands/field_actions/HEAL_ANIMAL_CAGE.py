from utils import cageCareUtils, fieldItemUtils as items
from utils.zooErrors import ZooError, INVALID_REQUEST, NOT_ENOUGH_RESOURCES

# field.fia hAC / shAC / sfAC / pfAC: {"id": <cage uniqueId>}
#   hAC   heal: one medicine per animal
#   shAC  super heal: one supermedicine, keeps the animals healthy for longer
#   sfAC  super feed: one superfood (super_fishfood in the ocean zoo), double feed xp
#   pfAC  power feed: one powerfood (power_fishfood)
# The client takes the resource and adds the xp itself; we send cage, res and uObj back.

ACTIONS = {"hAC": "heal", "shAC": "superheal", "sfAC": "superfeed", "pfAC": "powerfeed"}


def handle_cageCareAction(request, user_id, obj, json_data, config_data, current_field_id):
    cage = items.get_item(json_data, "cages", current_field_id, request["id"])
    if cageCareUtils.species_config(config_data, cage) is None or cageCareUtils.animal_count(cage) == 0:
        raise ZooError(INVALID_REQUEST, f"cage {request['id']} has no animals")
    if not cageCareUtils.perform(obj, json_data, config_data, cage, ACTIONS[request["fia"]], current_field_id):
        raise ZooError(NOT_ENOUGH_RESOURCES, resync=("res", "uObj"))

    items.send_item(obj, "cages", current_field_id, cage)
    obj["res"] = json_data["res"]
    obj["uObj"] = json_data["uObj"]


handle_healAnimalCage = handle_cageCareAction
