def handle_getConfig(request, user_id, obj, json_data, config_data):
    # config_data is loaded once by utils.configUtils and shared (read-only)
    obj["config"] = config_data
