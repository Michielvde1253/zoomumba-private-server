from utils import cageCareUtils, rewardUtils, fieldItemUtils as items
from utils.zooErrors import ZooError, INVALID_REQUEST, NOT_ENOUGH_MONEY

# field.fia uc: {"id": <cage uniqueId>} - upgrade a cage one level (max 5).
# Cost is main.ucObj[level + 1]: coins "pp" + paws "pPaw", or in the ocean zoo
# "oceanworld_pp" coins + "oceanworld_pearls" pearls (OpenCageUgradeWindowCommand).
# The cage has to be healthy (CageActionMenu). The client changes nothing
# itself, so the cage and uObj come back.
#
# field.fia uCa: {"id", "eId"} - event upgrade: pays cageUpEv[eId].amount of
# collection item cageUpEv[eId].collItemId (the client took one already) and
# marks the cage with that event.

MAX_CAGE_LEVEL = 5


def _pay(json_data, field, amount):
    if amount <= 0:
        return
    if json_data["uObj"].get(field, 0) < amount:
        raise ZooError(NOT_ENOUGH_MONEY)
    json_data["uObj"][field] -= amount


def handle_upgradeCage(request, user_id, obj, json_data, config_data, current_field_id):
    cage = items.get_item(json_data, "cages", current_field_id, request["id"])
    level = int(cage.get("level", 1))
    if level >= MAX_CAGE_LEVEL:
        raise ZooError(INVALID_REQUEST, "cage is already at the highest level")
    if cageCareUtils.is_sick(cage):
        raise ZooError(INVALID_REQUEST, "only healthy cages can be upgraded")
    costs = config_data["main"]["ucObj"][str(level + 1)]
    if cageCareUtils.is_ocean(json_data, current_field_id):
        _pay(json_data, "uCv", int(costs.get("oceanworld_pp", 0)))
        _pay(json_data, "pearls", int(costs.get("oceanworld_pearls", 0)))
    else:
        _pay(json_data, "uCv", int(costs.get("pp", 0)))
        _pay(json_data, "pPaw", int(costs.get("pPaw", 0)))
    cage["level"] = level + 1

    items.send_item(obj, "cages", current_field_id, cage)
    obj["uObj"] = json_data["uObj"]


def handle_upgradeEventCage(request, user_id, obj, json_data, config_data, current_field_id):
    cage = items.get_item(json_data, "cages", current_field_id, request["id"])
    upgrade = config_data.get("cageUpEv", {}).get(str(request.get("eId")))
    if upgrade is None:
        raise ZooError(INVALID_REQUEST, f"no event cage upgrade {request.get('eId')}")
    owned = json_data.setdefault("collItems", {}).get(str(upgrade["collItemId"]))
    if owned is None or owned["cnt"] < int(upgrade.get("amount", 1)):
        raise ZooError(INVALID_REQUEST, "not enough event items", resync=("collItems",))
    owned["cnt"] -= int(upgrade.get("amount", 1))
    cage["eventId"] = int(request["eId"])

    items.send_item(obj, "cages", current_field_id, cage)
    obj["collItems"] = json_data["collItems"]
