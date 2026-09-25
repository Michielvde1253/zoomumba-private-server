"""
Error handling for ZooApi.php commands.

A command handler can raise ZooError to tell the client that the call failed.
The server then:
  * rolls back any changes the handler made to the player's data,
  * answers the call with {"t": 0, "v": <code>} in the callstack (this triggers
    the client's addCallbackIfFalse(...) handlers instead of the IfTrue ones),
  * re-sends the authoritative state blocks listed in `resync` (default: uObj)
    so the client drops any optimistic changes it already showed.

Codes the client shows a window for (see ErrorHandlerCommand.as):
  system.user.maintenance, zoo.user.notAuth, system.user.notAuth,
  zoo.error.contact.noSuchUser, zoo.error.invite.recruitexists,
  zoo.error.field.notHappy, zoo.error.coupon.invalid,
  zoo.error.coupon.participated, zoo.error.coupon.bruteForce,
  zoo.error.circus.limitReached
Any other code is silently ignored by the client (only the callbacks fire).
"""

# Codes used by the original server (seen in the zoomumba.com HAR capture)
EVENT_NOT_RUNNING = "zoo.error.event.notRunning"
NOT_AUTH = "system.user.notAuth"
MAINTENANCE = "system.user.maintenance"
FIELD_NOT_HAPPY = "zoo.error.field.notHappy"
COUPON_INVALID = "zoo.error.coupon.invalid"
COUPON_PARTICIPATED = "zoo.error.coupon.participated"
NO_SUCH_USER = "zoo.error.contact.noSuchUser"

# Private-server codes (not known to the client, so no popup is shown)
NOT_IMPLEMENTED = "zoo.error.notImplemented"
NOT_ENOUGH_MONEY = "zoo.error.notEnoughMoney"
NOT_ENOUGH_RESOURCES = "zoo.error.notEnoughResources"
INVALID_REQUEST = "zoo.error.invalidRequest"
INTERNAL = "zoo.error.internal"


class ZooError(Exception):
    def __init__(self, code=INVALID_REQUEST, message=None, resync=("uObj",)):
        super().__init__(message or code)
        self.code = code
        self.resync = tuple(resync)
