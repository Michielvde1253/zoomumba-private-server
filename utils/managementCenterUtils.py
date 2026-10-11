"""Level based unlocks for the management center."""


# These buildings are unlocked by player level in the shipped game data.
# Keep this allowlist explicit: other entries (for example seasonal events)
# may also have userLevelRequired=0 but are not normal level rewards.
LEVEL_UNLOCK_BUILDINGS = {
    "storage",          # warehouse, level 0
    "watertower",       # level 0
    "breedingstation",  # level 5
    "kindergarden",     # level 5
    "tombola",          # Wheel of Fortune, level 5
    "recycling",        # level 7
    "crafting",         # workshop, level 7
    "safari",           # level 7
}


def apply_level_unlocks(json_data):
    """Mark reached level-gated management-center buildings as unlocked.

    Returns True if player state changed. The function is safe to call on both
    new accounts and old saves, so missed unlocks are repaired on login too.
    """
    level = int(json_data.get("uObj", {}).get("uLvl", 0))
    player_data = json_data.get("managementCenterData")
    config = json_data.get("managementCenterConfig")
    if not isinstance(player_data, dict) or not isinstance(config, dict):
        return False

    changed = False
    for key in LEVEL_UNLOCK_BUILDINGS:
        building = player_data.get(key)
        building_config = config.get(key)
        if not isinstance(building, dict) or not isinstance(building_config, dict):
            continue
        try:
            required_level = int(building_config.get("userLevelRequired", 0))
        except (TypeError, ValueError):
            continue
        if level >= required_level and int(building.get("builded", 0) or 0) != 1:
            building["builded"] = 1
            changed = True
    return changed


def sync_water_tower_capacity(json_data):
    """Repair the saved water cap to match the tower's saved upgrade level."""
    tower = json_data.get("managementCenterData", {}).get("watertower")
    levels = json_data.get("managementCenterConfig", {}).get("watertower", {}).get("levels", [])
    water = json_data.get("res", {}).get("1")
    if not isinstance(tower, dict) or not isinstance(water, dict):
        return False
    try:
        tower_level = int(tower.get("level", 0))
        level_config = next(
            (item for item in levels if int(item.get("level", -1)) == tower_level),
            None,
        )
        if level_config is None or "maxCap" not in level_config:
            return False
        capacity = int(level_config["maxCap"])
    except (TypeError, ValueError):
        return False
    if int(water.get("mCnt", 0)) == capacity:
        return False
    water["mCnt"] = capacity
    return True


def sync_storage_capacity(json_data):
    """Repair warehouse resource caps to match its saved upgrade level."""
    storage = json_data.get("managementCenterData", {}).get("storage")
    levels = json_data.get("managementCenterConfig", {}).get("storage", {}).get("levels", [])
    resources = json_data.get("res", {})
    if not isinstance(storage, dict) or not isinstance(resources, dict):
        return False
    try:
        level = int(storage.get("level", 0))
        level_config = next(
            (item for item in levels if int(item.get("level", -1)) == level),
            None,
        )
        if level_config is None or "maxCap" not in level_config:
            return False
        capacity = int(level_config["maxCap"])
    except (TypeError, ValueError):
        return False

    changed = False
    for resource_id in ("2", "3", "4", "5", "6", "7"):
        resource = resources.get(resource_id)
        if not isinstance(resource, dict):
            continue
        if int(resource.get("mCnt", 0)) != capacity:
            resource["mCnt"] = capacity
            changed = True
        # A reset to a lower level must not leave an impossible over-cap count.
        try:
            count = int(resource.get("cnt", 0))
            if count > capacity:
                resource["cnt"] = capacity
                changed = True
        except (TypeError, ValueError):
            pass
    return changed


def sync_recycling_capacity(json_data):
    """Repair the trash resource cap to match the recycling building level."""
    recycling = json_data.get("managementCenterData", {}).get("recycling")
    levels = json_data.get("managementCenterConfig", {}).get("recycling", {}).get("levels", [])
    trash = json_data.get("res", {}).get("13")
    if not isinstance(recycling, dict) or not isinstance(trash, dict):
        return False
    try:
        level = int(recycling.get("level", 0))
        level_config = next(
            (item for item in levels if int(item.get("level", -1)) == level),
            None,
        )
        if level_config is None or "maxCap" not in level_config:
            return False
        capacity = int(level_config["maxCap"])
    except (TypeError, ValueError):
        return False
    if int(trash.get("mCnt", 0)) == capacity:
        changed = False
    else:
        trash["mCnt"] = capacity
        changed = True
    try:
        count = int(trash.get("cnt", 0))
        if count > capacity:
            trash["cnt"] = capacity
            changed = True
    except (TypeError, ValueError):
        pass
    return changed
