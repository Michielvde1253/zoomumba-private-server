from utils import expansionUtils, shopUtils
from utils.zooErrors import ZooError, INVALID_REQUEST, NOT_IMPLEMENTED, EVENT_NOT_RUNNING

# field.fia "bP": {"pId": <premiumId>} (BUY_PREMIUM) or {"pId", "cnt"} (BUY_PREMIUM_WITH_COUT)
# Only zoo expansions are implemented so far.

def handle_buyPremium(request, user_id, obj, json_data, config_data, current_field_id):
    premium_id = int(request["pId"])
    item = config_data["gameItems"]["premium"].get(str(premium_id))
    if item is None:
        raise ZooError(INVALID_REQUEST, f"unknown premium item {premium_id}")

    if premium_id in expansionUtils.EXPANSION_FIELD_TYPES and expansionUtils.get_steps(item):
        buy_expansion(premium_id, item, obj, json_data)
    elif premium_id in (23, 128):
        # Anniversary cakes, only sold during the anniversary events
        raise ZooError(EVENT_NOT_RUNNING)
    else:
        raise ZooError(NOT_IMPLEMENTED, f"bP {premium_id} ({item.get('alias')})")


def buy_expansion(premium_id, item, obj, json_data):
    field_type = str(expansionUtils.EXPANSION_FIELD_TYPES[premium_id])
    field_id = json_data.get("fIds", {}).get(field_type)
    if field_id is None or str(field_id) not in json_data["pfObj"]:
        raise ZooError(INVALID_REQUEST, f"player has no playfield of type {field_type}")

    field = json_data["pfObj"][str(field_id)]
    step = expansionUtils.get_next_buyable_step(item, json_data["uObj"]["uLvl"], field["fSize"])
    if step is None:
        raise ZooError(INVALID_REQUEST, "no expansion left to buy", resync=("uObj", "pfObj"))

    # The client always shows (and deducts) the real currency price
    if step.get("cR", 0) > 0:
        shopUtils.reduce_real_currency(step["cR"], json_data)
    elif step.get("cV", 0) > 0:
        shopUtils.reduce_virtual_currency(step["cV"], json_data)

    expansionUtils.set_field_size(json_data, field_id, step["fsize"])

    # A bigger fSize in pfObj makes the client re-render the field (EXPAND_PLAYFIELD)
    obj["pfObj"] = json_data["pfObj"]
    obj["uObj"] = json_data["uObj"]
