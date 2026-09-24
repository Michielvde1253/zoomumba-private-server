def handle_swfCookieSet(request, user_id, obj, json_data, config_data):
    # The client sends {<name>: {"name": <name>, "timestamp": <int>}, ...}
    # and reads them back from init.getUser as swfCookies.cookies.
    if not isinstance(request, dict):
        return
    swf_cookies = json_data.setdefault("swfCookies", {})
    cookies = swf_cookies.get("cookies")
    if not isinstance(cookies, dict):
        cookies = {}
    for name, cookie in request.items():
        if isinstance(cookie, dict):
            cookies[name] = {"name": cookie.get("name", name), "timestamp": int(cookie.get("timestamp", 0))}
    swf_cookies["cookies"] = cookies
