"""
Extra zoos (playfields). fIds.<fieldType> = fieldId, pfObj.<fieldId> = settings,
items in fObj.<type>.<fieldId>, animals in animals.<fieldId>.

How a zoo unlocks (MapConfig.as, hardcoded in the client; the client only
checks that the player has the real currency):

  type  zoo          free when                         or for (real currency)
  2     forgotten    main zoo expanded 3 times (13)    150
  3     new/third    forgotten zoo expanded 8 times    150
  4     river        level 90                          500
  5     coast        level 15                          75
  6     oceanworld   level 17                          - (free only)

Free unlocks are the server's job: the client never asks for them, it just
shows the zoo on the map once fIds has an entry for it (field.ul answers the
paid ones). A new zoo starts one step below the first step of its expansion
item and has one road in front of the gate at (31, 88) - where the road
connection check starts, and where every zoo in the HAR capture has a road.
"""
import time

from utils import expansionUtils

MAIN, FORGOTTEN, THIRD, RIVER, COAST, OCEAN = 1, 2, 3, 4, 5, 6
EXPANSION_ITEM = {MAIN: 11, FORGOTTEN: 13, THIRD: 35, RIVER: 125, COAST: 130, OCEAN: 132}
START_SIZE_MAIN = 10

# type -> (level needed, (zoo type, expansions of it) needed, price in real currency or None)
UNLOCKS = {
    FORGOTTEN: (None, (MAIN, 3), 150),
    THIRD: (None, (FORGOTTEN, 8), 150),
    RIVER: (90, None, 500),
    COAST: (15, None, 75),
    OCEAN: (17, None, None),
}
GATE_X, GATE_Y = 31, 89
GATE_ROAD = (31, 88)
LAND_ROAD, OCEAN_ROAD = 6, 26   # "planks" (26) is the only ocean road
ENTRANCE_BUILDING = {OCEAN: 8}  # HAR: the ocean zoo has entrance 8, other extra zoos 0
ITEM_KEYS = ("cages", "stores", "decos", "roads", "trashbins", "specials")


def field_id_of(json_data, field_type):
    field_id = json_data.get("fIds", {}).get(str(field_type))
    return str(field_id) if field_id is not None and str(field_id) in json_data.get("pfObj", {}) else None


def start_size(config_data, field_type):
    if field_type == MAIN:
        return START_SIZE_MAIN
    item = config_data["gameItems"]["premium"][str(EXPANSION_ITEM[field_type])]
    return min(step["fsize"] for step in expansionUtils.get_steps(item)) - 1


def expansions_of(json_data, config_data, field_type):
    field_id = field_id_of(json_data, field_type)
    if field_id is None:
        return -1
    return int(json_data["pfObj"][field_id]["fSize"]) - start_size(config_data, field_type)


def free_unlock_reached(json_data, config_data, field_type):
    level, expansion, _ = UNLOCKS[field_type]
    if level is not None:
        return json_data["uObj"]["uLvl"] >= level
    other, needed = expansion
    return expansions_of(json_data, config_data, other) >= needed


def create_field(json_data, config_data, field_type, user_id):
    """Add an empty zoo of this type. Returns its field id."""
    field_id = f"0{field_type}{user_id}"
    size = start_size(config_data, field_type)
    json_data.setdefault("fIds", {})[str(field_type)] = field_id
    field = {"uId": user_id, "fId": field_id, "fType": field_type, "fSize": size,
             "attMax": 0, "att": 0, "attStatic": 0, "trashbins": 0, "trashroads": 0,
             "lastPush": int(time.time()), "eBuildingId": ENTRANCE_BUILDING.get(field_type, 0),
             "zooGatePosX": GATE_X, "zooGatePosY": GATE_Y}
    field.update(expansionUtils.bounds_for_size(size))
    json_data.setdefault("pfObj", {})[field_id] = field

    from utils import fieldItemUtils as items  # avoids an import cycle
    for key in ITEM_KEYS:
        items.get_items(json_data, key, field_id)
    json_data.setdefault("animals", {})[field_id] = {}

    road = {"id": json_data["next_object_id"], "uId": user_id, "fId": field_id,
            "rId": OCEAN_ROAD if field_type == OCEAN else LAND_ROAD, "act": 1,
            "x": GATE_ROAD[0], "y": GATE_ROAD[1], "r": 0, "deco": 0, "trashbin": 0}
    json_data["next_object_id"] += 1
    items.get_items(json_data, "roads", field_id)[str(road["id"])] = road
    return field_id


def grant_free_fields(json_data, config_data, user_id):
    """Create every zoo whose free unlock condition is met. Returns the new field ids."""
    created = []
    changed = True
    while changed:  # the forgotten zoo can unlock the third one
        changed = False
        for field_type in UNLOCKS:
            if field_id_of(json_data, field_type) is None and free_unlock_reached(json_data, config_data, field_type):
                created.append(create_field(json_data, config_data, field_type, user_id))
                changed = True
    return created
