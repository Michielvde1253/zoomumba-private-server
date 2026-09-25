"""
Resources (json_data["res"]) have a storage limit, mCnt. The client never
shows more than that (ResourcesProxy.increaseResource clamps), so anything
over the limit is lost. Materials (json_data["mat"]) also carry an mCnt, but
the client doesn't clamp them (MaterialProxy.increaseMaterial), so they're
left uncapped.
"""


def get_resource(json_data, resource_id, user_id=None):
    resources = json_data.setdefault("res", {})
    return resources.setdefault(str(resource_id), {"uId": user_id if user_id is not None else json_data["uObj"].get("uId", 0),
                                                    "id": int(resource_id), "cnt": 0, "mCnt": 250})


def room_for(json_data, resource_id):
    """How many more of this resource fit in storage."""
    resource = get_resource(json_data, resource_id)
    if "mCnt" not in resource:
        return float("inf")
    return max(0, resource["mCnt"] - resource["cnt"])


def add_resource(json_data, resource_id, amount, user_id=None):
    """Add up to the storage limit; the rest is lost. Returns what was added."""
    resource = get_resource(json_data, resource_id, user_id)
    added = min(amount, room_for(json_data, resource_id))
    resource["cnt"] += added
    return added
