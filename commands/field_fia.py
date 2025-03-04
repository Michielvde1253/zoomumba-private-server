import time
from utils import shopUtils
from utils import roadPathfindingUtils

empty_cage = {"id":-1,"uId":0,"fId":0,"cId":1,"sId":0,"act":0,"level":1,"x":34,"y":84,"r":0,"male":0,"female":0,"child":0,"build":1605824682,"breed":0,"clean":0,"feed":0,"water":0,"cuddle":0,"sick":0,"health":0,"sfeed":0,"eventId":0,"evEnd":0,"drops":{"cu":{"col":0,"eItem":0,"eCol":0},"cl":{"col":{"id":244,"amount":1},"eItem":0,"eCol":0},"wa":{"col":0,"eItem":0,"eCol":0},"fe":{"col":0,"pp":2,"pl":0,"eItem":0,"eCol":0},"sf":{"col":0,"pp":2,"pl":0,"eItem":0},"pf":{"col":0,"pp":2,"pl":0,"eItem":0},"hl":{"pp":2,"pl":0},"sh":{"pp":3,"pl":0},"eb":{"pp":2,"pl":0},"db":{"pp":2,"pl":0}}}
empty_animal = {"id":-1,"uId":0,"aId":0,"sId":0,"cId":0,"fId":0,"fTime":0,"act":0}
empty_road = {"id": -1,"uId": 0,"fId": 0,"rId": 6,"act": 0,"x": 24,"y": 72,"r": 0,"deco": 0,"trashbin": 6341202}
empty_deco = {"id": -1,"uId": 0,"fId": 0,"dId": 76,"act": 0,"x": 37,"y": 82,"r": 0,"build": 1315636007}

