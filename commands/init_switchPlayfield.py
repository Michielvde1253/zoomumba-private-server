import time

def handle_switchPlayfield(request, user_id, obj, json_data, config_data):
    # To-do: only send requested field (if possible)
    type = str(request["type"])
    json_data["uObj"]["current_field"] = json_data["fIds"][type]

    obj["fObj"] = json_data["fObj"]