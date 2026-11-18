# codes that the client supports
EVENT_NOT_RUNNING = "zoo.error.event.notRunning"
NOT_AUTH = "system.user.notAuth"
MAINTENANCE = "system.user.maintenance"
FIELD_NOT_HAPPY = "zoo.error.field.notHappy"
COUPON_INVALID = "zoo.error.coupon.invalid"
COUPON_PARTICIPATED = "zoo.error.coupon.participated"
NO_SUCH_USER = "zoo.error.contact.noSuchUser"

# codes that are defined by us, client ignores them
NOT_IMPLEMENTED = "zoo.error.notImplemented"
NOT_ENOUGH_MONEY = "zoo.error.notEnoughMoney"
NOT_ENOUGH_RESOURCES = "zoo.error.notEnoughResources"
INVALID_REQUEST = "zoo.error.invalidRequest"
INTERNAL = "zoo.error.internal"


class ZooError(Exception):
    def __init__(self, code=INVALID_REQUEST, message=None, resync=("uObj",)):
        super().__init__(message or code)
        self.code = code
        self.resync = tuple(resync) # resend these to the client, used in case a command is rejected but the client already applied it locally
