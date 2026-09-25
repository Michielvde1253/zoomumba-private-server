from utils import cageCareUtils, shopUtils, trashbinUtils, fieldItemUtils as items
from utils.zooErrors import ZooError, INVALID_REQUEST

# Assistants (asObj.<asId> = {"asId", "end", "nL"}): while `end` is in the
# future the player can use them. nL=1 stops the "your assistant ran out,
# renew?" popup (AssistancesProxy).
#
#   bAs   {"asId", "cR", "type": 1|2|3}  hire for lifeTime[type] (1/7/28 days) for buyReal[type]
#   cAt   {"asId"}                       player closed the renew popup: don't show it again
#   uA    {"asId"}                       run the assistant over the whole current zoo
#   uAsfA / uApfA {"asId": 1|8}          feed assistant super feeds / power feeds every cage below 80% food
#   uAshC {"asId": 7}                    heal assistant super heals every sick cage
#
# The client changes nothing itself when an assistant works: it compares the
# cages, currencies and resources it gets back with what it had and shows the
# difference (GameManager.handleCagesData), so we send every cage of the zoo
# (it also takes the count of cages sent as the zoo's cage count), res and uObj.
# Cages are worked through in order until the resources run out; assistants
# add their xpMod as extra xp.

FEED, WATER, CLEAN, CUDDLE, TRASH, CASH, HEAL = 1, 2, 3, 4, 5, 6, 7
OCEAN = {FEED: 8, WATER: 9, CLEAN: 10, CUDDLE: 11}
CARE = {FEED: "feed", WATER: "water", CLEAN: "clean", CUDDLE: "cuddle", HEAL: "heal",
        8: "feed", 9: "water", 10: "clean", 11: "cuddle"}
DIRECTOR = 0


def _assistants(json_data):
    return json_data.setdefault("asObj", {})


def is_active(json_data, assistant_id):
    entry = _assistants(json_data).get(str(assistant_id))
    return entry is not None and int(entry.get("end") or 0) > items.now()


def _require(json_data, assistant_id):
    if not is_active(json_data, assistant_id):
        raise ZooError(INVALID_REQUEST, f"assistant {assistant_id} isn't hired", resync=("asObj",))


def _xp_mod(config_data, assistant_id):
    return float(config_data["gameItems"]["assists"].get(str(assistant_id), {}).get("xpMod", 0))


def _cages(json_data, field_id):
    return list(items.get_items(json_data, "cages", field_id).values())


def _care_for_all(obj, json_data, config_data, field_id, action, assistant_id):
    done = 0
    for cage in _cages(json_data, field_id):
        if cageCareUtils.needs(config_data, cage, action) and \
                cageCareUtils.perform(obj, json_data, config_data, cage, action, field_id, _xp_mod(config_data, assistant_id)):
            done += 1
    return done


def _clear_trash(json_data, config_data, field_id):
    field = json_data["pfObj"][str(field_id)]
    amount = field.get("trashroads", 0) + field.get("trashbins", 0)
    field["trashroads"] = field["trashbins"] = 0
    trashbinUtils.give_trash_rewards(json_data, amount)
    json_data["uObj"]["uEp"] += int(amount * float(config_data["gameItems"]["assists"].get(str(TRASH), {}).get("trashMod", 0)))
    return amount


def _collect_stores(obj, json_data, config_data, field_id):
    collected = 0
    for store in items.get_items(json_data, "stores", field_id).values():
        config = items.item_config(config_data, "stores", store)
        if store.get("build", 0) > items.now() or store.get("collect", 0) > items.now():
            continue
        store["collect"] = items.now() + int(config["collectTime"])
        json_data["uObj"]["uCv"] += int(config["collectVirtual"])
        items.send_item(obj, "stores", field_id, store)
        collected += 1
    return collected


def _send_zoo(obj, json_data, field_id):
    for cage in _cages(json_data, field_id):
        items.send_item(obj, "cages", field_id, cage)
    obj["uObj"] = json_data["uObj"]
    obj["res"] = json_data["res"]


def handle_useAssistant(request, user_id, obj, json_data, config_data, current_field_id):
    assistant_id = int(request["asId"])
    ocean = cageCareUtils.is_ocean(json_data, current_field_id)

    if assistant_id == DIRECTOR:
        # The zoo director does the feed, water, clean and cuddle rounds at once
        # and needs all of the zoo's assistants (AssistancesProxy.haveAllAssistantsActive)
        crew = [OCEAN[a] if ocean else a for a in (FEED, WATER, CLEAN, CUDDLE)] + [TRASH, CASH]
        for member in crew:
            _require(json_data, member)
        for member in crew[:4]:
            _care_for_all(obj, json_data, config_data, current_field_id, CARE[member], member)
    else:
        _require(json_data, assistant_id)
        if assistant_id in CARE:
            _care_for_all(obj, json_data, config_data, current_field_id, CARE[assistant_id], assistant_id)
        elif assistant_id == TRASH:
            _clear_trash(json_data, config_data, current_field_id)
            obj["pfObj"] = json_data["pfObj"]
        elif assistant_id == CASH:
            _collect_stores(obj, json_data, config_data, current_field_id)
        else:
            raise ZooError(INVALID_REQUEST, f"unknown assistant {assistant_id}")

    _send_zoo(obj, json_data, current_field_id)


def _special_round(action, request, obj, json_data, config_data, current_field_id):
    assistant_id = int(request["asId"])
    _require(json_data, assistant_id)
    _care_for_all(obj, json_data, config_data, current_field_id, action, assistant_id)
    _send_zoo(obj, json_data, current_field_id)


def handle_superFeedAssistant(request, user_id, obj, json_data, config_data, current_field_id):
    _special_round("superfeed", request, obj, json_data, config_data, current_field_id)


def handle_powerFeedAssistant(request, user_id, obj, json_data, config_data, current_field_id):
    _special_round("powerfeed", request, obj, json_data, config_data, current_field_id)


def handle_superHealAssistant(request, user_id, obj, json_data, config_data, current_field_id):
    _special_round("superheal", request, obj, json_data, config_data, current_field_id)


def handle_buyAssistant(request, user_id, obj, json_data, config_data, current_field_id):
    assistant_id = str(request["asId"])
    config = config_data["gameItems"]["assists"].get(assistant_id)
    tier = str(request.get("type", 1))
    if config is None or tier not in config.get("lifeTime", {}):
        raise ZooError(INVALID_REQUEST, f"no assistant {assistant_id} / duration {tier}")
    shopUtils.reduce_real_currency(int(config["buyReal"][tier]), json_data)

    entry = _assistants(json_data).setdefault(assistant_id, {"asId": assistant_id, "end": "0", "nL": "1"})
    entry["end"] = str(max(items.now(), int(entry.get("end") or 0)) + int(config["lifeTime"][tier]))
    entry["nL"] = "0"  # ask to renew when it runs out
    obj["asObj"] = _assistants(json_data)
    obj["uObj"] = json_data["uObj"]


def handle_clearAssistantTimer(request, user_id, obj, json_data, config_data, current_field_id):
    entry = _assistants(json_data).get(str(request["asId"]))
    if entry is None:
        raise ZooError(INVALID_REQUEST, f"no assistant {request['asId']}")
    entry["nL"] = "1"
    obj["asObj"] = _assistants(json_data)
