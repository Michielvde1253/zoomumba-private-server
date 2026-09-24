"""
Playfield (zoo) expansions.

Expansion items live in config gameItems.premium and have params.expands, a
list of steps like {"lvl": 20, "fsize": 12, "cR": 15, "cV": 0}. Each step makes
the zoo one or more tiles bigger. Steps with "lvl" also unlock for free when
the player reaches that level (main zoo only); before that they can be bought
early with real currency. This mirrors ExpansionShopData.returnPrice() in the
client so the server charges exactly what the client showed.
"""

MAX_FIELD_SIZE = 18

# premiumId -> playfield type (PlayFieldsTypes) it expands
EXPANSION_FIELD_TYPES = {
    11: 1, 12: 1,              # main zoo (+ "to maximum")
    13: 2, 14: 2, 29: 2,       # forgotten zoo (14 = paid with tools, via field.eFbC)
    35: 3, 37: 3,              # third zoo
    125: 4, 126: 4,            # river zoo
    130: 5, 131: 5,            # coast zoo
    132: 6, 133: 6,            # ocean world
}


def get_steps(premium_item):
    expands = (premium_item.get("params") or {}).get("expands") or {}
    return list(expands.values()) if isinstance(expands, dict) else list(expands)


def get_next_buyable_step(premium_item, user_level, field_size):
    """The step the client offers for sale, or None (same rules as the client)."""
    best = None
    for step in get_steps(premium_item):
        if step.get("lvl") and user_level >= step["lvl"]:
            continue  # already unlocked for free by level
        if field_size < step["fsize"] and (best is None or step["fsize"] < best["fsize"]):
            best = step
    return best


def set_field_size(json_data, field_id, new_size):
    """Grow a playfield to new_size tiles, widening its grid bounds to match."""
    field = json_data["pfObj"][str(field_id)]
    delta = min(new_size, MAX_FIELD_SIZE) - field["fSize"]
    if delta <= 0:
        return False
    # Real server data: the grid grows towards lower minHorizontal and higher
    # maxVertical, 2 units per tile (e.g. fSize 6 -> 108/-48, fSize 13 -> 94/-34)
    field["fSize"] += delta
    field["minHorizontal"] -= 2 * delta
    field["maxVertical"] += 2 * delta
    return True


def apply_level_expansions(json_data, config_data, user_level):
    """Give the main zoo every free level-based expansion up to user_level."""
    item = config_data["gameItems"]["premium"].get("11")
    field_id = json_data.get("fIds", {}).get("1")
    if not item or field_id is None or str(field_id) not in json_data["pfObj"]:
        return False
    reached = [s["fsize"] for s in get_steps(item) if s.get("lvl") and user_level >= s["lvl"]]
    if not reached:
        return False
    return set_field_size(json_data, field_id, max(reached))
