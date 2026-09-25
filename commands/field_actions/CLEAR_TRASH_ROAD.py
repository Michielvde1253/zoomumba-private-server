from utils import trashbinUtils

# field.fia "cTr": {"cnt": <trash on that road tile>}
# Like emptying a bin: 1 XP + 1 trash resource per piece (the client adds these locally too).

def handle_clearTrashRoad(request, user_id, obj, json_data, config_data, current_field_id):
    field = json_data["pfObj"][str(current_field_id)]
    amount = max(0, min(int(request.get("cnt", 0)), field.get("trashroads", 0)))
    field["trashroads"] -= amount

    trashbinUtils.give_trash_rewards(json_data, amount)

    obj["uObj"] = json_data["uObj"]
    obj["res"] = json_data["res"]
