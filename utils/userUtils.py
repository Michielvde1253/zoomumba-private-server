def get_total_user_count():
    return total_user_count

def set_total_user_count(count):
    global total_user_count
    total_user_count = count

def get_zoo_from_db_by_userid(data_db, userid):
    return data_db.find_one({'id': userid})

def replace_placeholders(json_file, placeholder_value, replacement_value):
    """
    Replaces the placeholders in the new_player.json file.
    """
    data = json_file
    
    # Recursive function to replace placeholders
    def replace_values(obj):
        if isinstance(obj, dict):
            return {replace_values(key): replace_values(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [replace_values(item) for item in obj]
        elif isinstance(obj, str) and obj == placeholder_value:
            return replacement_value
        return obj
    
    # Replace placeholders
    return replace_values(data)

def get_differences(old_dict, new_dict):
    """
    Compares two dictionaries and returns the differences.
    """
    added = {k: new_dict[k] for k in new_dict if k not in old_dict}
    removed = {k: old_dict[k] for k in old_dict if k not in new_dict}
    modified = {k: new_dict[k] for k in new_dict if k in old_dict and old_dict[k] != new_dict[k]}
    
    return added, removed, modified

def save_zoo(collection, user_id, added, removed, modified):
    """
    Updates only the changed fields in the MongoDB document.
    """
    update_query = {}
    if added or modified:
        update_query["$set"] = {f"zoo.{k}": v for k, v in {**added, **modified}.items()}
    if removed:
        update_query["$unset"] = {f"zoo.{k}": "" for k in removed}

    if update_query:
        collection.update_one({"id": user_id}, update_query)

def calculate_level_based_on_xp(xp, config_data):
    for i in range(len(config_data["main"]["u_level"])):
        if xp < int(config_data["main"]["u_level"][i]):
            return i
    return 0