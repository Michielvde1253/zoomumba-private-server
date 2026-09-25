from utils import fieldItemUtils as items, shopUtils

# field.fia bSB: {"sbId": 1 (breeding lab) | 2 (nursery), "x", "y", "r", "cR"}
# Stored like the ones in the HAR capture under fObj.specials.<fieldId>.<id>.

def handle_buySpecial(request, user_id, obj, json_data, config_data, current_field_id):
    special_id = int(request["sbId"])
    config = items.item_config(config_data, "specials", {"sbId": special_id})
    shopUtils.buy_from_shop(config, json_data["uObj"]["uLvl"], json_data)

    special = {
        "id": json_data["next_object_id"], "uId": user_id, "fId": current_field_id,
        "sbId": special_id, "act": 0, "level": 0,
        "x": request["x"], "y": request["y"], "r": request.get("r", 0),
        "build": items.now() + int(config.get("buildTime", 0)), "end": 0,
    }
    for slot in range(1, 6):
        special[f"usedItemType{slot}"] = 0
        special[f"usedItemId{slot}"] = 0
    special["act"] = items.building_active(json_data, config, special["x"], special["y"])
    json_data["next_object_id"] += 1

    items.get_items(json_data, "specials", current_field_id)[str(special["id"])] = special
    items.send_item(obj, "specials", current_field_id, special)
    obj["uObj"] = json_data["uObj"]
