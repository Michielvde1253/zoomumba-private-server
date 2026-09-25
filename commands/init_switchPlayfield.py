from utils import playfieldUtils
from utils.zooErrors import ZooError, INVALID_REQUEST

# init.sP {"fId", "type"}: show another zoo. The client clears its field and
# rebuilds it from actFId (which zoo type is active), pfObj (renders the
# ground, gate and bounds) and fObj/animals of that zoo (SwitchPlayfieldCommand).


def handle_switchPlayfield(request, user_id, obj, json_data, config_data):
    field_id = playfieldUtils.field_id_of(json_data, request.get("type"))
    if field_id is None:
        raise ZooError(INVALID_REQUEST, f"no zoo of type {request.get('type')}", resync=("fIds",))
    json_data["uObj"]["current_field"] = field_id
    json_data["actFId"] = field_id

    obj["actFId"] = field_id
    obj["pfObj"] = json_data["pfObj"]
    obj["fObj"] = json_data["fObj"]
    obj["animals"] = json_data["animals"]
    obj["uObj"] = json_data["uObj"]
