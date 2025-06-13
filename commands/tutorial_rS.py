import time

# Copied from field.fia
empty_cage = {"id":-1,"uId":0,"fId":0,"cId":1,"sId":0,"act":0,"level":1,"x":34,"y":84,"r":0,"male":0,"female":0,"child":0,"build":1605824682,"breed":0,"clean":0,"feed":0,"water":0,"cuddle":0,"sick":0,"health":0,"sfeed":0,"eventId":0,"evEnd":0,"drops":{"cu":{"col":0,"eItem":0,"eCol":0},"cl":{"col":{"id":244,"amount":1},"eItem":0,"eCol":0},"wa":{"col":0,"eItem":0,"eCol":0},"fe":{"col":0,"pp":2,"pl":0,"eItem":0,"eCol":0},"sf":{"col":0,"pp":2,"pl":0,"eItem":0},"pf":{"col":0,"pp":2,"pl":0,"eItem":0},"hl":{"pp":2,"pl":0},"sh":{"pp":3,"pl":0},"eb":{"pp":2,"pl":0},"db":{"pp":2,"pl":0}}}
empty_animal = {"id":-1,"uId":0,"aId":0,"sId":0,"cId":0,"fId":0,"fTime":0}

# XP reward per step (first one doesn't count so index starts at 1)
# 13th = final reward
# https://github.com/Michielvde1253/zoomumba-client/blob/20248990cf91a0f12581a26079e8366331438748/com/bigpoint/zoorama/core/feature/tutorials/managers/TutorialInjectionManager.as#L43
xpReward = [0,0,20,50,50,100,50,50,50,50,50,50,50,100]

numTasks = [-1,2,2,2,1,2,1,1,2,1,1,1,0,-1]

def handle_tutorialRs(request, user_id, obj, json_data, config_data):
    # Based on com.bigpoint.zoorama.core.feature.tutorials.managers.TutorialServerClone in the client.

    json_data["uObj"]["tutS"] = request["s"]
    json_data["uObj"]["tutT"] = request["t"]

    if numTasks[request["s"]] == request["t"]:
        # Only give reward when entire step is finished
        json_data["uObj"]["uEp"] += xpReward[request["s"]]

    current_field_id = json_data["uObj"]["current_field"]
    current_time = int(time.time())

    # The -10 on timers is because of a small inconsistency between server time and client time, causing glitches
    # There's probably a better way of doing this.

    if request["s"] == 0:
        # Init ice cage
        config_data_for_species = config_data["gameItems"]["animalsSpecies"]["7"]

        new_cage = empty_cage.copy()
        new_cage["id"] = 100
        new_cage["uId"] = user_id
        new_cage["fId"] = current_field_id
        new_cage["cId"] = 3
        new_cage["sId"] = 7
        new_cage["male"] = 2
        new_cage["female"] = 1
        new_cage["x"] = 29
        new_cage["y"] = 86
        new_cage["r"] = 0
        new_cage["act"] = 1
        new_cage["build"] = current_time - 10
        new_cage["clean"] = current_time - 10
        new_cage["feed"] = current_time - 10
        new_cage["water"] = current_time - 10
        new_cage["cuddle"] = current_time - 10
        new_cage["sick"] = current_time - 10
        new_cage["health"] = current_time + config_data_for_species["healthTime"] - 10

        json_data["fObj"]["cages"][current_field_id]["100"] = new_cage

        json_data["fObj"]["stores"][current_field_id]["101"]["collect"] = current_time + 3600 # Why 3600? No idea, because the game does this as well.

    if request["s"] == 4:
        config_data_for_species = config_data["gameItems"]["animalsSpecies"]["7"]

        json_data["fObj"]["cages"][current_field_id]["100"]["clean"] = current_time + config_data_for_species["cleanTime"] - 10
        json_data["fObj"]["cages"][current_field_id]["100"]["feed"] = current_time + config_data_for_species["feedTime"] - 10
        json_data["fObj"]["cages"][current_field_id]["100"]["water"] = current_time + config_data_for_species["waterTime"] - 10
        json_data["fObj"]["cages"][current_field_id]["100"]["cuddle"] = current_time + config_data_for_species["cuddleTime"] - 10
        json_data["fObj"]["cages"][current_field_id]["100"]["health"] = current_time + config_data_for_species["healthTime"] - 10

    if request["s"] == 5 and request["t"] == 2:
        # Init meadow cage
        config_data_for_species = config_data["gameItems"]["animalsSpecies"]["1"]

        new_cage = empty_cage.copy()
        new_cage["id"] = 107 # -5 used in the game client, but i suppose that's a placeholder
        new_cage["uId"] = user_id
        new_cage["fId"] = current_field_id
        new_cage["cId"] = 1
        new_cage["sId"] = 1
        new_cage["male"] = 1
        new_cage["female"] = 1
        new_cage["x"] = 29
        new_cage["y"] = 84
        new_cage["r"] = 0
        new_cage["act"] = 0
        new_cage["build"] = current_time - 10
        new_cage["clean"] = current_time + config_data_for_species["cleanTime"] - 10
        new_cage["feed"] = current_time - 10
        new_cage["water"] = current_time + config_data_for_species["waterTime"] - 10
        new_cage["cuddle"] = current_time + config_data_for_species["cuddleTime"] - 10
        new_cage["sick"] = current_time - 10
        new_cage["health"] = current_time + config_data_for_species["healthTime"] - 10

        json_data["fObj"]["cages"][current_field_id]["107"] = new_cage

    if request["s"] == 9:
        # Set entrance fee to 500
        json_data["uObj"]["entranceFee"] = 500

    if request["s"] == 12:
        # Tutorial finished, give rewards
        json_data["uObj"]["uCv"] += 440
        json_data["uObj"]["uEp"] += xpReward[13]
        json_data["uObj"]["uTut"] = 0

    obj["fObj"] = json_data["fObj"]
    obj["uObj"] = json_data["uObj"]