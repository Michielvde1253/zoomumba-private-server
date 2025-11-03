from utils import attractionUtils

def handle_pushGet(request, user_id, obj, json_data, config_data):
    # Add entrance fee for current field
    current_field_id = json_data["uObj"]["current_field"]

    time_since_last_push = obj["sData"]["time"] - json_data["pfObj"][current_field_id]["lastPush"]
    
    entrance_fee_per_second = attractionUtils.calculate_entrance_fee_per_hour(json_data, config_data, current_field_id) / 3600

    entrance_fee_gained = entrance_fee_per_second * time_since_last_push
    json_data["uObj"]["entranceFee"] += round(entrance_fee_gained)

    entrance_fee_limit = attractionUtils.calculate_entrance_fee_limit(json_data)

    if json_data["uObj"]["entranceFee"] > entrance_fee_limit:
        json_data["uObj"]["entranceFee"] = entrance_fee_limit

    # Spawn trash
    json_data["pfObj"][current_field_id]["trashroads"] += round(time_since_last_push * 0.05)
    # Approximately, based on Tomonok's saved network session
    # I'm not sure if this is supposed to be a constant, or dependant on certain factors

    # Save last push time
    json_data["pfObj"][current_field_id]["lastPush"] = obj["sData"]["time"]

    # Send to game
    obj["alObj"] = json_data["alObj"]
    obj["animals"] = json_data["animals"]
    obj["cinema"] = json_data["cinema"]
    obj["collItems"] = json_data["collItems"]
    obj["events"] = json_data["events"]
    obj["fObj"] = {}
    obj["fObj"]["cages"] = json_data["fObj"]["cages"][current_field_id]
    obj["gObj"] = json_data["gObj"]
    obj["lObj"] = json_data["lObj"]
    obj["mObj"] = json_data["mObj"]
    #obj["paymentPacks"] = json_data["paymentPacks"]
    obj["pfObj"] = json_data["pfObj"]
    obj["push"] = "" # Not sure what this is
    obj["pwrUp"] = json_data["pwrUp"]
    obj["qObj"] = json_data["qObj"]
    obj["sData"] = json_data["sData"]
    obj["uFrI"] = json_data["uFrI"]
    obj["uFs"] = json_data["uFs"]
    obj["uObj"] = json_data["uObj"]