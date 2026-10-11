from utils import shopUtils
from utils.zooErrors import ZooError, INVALID_REQUEST


# Resource 1 is water. The warehouse controls the regular feed resources.
BUILDING_RESOURCES = {
    "storage": ("2", "3", "4", "5", "6", "7"),
    "watertower": ("1",),
    "recycling": ("13",),
}


def handle_managementCenterUpgrade(request, user_id, obj, json_data, config_data):
    """Upgrade a management-center building using its configured next level."""
    building = str(request.get("building", ""))
    if building not in BUILDING_RESOURCES:
        raise ZooError(INVALID_REQUEST, f"unsupported management center building: {building}",
                       resync=("managementCenterData", "uObj", "res"))

    player_building = json_data.get("managementCenterData", {}).get(building)
    building_config = json_data.get("managementCenterConfig", {}).get(building)
    levels = building_config.get("levels", []) if building_config else []
    if not isinstance(player_building, dict) or not levels:
        raise ZooError(INVALID_REQUEST, f"missing management center configuration for {building}",
                       resync=("managementCenterData", "uObj", "res"))

    try:
        current_level = int(player_building.get("level", 0))
    except (TypeError, ValueError):
        raise ZooError(INVALID_REQUEST, f"invalid current level for {building}",
                       resync=("managementCenterData", "uObj", "res"))

    next_level = next((entry for entry in levels
                       if int(entry.get("level", -1)) == current_level + 1), None)
    if next_level is None:
        raise ZooError(INVALID_REQUEST, f"{building} is already at its maximum level",
                       resync=("managementCenterData", "uObj", "res"))

    # The Flash client sends instantBuyReal=1 when the player selects the
    # premium-currency price, and 0 for the virtual-currency price.
    try:
        pay_real = int(request.get("instantBuyReal", 0)) == 1
    except (TypeError, ValueError):
        raise ZooError(INVALID_REQUEST, "invalid currency selection",
                       resync=("managementCenterData", "uObj", "res"))

    price_key = "buyReal" if pay_real else "buyVirtual"
    price = int(next_level.get(price_key, 0))
    if price <= 0:
        raise ZooError(INVALID_REQUEST, f"{building} cannot be upgraded with the selected currency",
                       resync=("managementCenterData", "uObj", "res"))

    if pay_real:
        shopUtils.reduce_real_currency(price, json_data)
    else:
        shopUtils.reduce_virtual_currency(price, json_data)

    player_building["level"] = current_level + 1
    max_capacity = next_level.get("maxCap")
    if max_capacity is not None:
        for resource_id in BUILDING_RESOURCES[building]:
            resource = json_data.get("res", {}).get(resource_id)
            if resource is not None:
                resource["mCnt"] = int(max_capacity)

    obj["managementCenterData"] = json_data["managementCenterData"]
    obj["uObj"] = json_data["uObj"]
    obj["res"] = json_data.get("res", {})