def handle_fieldFia(request, user_id, obj, json_data, config_data):
    current_field_id = json_data["uObj"]["current_field"]

    match request["fia"]:

        #############
        # BUY ITEMS #
        #############

        case "bC": # BUY_CAGE
            # Create field object if needed
            if str(current_field_id) not in json_data["fObj"]["cages"]:
                json_data["fObj"]["cages"][str(current_field_id)] = {}

            # Initialize new cage
            new_cage = empty_cage.copy()
            new_cage["id"] = json_data["next_object_id"]
            new_cage["uId"] = user_id
            new_cage["fId"] = current_field_id
            new_cage["cId"] = request["cId"]
            new_cage["x"] = request["x"]
            new_cage["y"] = request["y"]
            new_cage["r"] = request["r"]
            new_cage["build"] = int(time.time()) + 10

            json_data["next_object_id"] += 1
            json_data["fObj"]["cages"][str(current_field_id)][str(new_cage["id"])] = new_cage

            # Buy item
            config_data_for_cage = config_data["gameItems"]["cages"][str(request["cId"])]
            shopUtils.buy_from_shop(config_data_for_cage, json_data["uObj"]["uLvl"], json_data)

            # Check for nearby roads and set to active if needed
            json_data["fObj"]["cages"][str(current_field_id)][str(new_cage["id"])]["act"] = int(roadPathfindingUtils.is_building_active(json_data, request["x"], request["y"], config_data_for_cage["width"], config_data_for_cage["height"]))

            # Send objects to game
            obj["fObj"] = json_data["fObj"]
            obj["req"] = request["req:"] # typo by bigpoint lol
            obj["uObj"] = json_data["uObj"]


        case "bAC": # BUY_ANIMAL_CAGE
            # Create field object if needed
            if str(current_field_id) not in json_data["animals"]:
                json_data["animals"][str(current_field_id)] = {}
            if str(request["id"]) not in json_data["animals"][str(current_field_id)]:
                json_data["animals"][str(current_field_id)][str(request["id"])] = {}

            # Initialize new animal
            new_animal = empty_animal.copy()
            new_animal["id"] = json_data["next_object_id"]
            new_animal["uId"] = user_id
            new_animal["fId"] = current_field_id
            new_animal["cId"] = request["id"]
            new_animal["aId"] = request["aId"]
            new_animal["sId"] = config_data["gameItems"]["animals"][str(request["aId"])]["speciesId"]

            json_data["next_object_id"] += 1

            json_data["animals"][str(current_field_id)][str(request["id"])][str(new_animal["id"])] = new_animal

            # Get cage
            cage = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]
            cage["sId"] = new_animal["sId"]

            current_time = int(time.time())

            # Get config data for animal + species
            config_data_for_animal = config_data["gameItems"]["animals"][str(request["aId"])]
            config_data_for_species = config_data["gameItems"]["animalsSpecies"][str(new_animal["sId"])]

            # Setup cage
            male = config_data_for_animal["male"]
            child = config_data_for_animal["child"]
            if male == 1:
                cage["male"] += 1
            elif child == 1:
                cage["child"] += 1
            else:
                cage["female"] += 1

            cage["clean"] = current_time + config_data_for_species["cleanTime"]
            cage["feed"] = current_time + config_data_for_species["feedTime"]
            cage["water"] = current_time + config_data_for_species["waterTime"]
            cage["cuddle"] = current_time + config_data_for_species["cuddleTime"]
            cage["sick"] = current_time
            cage["health"] = current_time + config_data_for_species["healthTime"]

            # Buy item
            shopUtils.buy_from_shop(config_data_for_animal, json_data["uObj"]["uLvl"], json_data)

            # Send objects to game
            obj["fObj"] = json_data["fObj"]
            obj["uObj"] = json_data["uObj"]
            obj["animals"] = json_data["animals"]
            obj["req"] = request["req:"] # typo by bigpoint lol

        case "bR": # BUY_ROAD
            # Create field object if needed
            if str(current_field_id) not in json_data["fObj"]["roads"]:
                json_data["fObj"]["roads"][str(current_field_id)] = {}

            # Initialize new road
            new_road = empty_road.copy()
            new_road["id"] = json_data["next_object_id"]
            new_road["uId"] = user_id
            new_road["fId"] = current_field_id
            new_road["rId"] = request["rId"]
            new_road["x"] = request["x"]
            new_road["y"] = request["y"]
            new_road["r"] = request["r"]
            new_road["trashbin"] = int(time.time())

            json_data["next_object_id"] += 1
            json_data["fObj"]["roads"][str(current_field_id)][str(new_road["id"])] = new_road

            # Buy item
            config_data_for_road = config_data["gameItems"]["roads"][str(request["rId"])]
            shopUtils.buy_from_shop(config_data_for_road, json_data["uObj"]["uLvl"], json_data)

            # Check all buildings around the road and change them to active if needed:
            roadPathfindingUtils.check_all_buildings_around_tile(json_data, config_data, request["x"], request["y"])

            # Send objects to game
            obj["fObj"] = json_data["fObj"]
            obj["req"] = request["req:"] # typo by bigpoint lol
            obj["uObj"] = json_data["uObj"]

        case "bD": # BUY_DECO
            # Create field object if needed
            if str(current_field_id) not in json_data["fObj"]["decos"]:
                json_data["fObj"]["decos"][str(current_field_id)] = {}

            # Initialize new road
            new_deco = empty_deco.copy()
            new_deco["id"] = json_data["next_object_id"]
            new_deco["uId"] = user_id
            new_deco["fId"] = current_field_id
            new_deco["dId"] = request["dId"]
            new_deco["x"] = request["x"]
            new_deco["y"] = request["y"]
            new_deco["r"] = request["r"]
            new_deco["build"] = int(time.time()) + 10

            json_data["next_object_id"] += 1
            json_data["fObj"]["decos"][str(current_field_id)][str(new_deco["id"])] = new_deco

            # Buy item
            config_data_for_deco = config_data["gameItems"]["decos"][str(request["dId"])]
            shopUtils.buy_from_shop(config_data_for_road, json_data["uObj"]["uLvl"], json_data)

            # Check for nearby roads and set to active if needed
            json_data["fObj"]["decos"][str(current_field_id)][str(new_deco["id"])]["act"] = int(roadPathfindingUtils.is_building_active(json_data, request["x"], request["y"], config_data_for_deco["width"], config_data_for_deco["height"]))

            # Send objects to game
            obj["fObj"] = json_data["fObj"]
            obj["req"] = request["req:"] # typo by bigpoint lol
            obj["uObj"] = json_data["uObj"]

        case "bIr": # BUY_RESOURCE

            # Buy item
            config_data_for_resource = config_data["gameItems"]["resources"][str(request["irId"])]
            shopUtils.buy_multiple_from_shop(config_data_for_resource, json_data["uObj"]["uLvl"], json_data, request["cnt"])
            json_data["res"][str(request["irId"])]["cnt"] += request["cnt"]

            # Send objects to game
            obj["req"] = request["req:"] # typo by bigpoint lol
            obj["uObj"] = json_data["uObj"]
            obj["res"] = json_data["res"]

        #################
        # ANIMALS STUFF #
        #################

        case ("fAC" | "wAC"): # FEED_ANIMAL_CAGE or WATER_ANIMAL_CAGE
            current_time = int(time.time())

            cage = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]

            species_id = cage["sId"]
            config_data_for_species = config_data["gameItems"]["animalsSpecies"][str(species_id)]

            # To-do: is there a better way to count the animals?
            count_males = cage["male"]
            count_females = cage["female"]
            count_childs = cage["child"]
            count_total = count_males + count_females + count_childs

            if request["fia"] == "fAC":
                food_id = config_data_for_species["foodId"]
                food_per_animal = config_data_for_species["foodPerAnimal"]
            elif request["fia"] == "wAC":
                food_id = 1
                food_per_animal = config_data_for_species["waterPerAnimal"]

            total_food_cost = food_per_animal * count_total

            if json_data["res"][str(food_id)]["cnt"] >= total_food_cost:

                if request["fia"] == "fAC":
                    if json_data["uObj"]["uTut"] == 0: # During tutorial no exp is given
                        json_data["uObj"]["uEp"] += shopUtils.get_cage_calculated_xp(cage, "feed", config_data, json_data["uObj"]["uLvl"], count_total)

                    cage["feed"] = current_time + config_data_for_species["feedTime"]

                elif request["fia"] == "wAC":
                    if json_data["uObj"]["uTut"] == 0: # During tutorial no exp is given
                        json_data["uObj"]["uEp"] += shopUtils.get_cage_calculated_xp(cage, "water", config_data, json_data["uObj"]["uLvl"], count_total)

                    cage["water"] = current_time + config_data_for_species["waterTime"]

                json_data["res"][str(food_id)]["cnt"] -= total_food_cost

            obj["uObj"] = json_data["uObj"]
            obj["fObj"] = json_data["fObj"]
            obj["res"] = json_data["res"]

        case ("cAC" | "cuAC"): # CLEAN_ANIMAL_CAGE or CUDDLE_ANIMAL_CAGE
            current_time = int(time.time())

            cage = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]

            species_id = cage["sId"]
            config_data_for_species = config_data["gameItems"]["animalsSpecies"][str(species_id)]

            # To-do: is there a better way to count the animals?
            count_males = cage["male"]
            count_females = cage["female"]
            count_childs = cage["child"]
            count_total = count_males + count_females + count_childs

            if request["fia"] == "cAC":
                if json_data["uObj"]["uTut"] == 0: # During tutorial no exp is given
                    json_data["uObj"]["uEp"] += shopUtils.get_cage_calculated_xp(cage, "clean", config_data, json_data["uObj"]["uLvl"], count_total)

                cage["clean"] = current_time + config_data_for_species["cleanTime"]

            elif request["fia"] == "cuAC":
                if json_data["uObj"]["uTut"] == 0: # During tutorial no exp is given
                    json_data["uObj"]["uEp"] += shopUtils.get_cage_calculated_xp(cage, "cuddle", config_data, json_data["uObj"]["uLvl"], count_total)

                cage["cuddle"] = current_time + config_data_for_species["cuddleTime"]

            obj["uObj"] = json_data["uObj"]
            obj["fObj"] = json_data["fObj"]

        case "cEf": # COLLECT_ENTRANCE_FEE
            json_data["uObj"]["uCv"] += json_data["uObj"]["entranceFee"]
            json_data["uObj"]["entranceFee"] = 0

            # Send objects to game
            obj["req"] = request["req:"] # typo by bigpoint lol
            obj["uObj"] = json_data["uObj"]

        case "cSt": # COLLECT_STORE_MONEY
            # the fTime in player json seems to be unused?

            store = json_data["fObj"]["stores"][str(current_field_id)][str(request["id"])]
            store_id = store["stId"]
            
            config_data_for_store = config_data["gameItems"]["stores"][str(store_id)]

            if(int(time.time()) >= store["collect"]):
                store["collect"] = int(time.time()) + config_data_for_store["collectTime"]
                json_data["uObj"]["uCv"] += config_data_for_store["collectVirtual"]

            # Send objects to game
            obj["req"] = request["req:"] # typo by bigpoint lol
            obj["uObj"] = json_data["uObj"]
            obj["fObj"] = json_data["fObj"]

        case "mC": # MOVE_CAGE

            json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]["x"] = request["x"]
            json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]["y"] = request["y"]

            cage_id = json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]["cId"]
            config_data_for_cage = config_data["gameItems"]["cages"][str(cage_id)]

            # Check for nearby roads and set to active if needed
            json_data["fObj"]["cages"][str(current_field_id)][str(request["id"])]["act"] = int(roadPathfindingUtils.is_building_active(json_data, request["x"], request["y"], config_data_for_cage["width"], config_data_for_cage["height"]))

            # Send objects to game
            obj["req"] = request["req:"] # typo by bigpoint lol
            obj["fObj"] = json_data["fObj"]

        case "mR": # MOVE_ROAD

            json_data["fObj"]["roads"][str(current_field_id)][str(request["id"])]["x"] = request["x"]
            json_data["fObj"]["roads"][str(current_field_id)][str(request["id"])]["y"] = request["y"]

            # Check all buildings around the road and change them to active if needed:
            roadPathfindingUtils.check_all_buildings_around_tile(json_data, config_data, request["x"], request["y"])

            # Send objects to game
            obj["req"] = request["req:"] # typo by bigpoint lol
            obj["fObj"] = json_data["fObj"]

        case _:
            print("field.fia case not handled.")