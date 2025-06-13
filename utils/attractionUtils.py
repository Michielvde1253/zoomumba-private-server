import time
import math

def calculate_static_attraction(json_data, config_data, field_id):
    # Decorations, cages, roads and stores
    total_static_attraction = 0
    for j in json_data["fObj"]["decos"][field_id]:
        i = json_data["fObj"]["decos"][field_id][j]
        dId = i["dId"]
        attraction = config_data["gameItems"]["decos"][str(dId)]["attraction"]
        total_static_attraction += attraction
    for j in json_data["fObj"]["cages"][field_id]:
        i = json_data["fObj"]["cages"][field_id][j]
        cId = i["cId"]
        attraction = config_data["gameItems"]["cages"][str(cId)]["attraction"]
        total_static_attraction += attraction
    for j in json_data["fObj"]["roads"][field_id]:
        i = json_data["fObj"]["roads"][field_id][j]
        rId = i["rId"]
        attraction = config_data["gameItems"]["roads"][str(rId)]["attraction"]
        total_static_attraction += attraction
    for j in json_data["fObj"]["stores"][field_id]:
        i = json_data["fObj"]["stores"][field_id][j]
        stId = i["stId"]
        attraction = config_data["gameItems"]["stores"][str(stId)]["attraction"]
        total_static_attraction += attraction

    return total_static_attraction

def calculate_current_and_max_attraction(json_data, config_data, field_id):
    # Animals
    total_current_attraction = 0
    max_attraction = 0
    for j in json_data["fObj"]["cages"][field_id]:
        i = json_data["fObj"]["cages"][field_id][j]
        sId = i["sId"]
        cId = i["cId"]

        if sId <= 0 or i["act"] == 0: # Only look at non-empty cages that are connected to a road
            continue

        count_males = i["male"]
        count_females = i["female"]
        count_childs = i["child"]

        attraction_animals = count_males * config_data["gameItems"]["animalsSpecies"][str(sId)]["attraction"][0]
        attraction_animals += count_females * config_data["gameItems"]["animalsSpecies"][str(sId)]["attraction"][1]
        attraction_animals += count_childs * config_data["gameItems"]["animalsSpecies"][str(sId)]["attraction"][2]

        current_time = int(time.time())
        attraction_health = 0.1
        if i["clean"] > current_time:
            attraction_health += 0.3
        if i["feed"] > current_time:
            attraction_health += 0.3
        if i["water"] > current_time:
            attraction_health += 0.3
        if i["cuddle"] > current_time:
            attraction_health += 0.5

        if config_data["gameItems"]["animalsSpecies"][str(sId)]["cages"][str(cId)] == 1: # "Crazy" bonus
            attraction_cagebonus = 1.1
        else:
            attraction_cagebonus = 1
            
        # https://github.com/Michielvde1253/zoomumba-client/blob/20248990cf91a0f12581a26079e8366331438748/com/bigpoint/zoomumba/model/playfield/PlayfieldSettingsProxy.as#L270

        # this might need to be round() instead of math.ceil()
        total_current_attraction += math.ceil(attraction_animals * attraction_health * attraction_cagebonus)
        max_attraction += math.ceil(attraction_animals * 1.5 * attraction_cagebonus)

    return total_current_attraction, max_attraction

def calculate_attraction(json_data, config_data, field_id):
    static_attraction = calculate_static_attraction(json_data, config_data, field_id)
    current_attraction = calculate_current_and_max_attraction(json_data, config_data, field_id)[0]
    max_attraction = calculate_current_and_max_attraction(json_data, config_data, field_id)[0]

    if static_attraction > (0.2 * max_attraction):
        static_attraction = math.floor(max_attraction)
    attraction = static_attraction + current_attraction
    print(f"[DEBUG] The attraction is {attraction}")
    return attraction

def calculate_entrance_fee_per_hour(json_data, config_data, field_id):
    return math.sqrt(calculate_attraction(json_data, config_data, field_id)) * 35

def calculate_entrance_fee_limit(json_data):
    # https://github.com/Michielvde1253/zoomumba-client/blob/20248990cf91a0f12581a26079e8366331438748/com/bigpoint/zoorama/view/actionMenu/GateActionMenu.as#L158
    level = json_data["uObj"]["uLvl"]
    return round((65 * math.pow(level, 2) - 350 * level + 7500) / 500) * 500