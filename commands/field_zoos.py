from utils import playfieldUtils, expansionUtils, shopUtils, fieldItemUtils as items
from utils.zooErrors import ZooError, INVALID_REQUEST, NOT_ENOUGH_MONEY
from commands.inventory_iva import item_to_inventory, trashbin_to_inventory

# field.ul {"t": <field type>}: unlock a zoo on the world map (MapFullScreenMediator).
#   Free once its condition is met (playfieldUtils.UNLOCKS), otherwise for its
#   real-currency price; the client deducts nothing and only redraws the map
#   from fIds, so fIds, pfObj and uObj come back.
# field.eFbC {"tools", "zd"}: buy the forgotten zoo's next expansion (premium 13)
#   with "tools" (collection item 1, expansion_coins) plus "zd" real currency
#   for the rest of the step's price (ExpansionBuyCommand).
# field.moveItemsToInventory {}: put everything on the current zoo into the
#   inventory (AllInInventoryCommand); the client then reloads the zoo with init.sP.

TOOLS_ITEM = "1"


def handle_fieldUnlock(request, user_id, obj, json_data, config_data):
    field_type = int(request.get("t", 0))
    if field_type not in playfieldUtils.UNLOCKS:
        raise ZooError(INVALID_REQUEST, f"zoo type {field_type} can't be unlocked")
    if playfieldUtils.field_id_of(json_data, field_type) is not None:
        raise ZooError(INVALID_REQUEST, f"zoo type {field_type} is already unlocked", resync=("uObj", "fIds"))
    if not playfieldUtils.free_unlock_reached(json_data, config_data, field_type):
        price = playfieldUtils.UNLOCKS[field_type][2]
        if price is None:
            raise ZooError(INVALID_REQUEST, f"zoo type {field_type} can't be bought", resync=("uObj", "fIds"))
        shopUtils.reduce_real_currency(price, json_data)
    playfieldUtils.create_field(json_data, config_data, field_type, user_id)
    obj["fIds"] = json_data["fIds"]
    obj["pfObj"] = json_data["pfObj"]
    obj["uObj"] = json_data["uObj"]


def handle_extendForgottenWithTools(request, user_id, obj, json_data, config_data):
    field_id = playfieldUtils.field_id_of(json_data, playfieldUtils.FORGOTTEN)
    if field_id is None:
        raise ZooError(INVALID_REQUEST, "no forgotten zoo")
    item = config_data["gameItems"]["premium"][str(playfieldUtils.EXPANSION_ITEM[playfieldUtils.FORGOTTEN])]
    field = json_data["pfObj"][field_id]
    step = expansionUtils.get_next_buyable_step(item, json_data["uObj"]["uLvl"], field["fSize"])
    if step is None:
        raise ZooError(INVALID_REQUEST, "no expansion left to buy", resync=("uObj", "pfObj", "collItems"))

    tools, real = int(request.get("tools", 0)), int(request.get("zd", 0))
    if tools < 0 or real < 0 or tools + real != int(step["cR"]):
        raise ZooError(INVALID_REQUEST, f"{tools} tools + {real} real doesn't match the price {step['cR']}", resync=("uObj", "collItems"))
    owned = json_data.setdefault("collItems", {}).get(TOOLS_ITEM, {"cnt": 0})
    if owned.get("cnt", 0) < tools:
        raise ZooError(NOT_ENOUGH_MONEY, resync=("uObj", "collItems"))
    shopUtils.reduce_real_currency(real, json_data)
    if tools:
        json_data["collItems"][TOOLS_ITEM]["cnt"] -= tools

    expansionUtils.set_field_size(json_data, field_id, step["fsize"])
    obj["pfObj"] = json_data["pfObj"]
    obj["collItems"] = json_data["collItems"]
    obj["uObj"] = json_data["uObj"]


def handle_moveItemsToInventory(request, user_id, obj, json_data, config_data):
    field_id = str(json_data["uObj"]["current_field"])
    for key, category in (("roads", items.ROAD), ("cages", items.CAGE), ("stores", items.STORE),
                          ("decos", items.DECOR), ("specials", items.SPECIALS)):
        for item_id in list(items.get_items(json_data, key, field_id)):
            item_to_inventory({"type": category, "id": int(item_id)}, user_id, obj, json_data, config_data, field_id)
    for item_id in list(items.get_items(json_data, "trashbins", field_id)):
        trashbin_to_inventory({"id": int(item_id)}, user_id, obj, json_data, config_data, field_id)
