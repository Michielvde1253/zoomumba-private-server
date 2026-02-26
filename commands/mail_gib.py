
def handle_mailGetInbox(request, user_id, obj, json_data, config_data):
    obj["mObj"] = {}
    obj["mObj"]["ib"] = json_data["mObj"]["ib"]