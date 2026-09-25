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


def bounds_for_size(field_size):
    """Grid bounds of a zoo of field_size tiles. Every playfield in the HAR
    capture fits this (fSize 6 -> 108/-48, 9 -> 102/-42, 10 -> 100/-40,
    13 -> 94/-34), and so do the client's GameBackGround constants
    (MIN_HORIZONTAL_SMALLEST_ZOO = 100 at size 10, _BIGGEST_ZOO = 84 at 18).
    The client draws the zoo from these bounds, not from fSize."""
    return {"minHorizontal": 120 - 2 * field_size, "maxHorizontal": 120,
            "minVertical": -60, "maxVertical": -60 + 2 * field_size}


def fix_bounds(field):
    """Make a playfield's grid bounds match its fSize. Returns True if they changed."""
    wanted = bounds_for_size(int(field["fSize"]))
    changed = any(field.get(k) != v for k, v in wanted.items())
    field.update(wanted)
    return changed


def set_field_size(json_data, field_id, new_size):
    """Grow a playfield to new_size tiles and set its grid bounds to match."""
    field = json_data["pfObj"][str(field_id)]
    new_size = min(new_size, MAX_FIELD_SIZE)
    if new_size <= int(field["fSize"]):
        return False
    field["fSize"] = new_size
    fix_bounds(field)
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


def repair_fields(json_data, config_data):
    """On login: fix grid bounds that don't match fSize (new_player.json had
    a size-11 grid on a size-10 zoo) and hand out level expansions an older
    save missed. Returns True if anything changed."""
    changed = False
    for field in json_data.get("pfObj", {}).values():
        if isinstance(field, dict) and "fSize" in field:
            changed |= fix_bounds(field)
    changed |= apply_level_expansions(json_data, config_data, json_data["uObj"]["uLvl"])
    return changed
