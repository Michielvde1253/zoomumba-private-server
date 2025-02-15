from collections import deque

def get_tiles_around_building(size_x, size_y, coord_x, coord_y):
    # coord_x and coord_y are on the upper corner of the building
    tiles_around_building = []
    for i in range(size_x):
        # Top right edge
        tiles_around_building.append((coord_x + i, coord_y - 1))
        # Bottom left edge
        tiles_around_building.append((coord_x + i, coord_y + size_y))

    for i in range(size_y):
        # Top left edge
        tiles_around_building.append((coord_x - 1, coord_y + i))
        # Bottom right edge
        tiles_around_building.append((coord_x + size_x, coord_y + i))

    # Corners (NOT NEEDED)
    #tiles_around_building.append((coord_x - 1, coord_y - 1))
    #tiles_around_building.append((coord_x + size_x, coord_y + size_y))
    #tiles_around_building.append((coord_x - 1, coord_y + size_y))
    #tiles_around_building.append((coord_x + size_x, coord_y - 1))

    return tiles_around_building

def find_roads(json_data, tiles_around_building):
    current_field_id = json_data["uObj"]["current_field"]
    roads = []
    roads_around_building = []

    for i in json_data["fObj"]["roads"][current_field_id]:
        road = json_data["fObj"]["roads"][current_field_id][i]
        roads.append((road["x"], road["y"]))
        if (road["x"], road["y"]) in tiles_around_building:
            roads_around_building.append((road["x"], road["y"]))

    return roads, roads_around_building


def path_exists(roads, start_tiles, end):
    # Made with ChatGPT

    if not any(tile in roads for tile in start_tiles) or end not in roads:
        return False
    
    visited = set(start_tiles)  # Start from all given tiles
    queue = deque(start_tiles)

    while queue:
        x, y = queue.popleft()
        if (x, y) == end:
            return True

        # Check 4 possible directions (left, right, up, down)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (x + dx, y + dy)
            if neighbor in roads and neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    
    return False

def is_building_active(json_data, coord_x, coord_y, size_x, size_y):
    tiles_around_building = get_tiles_around_building(size_x, size_y, coord_x, coord_y)
    roads, roads_around_building = find_roads(json_data, tiles_around_building)

    if (31,88) not in roads: # Road in front of the entrance doesn't exist at all
        # To-do: support other fields where the entrance gate is in a different location.
        return False
    
    return path_exists(roads, roads_around_building, (31,88))

def check_all_buildings_around_tile(json_data, config_data, coord_x, coord_y):
    ############################################
    # Used when placing/moving/deleting a road #
    ############################################
    # for placing buildings we check just that building (using is_building_active()).


    # To-do: Rewrite this entire function in a proper way
    # Currently this gets all the buildings on the map and runs the pathfinding on all
    # of them separately, which is not exactly very efficient
    current_field_id = json_data["uObj"]["current_field"]

    # Stores
    for j in json_data["fObj"]["stores"][current_field_id]:
        i = json_data["fObj"]["stores"][current_field_id][j]
        config_data_for_store = config_data["gameItems"]["stores"][str(i["stId"])]
        i["act"] = int(is_building_active(json_data, i["x"], i["y"], config_data_for_store["width"], config_data_for_store["height"]))

    # Cages
    for j in json_data["fObj"]["cages"][current_field_id]:
        i = json_data["fObj"]["cages"][current_field_id][j]
        config_data_for_cage = config_data["gameItems"]["cages"][str(i["cId"])]
        i["act"] = int(is_building_active(json_data, i["x"], i["y"], config_data_for_cage["width"], config_data_for_cage["height"]))

    # Decos
    for j in json_data["fObj"]["decos"][current_field_id]:
        i = json_data["fObj"]["decos"][current_field_id][j]
        config_data_for_deco = config_data["gameItems"]["decos"][str(i["dId"])]
        i["act"] = int(is_building_active(json_data, i["x"], i["y"], config_data_for_deco["width"], config_data_for_deco["height"]))

    # Trashbins
    for j in json_data["fObj"]["trashbins"][current_field_id]:
        i = json_data["fObj"]["trashbins"][current_field_id][j]
        config_data_for_trashbin = config_data["gameItems"]["trashbins"][str(i["tbId"])]
        i["act"] = int(is_building_active(json_data, i["x"], i["y"], config_data_for_trashbin["width"], config_data_for_trashbin["height"]))