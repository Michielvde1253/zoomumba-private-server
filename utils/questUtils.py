"""
Daily quests (qObj.daily), as the client's QuestsProxy / DailyQuestsTabMediator
expect them:

  qObj.daily.<qdId> = {"qdId", "uId", "active", "done", "endTime",
                       "tasks": [{"affectAll", "itemType": "species", "itemId",
                                  "actionName": feed|water|clean|cuddle,
                                  "actionCount"}],
                       "reward": {"currencyVirtual", "currencyReal", "xp",
                                  "resources": {"8": n, "9": n}}}
  uObj.nDQ = when the next set of quests is due (the window counts down to it
             and then calls quest.gQ).

At most 5 quests (the window refetches if there are more), one active at a
time. The client never counts progress itself; it only shows actionCount. So
the server counts actionCount down as the player works through a task (the
client's task object is sealed, so no extra progress field can be sent) and
keeps the original counts in questTargets.<qdId> to reset an aborted quest.
A quest is done when every task is at 0.
"""
import copy
import random
import time

QUEST_COUNT = 5
QUEST_LIFETIME = 24 * 3600
RENEW_COST_REAL = 10          # DailyQuestsTabMediator.renewQuests checks realMoney >= 10
ACTIONS = ("feed", "water", "clean", "cuddle")
ACTION_EXP_FIELD = {"feed": "feedExpReward", "water": "waterExpReward",
                    "clean": "cleanExpReward", "cuddle": "cuddleExpReward"}
# field.fia -> quest actionName
FIA_ACTIONS = {"fAC": "feed", "wAC": "water", "cAC": "clean", "cuAC": "cuddle"}


def get_daily(json_data):
    qobj = json_data.setdefault("qObj", {})
    if not isinstance(qobj.get("daily"), dict):
        qobj["daily"] = {}
    return qobj["daily"]


def targets(json_data, quest_id):
    """The original actionCounts of a quest (the stored ones count down)."""
    quest = get_daily(json_data)[str(quest_id)]
    return json_data.setdefault("questTargets", {}).setdefault(
        str(quest_id), [int(task["actionCount"]) for task in quest["tasks"]])


def reset_progress(json_data, quest_id):
    quest = get_daily(json_data)[str(quest_id)]
    for task, target in zip(quest["tasks"], targets(json_data, quest_id)):
        task["actionCount"] = target


def send_quest(obj, json_data, quest_id, deleted=False):
    quest = get_daily(json_data)[str(quest_id)] if not deleted else {"qdId": str(quest_id), "del": 1}
    obj.setdefault("qObj", {}).setdefault("daily", {})[str(quest_id)] = quest


def active_quest_id(json_data):
    for qid, quest in get_daily(json_data).items():
        if int(quest.get("active", 0)) == 1:
            return qid
    return None


# ---- generating ----

def owned_species(json_data, config_data):
    species = set()
    for field_id, cages in (json_data.get("fObj", {}).get("cages") or {}).items():
        if field_id == "0" or not isinstance(cages, dict):
            continue
        for cage in cages.values():
            if cage.get("sId") and cage.get("male", 0) + cage.get("female", 0) + cage.get("child", 0) > 0:
                species.add(cage["sId"])
    return sorted(s for s in species if str(s) in config_data["gameItems"]["animalsSpecies"])


def make_reward(config_data, tasks):
    """Rough fit to the rewards in the HAR capture: ~150 xp plus half the
    species' action xp per action, and/or a flat 350-400 coins."""
    xp = 0
    for task in tasks:
        species = config_data["gameItems"]["animalsSpecies"][str(task["itemId"])]
        xp += task["actionCount"] * (150 + species.get(ACTION_EXP_FIELD[task["actionName"]], 0) // 2)
    kind = random.choice(("both", "xp", "coins"))
    return {"currencyVirtual": random.randint(350, 400) if kind != "xp" else 0,
            "xp": xp if kind != "coins" else 0,
            "resources": {"8": 0, "9": 0}, "currencyReal": 0}


def new_quests(json_data, config_data, user_id):
    """Replace the daily quests with a fresh set (none if the zoo has no animals yet).
    Returns the ids that were dropped."""
    daily = get_daily(json_data)
    dropped = list(daily)
    daily.clear()
    json_data["questTargets"] = {}

    now = int(time.time())
    end_time = now + QUEST_LIFETIME
    json_data["uObj"]["nDQ"] = end_time
    species = owned_species(json_data, config_data)
    if not species:
        return dropped

    for _ in range(QUEST_COUNT):
        tasks, used = [], set()
        for _ in range(random.choice((1, 1, 1, 2, 3))):
            species_id, action = random.choice(species), random.choice(ACTIONS)
            if (species_id, action) in used:
                continue
            used.add((species_id, action))
            tasks.append({"affectAll": 0, "itemType": "species", "itemId": species_id,
                          "actionName": action, "actionCount": random.randint(5, 15)})
        quest_id = str(json_data["next_object_id"])
        json_data["next_object_id"] += 1
        daily[quest_id] = {"qdId": quest_id, "uId": str(user_id), "active": 0, "done": 0,
                           "endTime": end_time, "tasks": tasks, "reward": make_reward(config_data, tasks)}
        targets(json_data, quest_id)
    return dropped


# ---- progress ----

def count_cage_action(obj, json_data, cage, fia):
    """A cage action happened: advance the active quest's matching tasks."""
    action = FIA_ACTIONS.get(fia)
    quest_id = active_quest_id(json_data)
    if action is None or quest_id is None:
        return
    quest = get_daily(json_data)[quest_id]
    if int(quest.get("done", 0)) == 1:
        return
    targets(json_data, quest_id)  # remember the original counts before the first one goes down
    changed = False
    for task in quest["tasks"]:
        if task["actionName"] != action or int(task["actionCount"]) <= 0:
            continue
        if int(task.get("affectAll", 0)) == 1 or int(task["itemId"]) == int(cage.get("sId", 0)):
            task["actionCount"] = int(task["actionCount"]) - 1
            changed = True
    if not changed:
        return
    if all(int(task["actionCount"]) <= 0 for task in quest["tasks"]):
        quest["done"] = 1
    send_quest(obj, json_data, quest_id)
