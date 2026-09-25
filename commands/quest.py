import time

from utils import questUtils, resourceUtils, shopUtils
from utils.zooErrors import ZooError, INVALID_REQUEST

# quest.gQ  {}        the daily quests; a new set once uObj.nDQ has passed
# quest.gNQ {}        a new set right away for 10 real currency
# quest.sQ  {"id"}    start a quest (only one can be active)
# quest.cQ  {"id"}    abort the active quest: it goes back to not started, progress lost
# quest.gR  {"id"}    collect the reward of a finished quest; the quest is removed
# The client doesn't add quest rewards itself, and drops its quest list
# before gQ/gNQ, so each answer carries the quests and uObj/res it changed.

RESYNC = ("qObj", "uObj")


def _quest(json_data, quest_id):
    quest = questUtils.get_daily(json_data).get(str(quest_id))
    if quest is None:
        raise ZooError(INVALID_REQUEST, f"no daily quest {quest_id}", resync=RESYNC)
    return quest


def _send_all(obj, json_data):
    obj["qObj"] = {"daily": questUtils.get_daily(json_data)}
    obj["uObj"] = json_data["uObj"]


def handle_questGetQuests(request, user_id, obj, json_data, config_data):
    if int(time.time()) >= int(json_data["uObj"].get("nDQ") or 0) or not questUtils.get_daily(json_data):
        questUtils.new_quests(json_data, config_data, user_id)
    _send_all(obj, json_data)


def handle_questBuyNewQuests(request, user_id, obj, json_data, config_data):
    shopUtils.reduce_real_currency(questUtils.RENEW_COST_REAL, json_data)
    next_due = json_data["uObj"].get("nDQ")
    questUtils.new_quests(json_data, config_data, user_id)
    if next_due and int(next_due) > int(time.time()):
        json_data["uObj"]["nDQ"] = next_due  # buying doesn't move the free refresh
    _send_all(obj, json_data)


def handle_questStart(request, user_id, obj, json_data, config_data):
    quest = _quest(json_data, request["id"])
    active = questUtils.active_quest_id(json_data)
    if active is not None and active != str(request["id"]):
        raise ZooError(INVALID_REQUEST, f"quest {active} is already active", resync=RESYNC)
    quest["active"] = 1
    questUtils.send_quest(obj, json_data, request["id"])


def handle_questCancel(request, user_id, obj, json_data, config_data):
    quest = _quest(json_data, request["id"])
    quest["active"] = 0
    quest["done"] = 0
    questUtils.reset_progress(json_data, request["id"])
    questUtils.send_quest(obj, json_data, request["id"])


def handle_questGetReward(request, user_id, obj, json_data, config_data):
    quest = _quest(json_data, request["id"])
    if int(quest.get("active", 0)) != 1 or int(quest.get("done", 0)) != 1:
        raise ZooError(INVALID_REQUEST, f"quest {request['id']} isn't finished", resync=RESYNC)

    reward = quest.get("reward", {})
    json_data["uObj"]["uCv"] += int(reward.get("currencyVirtual", 0))
    json_data["uObj"]["uCr"] += int(reward.get("currencyReal", 0))
    json_data["uObj"]["uEp"] += int(reward.get("xp", 0))
    for resource_id, amount in (reward.get("resources") or {}).items():
        if int(amount) > 0:
            resourceUtils.add_resource(json_data, resource_id, int(amount), user_id)
            obj["res"] = json_data["res"]

    del questUtils.get_daily(json_data)[str(request["id"])]
    json_data.setdefault("questTargets", {}).pop(str(request["id"]), None)
    questUtils.send_quest(obj, json_data, request["id"], deleted=True)
    obj["uObj"] = json_data["uObj"]
