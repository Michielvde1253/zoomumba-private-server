from utils.shopUtils import reduce_real_currency
from utils.constantsUtils import TOMBOLA_TICKET_PRICE

def handle_tombolaBuyTicket(request, user_id, obj, json_data, config_data):
    if json_data["uTObj"]["t"] >= 5:
        return
    
    reduce_real_currency(TOMBOLA_TICKET_PRICE, json_data)
    json_data["uTObj"]["t"] += 1

    # Send to game
    obj["uTObj"] = json_data["uTObj"]
    obj["uObj"] = json_data["uObj"]