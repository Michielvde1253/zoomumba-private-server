"""
Fallback handlers for every ZooApi.php command the client can send but the
server doesn't implement yet (the full list comes from NET.as in the client).

Real handlers registered in app.py `available_commands` always win; these are
only used when no real handler exists. There are four kinds:

  * read   - "get" style calls: answer t:1 and echo whatever matching state
             the player document already has, so client windows can open
             instead of waiting forever for a response.
  * noop   - telemetry / fire-and-forget calls: answer t:1, nothing else.
  * event  - seasonal event calls: answer t:0 "zoo.error.event.notRunning",
             the same code the original server used for inactive events.
  * todo   - calls that would change game state: answer t:0
             "zoo.error.notImplemented" and re-send uObj so the client drops
             the currency/XP change it already applied locally.

Anything not listed here (e.g. a command from a newer client) is treated as
"todo" by get_stub_handler().
"""
from utils.zooErrors import ZooError, NOT_IMPLEMENTED, EVENT_NOT_RUNNING


def _echo(*keys):
    """Read stub: copy top-level keys from the player document into the response."""
    def handler(request, user_id, obj, json_data, config_data):
        for key in keys:
            if key in json_data:
                obj[key] = json_data[key]
    return handler


def _echo_mail_outbox(request, user_id, obj, json_data, config_data):
    obj.setdefault("mObj", {})["ob"] = json_data.get("mObj", {}).get("ob", {"cnt": 0})


def _echo_specials(request, user_id, obj, json_data, config_data):
    specials = json_data.get("fObj", {}).get("specials")
    if specials is not None:
        obj.setdefault("fObj", {})["specials"] = specials


def _echo_game_items(request, user_id, obj, json_data, config_data):
    obj["gameItems"] = config_data["gameItems"]


def _noop(request, user_id, obj, json_data, config_data):
    pass


def _log_client_error(request, user_id, obj, json_data, config_data):
    error = request.get("error") if isinstance(request, dict) else request
    print(f"[client error] uId={user_id}: {str(error)[:2000]}")


def _event_not_running(request, user_id, obj, json_data, config_data):
    raise ZooError(EVENT_NOT_RUNNING, resync=())


def _not_implemented(request, user_id, obj, json_data, config_data):
    raise ZooError(NOT_IMPLEMENTED)


READ = {
    "achievement.ga": _echo("alObj"),
    "quest.gQ": _echo("qObj"),
    "friends.gFs": _echo("uFs"),
    "friends.gFrI": _echo("uFrI"),
    "friends.gFsI": _echo("uFsI"),
    "mail.gob": _echo_mail_outbox,
    "avatar.get": _echo("ava"),
    "avatar.getConfig": _echo("avaConf"),
    "rankings.get": _echo("rankObj"),
    "recyclingCenter.grs": _echo("recyclingSlots"),
    "safari.gC": _echo("uSCObj"),
    "safari.gS": _echo("uSObj"),
    "field.getSpecials": _echo_specials,
    "inv.get": _echo_game_items,
}

NOOP = {
    "error.set": _log_client_error,
    "test.testAdam": _noop,
}

EVENT = [
    "advBreedEvt.getConfig", "advBreedEvt.redeem",
    "boardgame.get", "boardgame.buy", "boardgame.put", "boardgame.explodeBallon",
    "caravan.wTp", "caravan.redeem",
    "loan.gI", "loan.dI",
    "circus.bMc", "circus.oMb",
    "communityPayin.getEvent", "communityPayin.putDrop", "communityPayin.redeem",
    "easter.getEvent", "easter.putEgg", "easter.buyEgg",
    "frog.getEvent", "frog.putDrop", "frog.buyDrop", "frog.swapBalloons",
    "halloween2012.getEvent", "halloween2012.putDrop", "halloween2012.buyDrop",
    "valentine.getConfig", "valentine.move", "valentine.redeem", "valentine.reset",
    "xmas.dR", "xmas.redeem",
    "xmas2012.getEvent", "xmas2012.putDrop", "xmas2012.buyDrop",
]

TODO = [
    "user.swap", "user.uBN",
    "init.getNeighbour",
    "collection.rs",
    "mail.dm", "mail.rm", "mail.sm",
    "packs.buy", "gifts.redeem",
    "quest.cQ", "quest.gR", "quest.gNQ", "quest.sQ",
    "safari.bG", "safari.bJ", "safari.eG", "safari.eA", "safari.sT", "safari.sS", "safari.uJ",
    "item.buyPU", "item.buySB",
    "friends.iFbI", "friends.aFbI", "friends.dFbI", "friends.cFbI",
    "avatar.set",
    "field.ul", "field.eFbC", "field.moveItemsToInventory",
    "managementCenter.upgrade",
    "recyclingCenter.icrs", "recyclingCenter.crs", "recyclingCenter.brs", "recyclingCenter.srm",
    "craftingCenter.sbc", "craftingCenter.gac", "craftingCenter.cbc", "craftingCenter.icbc", "craftingCenter.dbct",
]

STUB_COMMANDS = {}
STUB_COMMANDS.update(READ)
STUB_COMMANDS.update(NOOP)
STUB_COMMANDS.update({name: _event_not_running for name in EVENT})
STUB_COMMANDS.update({name: _not_implemented for name in TODO})


def get_stub_handler(command):
    """Stub for `command`, or the generic not-implemented handler if it's unknown."""
    return STUB_COMMANDS.get(command, _not_implemented)
