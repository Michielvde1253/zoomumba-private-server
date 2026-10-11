import time
from commands.push_get import handle_pushGet
from utils import fieldItemUtils, expansionUtils, managementCenterUtils

def handle_getUser(request, user_id, obj, json_data, config_data):
    json_data["uObj"]["current_field"] = json_data["fIds"]["1"]
    json_data["actFId"] = json_data["fIds"]["1"]

    # Older saves have babies counted on cages without animal records
    fieldItemUtils.sync_all_cage_animals(json_data, config_data)
    # Older inventory handling kept animals hidden under their stored cage.
    # Surface them as normal inventory animals and empty the stored cage.
    fieldItemUtils.migrate_stored_cage_animals(json_data)

    # Grid bounds that don't match the zoo size, and missed level expansions
    expansionUtils.repair_fields(json_data, config_data)

    # Backfill level unlocks for both new accounts and old saves that missed
    # their original unlock event.
    managementCenterUtils.apply_level_unlocks(json_data)
    managementCenterUtils.sync_storage_capacity(json_data)
    managementCenterUtils.sync_water_tower_capacity(json_data)
    managementCenterUtils.sync_recycling_capacity(json_data)

    # Run push.get
    handle_pushGet(request, user_id, obj, json_data, config_data)

    obj.update(json_data)
    # The saved sData has an old time; the client syncs its clock from sData.time
    obj["sData"] = dict(json_data.get("sData") or {}, time=int(time.time()))
