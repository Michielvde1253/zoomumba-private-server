"""Helpers for trashbins (field.fia bTb / mTb)."""
def link_road(json_data, field_id, x, y, trashbin_id):
    """The original server stored the id of the trashbin standing on a road in road["trashbin"]
    (the client ignores it, but keep the data consistent)."""
    for road in json_data["fObj"].get("roads", {}).get(field_id, {}).values():
        if road.get("x") == x and road.get("y") == y:
            road["trashbin"] = trashbin_id
        elif road.get("trashbin") == trashbin_id:
            road["trashbin"] = 0
