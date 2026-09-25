
# Zoomumba Private Server

Zoomumba Private Server is an attempt to create a custom server for Zoomumba, a Bigpoint game.
Discord server: https://discord.gg/ukC5bEnqaC

## Legal Issues

This repository is made by Zoomumba fans, for Zoomumba fans. It's made out of nostalgia and will not be monetized in any way. Contact us for any legal problems, and we'll take appropriate action.

## How to play

A demo server is available at https://zoomumba-private-server.onrender.com/, but remember that this only a test server. Progress can be reset at any time and many features are not working yet.

## How to run the code locally

Install the libraries from requirements.txt, set up a MongoDB database and create a .env file like in the example. Then, simply run app.py!

You will need a browser that supports Flash (and Flash Player itself) to run the game. Alternatively, you can use [Flash Browser](https://github.com/radubirsan/FlashBrowser).

## Assets
We're still looking for some of Zoomumba's assets. If you have them or know how to get them, feel free to contact us!

## Running the tests

`tests/test_api.py` plays through the API the way the client does (register, buy, feed, breed, quests, inventory, ...) against an in-memory MongoDB, and checks both the answers and the saved player data:

```
pip install -r requirements.txt -r requirements-dev.txt
python tests/test_api.py
```

It exits non-zero if a check fails. It can't see what the Flash client does with the answers, so after bigger changes also run through [docs/PLAYTEST.md](docs/PLAYTEST.md) in the real client.

## How the server works

- **Transport:** the client POSTs to `/ZooApi.php?uId=&sid=&secTok=` with a form field `json` = `{"callstack": [{"<service>.<method>": {..., "req:": <request id>}}]}`. The answer is `{"callstack": {"<request id>": [{"t": 1|0, "v": <error code>}]}, "obj": {<state blocks>}}`. The client is state driven: whatever blocks come back in `obj` (`uObj`, `fObj`, `pfObj`, `res`, `animals`, `qObj`, ...) replace what it had.
- **Commands:** `app.py` maps each `service.method` to a handler in `commands/`; `field.fia` actions are in `commands/field_actions/` (registered in `commands/field_fia.py`), inventory actions in `commands/inventory_iva.py`. Shared game rules live in `utils/` (e.g. `cageCareUtils`, `dropUtils`, `questUtils`, `rewardUtils`, `resourceUtils`, `expansionUtils`, `fieldItemUtils`).
- **Field items:** `fObj.<type>.<fieldId>.<uniqueId>`, where field `"0"` is the inventory. Animals are `animals.<fieldId>.<cageId>.<uniqueId>`, inventory animals `animals."0"."0".<uniqueId>`. An item sent back with `del: 1` is removed on the client, with `del: 1, inv: 1` it moves to the inventory.
- **Optimistic client:** for most actions the client already changed its own numbers (money, resources, xp) before the answer arrives, so handlers always send back the authoritative blocks they changed.
- **Errors:** a handler can `raise ZooError(code)` (`utils/zooErrors.py`). The server rolls back that handler's changes to the player data, answers the call with `t:0`, and re-sends `uObj` (or the blocks named in `resync`) so the client drops its optimistic changes. Unexpected exceptions do the same with `zoo.error.internal`, so one broken handler never turns the whole request into an HTTP 500.
- **Stubs:** commands without a real implementation fall back to `commands/stubs.py`: "get" style calls answer `t:1` with whatever matching data the player document has, seasonal event calls answer `t:0 zoo.error.event.notRunning` (like the original server for inactive events), and anything else answers `t:0 zoo.error.notImplemented`.
- **Login repairs:** `init.getUser` fixes things older saves can have wrong: animal records that don't match the cage counters, zoo grid bounds that don't match the zoo size, and level-based expansions that were never granted.

## List of game commands

Every command in the client's `NET.as`: 101 implemented, 14 stubbed, 36 seasonal event commands (answer "event not running"), 22 not implemented yet. Regenerate with `python tools/command_status.py <NET.as>`.

### Implemented

- [x] collection.rs - REDEEM_COLLECTION_SET_REWARD
- [x] config.getConfig - GET_CONFIG
- [x] config.getCv - GET_CV_LIST
- [x] coupon.redeem - REDEEM_BONUS_CODE
- [x] craftingCenter.cbc - CRAFTING_COLLECT
- [x] craftingCenter.dbct - CRAFTING_TIME_DECREASE
- [x] craftingCenter.gac - CRAFTING_GET_REWARD
- [x] craftingCenter.icbc - CRAFTING_COLLECT_INSTANT
- [x] craftingCenter.sbc - CRAFTING_START
- [x] field.eFbC - EXTEND_FORGOTTEN_ZOO_TOOLS_BUY
- [x] field.fia (`beAC`) - BREED_END
- [x] field.fia (`bsAC`) - BREED_START
- [x] field.fia (`bdC`) - BUILD_CAGE_BUY
- [x] field.fia (`bdD`) - BUILD_DECO_BUY
- [x] field.fia (`bdSt`) - BUILD_STORE_BUY
- [x] field.fia (`bAC`) - BUY_ANIMAL_CAGE
- [x] field.fia (`bAInv`) - BUY_ANIMAL_TO_INVENTORY
- [x] field.fia (`bAs`) - BUY_ASSISTANT
- [x] field.fia (`bSB`) - BUY_BREEDING_LAB
- [x] field.fia (`bC`) - BUY_CAGE
- [x] field.fia (`bD`) - BUY_DECO
- [x] field.fia (`bSB`) - BUY_NURSERY
- [x] field.fia (`bP`) - BUY_PREMIUM
- [x] field.fia (`bP`) - BUY_PREMIUM_WITH_COUT
- [x] field.fia (`bIr`) - BUY_RESOURCE
- [x] field.fia (`bR`) - BUY_ROAD
- [x] field.fia (`bSt`) - BUY_STORE
- [x] field.fia (`bTb`) - BUY_TRASHBIN
- [x] field.fia (`cAC`) - CLEAN_ANIMAL_CAGE
- [x] field.fia (`cAt`) - CLEAR_ASSISTANT_TIMER
- [x] field.fia (`cTb`) - CLEAR_TRASH_BIN
- [x] field.fia (`cTr`) - CLEAR_TRASH_ROAD
- [x] field.fia (`cEf`) - COLLECT_ENTRANCE_FEE
- [x] field.fia (`cSt`) - COLLECT_STORE_MONEY
- [x] field.fia (`cuAC`) - CUDDLE_ANIMAL_CAGE
- [x] field.fia (`bdAC`) - DIRECT_BREED
- [x] field.fia (`beASB`) - END_ADVANCED_BREEDING_NET
- [x] field.fia (`reASB`) - END_NURSERY_BREEDING
- [x] field.fia (`fAC`) - FEED_ANIMAL_CAGE
- [x] field.fia (`hAC`) - HEAL_ANIMAL_CAGE
- [x] field.fia (`rdASB`) - INSTANT_NURSERY_BREEDING
- [x] field.fia (`mAC`) - MOVE_ANIMAL_CAGE
- [x] field.fia (`mSB`) - MOVE_BREEDING_LAB
- [x] field.fia (`mC`) - MOVE_CAGE
- [x] field.fia (`mD`) - MOVE_DECO
- [x] field.fia (`mSB`) - MOVE_NURSERY
- [x] field.fia (`mR`) - MOVE_ROAD
- [x] field.fia (`mSt`) - MOVE_STORE
- [x] field.fia (`mTb`) - MOVE_TRASH_BIN
- [x] field.fia (`pfAC`) - POWER_FEED_ANIMAL_CAGE
- [x] field.fia (`uApfA`) - POWER_FEED_ASSISTANT
- [x] field.fia (`sEb`) - SAVE_ACTIV_MAIN_BUILDING
- [x] field.fia (`sAC`) - SELL_ANIMAL_CAGE
- [x] field.fia (`sC`) - SELL_CAGE
- [x] field.fia (`sD`) - SELL_DECO
- [x] field.fia (`sR`) - SELL_ROAD
- [x] field.fia (`sSB`) - SELL_SPECIAL_ITEM
- [x] field.fia (`sSt`) - SELL_STORE
- [x] field.fia (`sTb`) - SELL_TRASH_BIN
- [x] field.fia (`bsASB`) - START_ADVANCED_BREEDING_NET
- [x] field.fia (`rsASB`) - START_NURSERY_BREEDING
- [x] field.fia (`sfAC`) - SUPER_FEED_ANIMAL_CAGE
- [x] field.fia (`uAsfA`) - SUPER_FEED_ASSISTANT
- [x] field.fia (`shAC`) - SUPER_HEAL_ANIMAL_CAGE
- [x] field.fia (`uAshC`) - SUPER_HEAL_ASSISTANT
- [x] field.fia (`uc`) - UPGRADE_CAGE
- [x] field.fia (`uCa`) - UPGRADE_EVENT_CAGE
- [x] field.fia (`uA`) - USE_ASSISTANT
- [x] field.fia (`bdASB`) - USE_ELIXIR
- [x] field.fia (`arASB`) - USE_RAISING_POTION
- [x] field.fia (`wAC`) - WATER_ANIMAL_CAGE
- [x] field.moveItemsToInventory - MOVE_ITEMS_TO_INVENTORY
- [x] field.ul - UNLOCK_FIELD
- [x] gameitems.get - SHOP_ITEMS_GET
- [x] init.getUser - GET_USER
- [x] init.sP - SWITCH_PLAYFIELD
- [x] inventory.iva - MOVE_ANIMAL_FROM_FIELD_TO_INVENTORY
- [x] inventory.iva - MOVE_ANIMAL_FROM_INVENTORY_TO_CAGE
- [x] inventory.iva - MOVE_ITEM_FROM_FIELD_TO_INVENTORY
- [x] inventory.iva - MOVE_ITEM_FROM_INVENTORY_TO_FIELD
- [x] inventory.iva - REQUEST_INVENTORY
- [x] inventory.iva - SELL_ITEM_FROM_INVENTORY
- [x] item.buySB - RECYCLE_BUY_SURPRISEBOX
- [x] mail.gib - MAIL_GET_INBOX
- [x] managementCenter.get - MANAGMENT_CENTER_GET
- [x] push.get - PUSH
- [x] quest.cQ - CANCEL_QUEST
- [x] quest.gNQ - BUY_NEW_QUESTS
- [x] quest.gQ - GET_QUESTS
- [x] quest.gR - FINISH_QUEST
- [x] quest.sQ - START_QUEST
- [x] recyclingCenter.brs - RECYCLE_BOOK_NEW_SLOT
- [x] recyclingCenter.crs - RECYCLE_COLLLECT_RECYCLE_SLOT
- [x] recyclingCenter.grs - RECYCLE_GET_SLOTS
- [x] recyclingCenter.icrs - RECYCLE_INSTANT_COLLLECT_RECYCLE_SLOT
- [x] recyclingCenter.srm - RECYCLE_START_RECYCLE_MATERIAL
- [x] swfCookie.set - SAVE_FLASH_COOKIE
- [x] swfOpt.set - SET_USER
- [x] tombola.bTT - BUY_FORTUNE_WHEEL_TICKET
- [x] tombola.rTT - REDEEM_FORTUNE_WHEEL_TICKET
- [x] tutorial.rS - TUTORIAL_STORE_STATS

### Stubbed (the client gets an answer, nothing is changed)

- [ ] achievement.ga - GET_ACHIEVEMENTS — stub: returns saved data
- [ ] avatar.get - AVATAR_GET — stub: returns saved data
- [ ] avatar.getConfig - AVATAR_GET_CONFIG — stub: returns saved data
- [ ] error.set - LOG_FLASH_ERROR — stub: accepted, ignored
- [ ] field.getSpecials - GET_SPECIALS_DATA — stub: returns saved data
- [ ] friends.gFrI - FRIENDS_INVITATIONS_RECEIVED — stub: returns saved data
- [ ] friends.gFs - FRIENDS_FRIENDSHIPS — stub: returns saved data
- [ ] friends.gFsI - FRIENDS_INVITATIONS_SENT — stub: returns saved data
- [ ] inv.get - INVENTORY_GET — stub: returns saved data
- [ ] mail.gob - MAIL_GET_OUTBOX — stub: returns saved data
- [ ] rankings.get - GET_RANKING_LIST — stub: returns saved data
- [ ] safari.gC - GET_SAFARI_CONFIG — stub: returns saved data
- [ ] safari.gS - GET_SAFARI_SATE — stub: returns saved data
- [ ] test.testAdam - DEBUG_PHP_ACTION — stub: accepted, ignored

### Not implemented yet

- [ ] avatar.set - AVATAR_SAVE — not implemented
- [ ] friends.aFbI - FRIENDS_ACCEPT_FRIEND — not implemented
- [ ] friends.cFbI - FRIENDS_CANCEL_FRIENDSHIP — not implemented
- [ ] friends.dFbI - FRIENDS_DECLINE_FRIEND — not implemented
- [ ] friends.iFbI - FRIENDS_INVITE_FRIEND — not implemented
- [ ] gifts.redeem - REDEEM_GIFT — not implemented
- [ ] init.getNeighbour - GET_NEIGHBOUR — not implemented
- [ ] item.buyPU - BUY_POWERUP_SHOP — not implemented
- [ ] mail.dm - MAIL_DELETE_ITEM — not implemented
- [ ] mail.rm - MAIL_IS_READ — not implemented
- [ ] mail.sm - MAIL_SEND_BY_ID — not implemented
- [ ] managementCenter.upgrade - MANAGMENTCENTER_UPGRADE — not implemented
- [ ] packs.buy - BUY_PROMO_PACK — not implemented
- [ ] safari.bG - BUY_SAFARI_FUEL — not implemented
- [ ] safari.bJ - SAFARI_BUY_JOKER — not implemented
- [ ] safari.eA - EXPLORE_SAFARI_TILE — not implemented
- [ ] safari.eG - SAFARI_END — not implemented
- [ ] safari.sS - START_SAFARI — not implemented
- [ ] safari.sT - SKIP_SAFARI_TIMER — not implemented
- [ ] safari.uJ - USE_SAFARI_JOKER — not implemented
- [ ] user.swap - SWAP_CURRENCY — not implemented
- [ ] user.uBN - SEARCH_USER_BY_NAME — not implemented

### Seasonal events (answer "event not running")

- [ ] advBreedEvt.getConfig - ADVANCED_BREEDING_EVENT_CONFIG — event not running
- [ ] advBreedEvt.redeem - ADVANCED_BREEDING_EVENT_REDEEM — event not running
- [ ] boardgame.buy - BOARDGAME_BUY — event not running
- [ ] boardgame.explodeBallon - EXPLODE_BALLONS — event not running
- [ ] boardgame.explodeBallon - EXPLODE_BALLONS_TYPE — event not running
- [ ] boardgame.get - BOARDGAME_GET — event not running
- [ ] boardgame.put - BOARDGAME_PUT — event not running
- [ ] boardgame.put - BOARDGAME_PUT_INSTANT_BUY — event not running
- [ ] caravan.redeem - BABY_EVENT_REDEEM — event not running
- [ ] caravan.wTp - BABY_EVENT_TRADE_COLLECTABLE — event not running
- [ ] circus.bMc - CIRCUS_BUY_BOX — event not running
- [ ] circus.oMb - CIRCUS_OPEN_BOX — event not running
- [ ] communityPayin.getEvent - COMMUNITY_PAYIN_GET_EVENT — event not running
- [ ] communityPayin.putDrop - COMMUNITY_PAYIN_PUTDROP — event not running
- [ ] communityPayin.redeem - COMMUNITY_PAYIN_REDEEM — event not running
- [ ] easter.buyEgg - EASTER_BUY_EGG — event not running
- [ ] easter.getEvent - EASTER_GET_EVENT — event not running
- [ ] easter.putEgg - EASTER_PUT_EGG — event not running
- [ ] frog.buyDrop - FROG_BUY_DROPICON — event not running
- [ ] frog.getEvent - FROG_GET_EVENT — event not running
- [ ] frog.putDrop - FROG_PUT_DROPICON — event not running
- [ ] frog.swapBalloons - FROG_BUY_ANNIVERSARY — event not running
- [ ] halloween2012.buyDrop - HALLOWEEN2012_BUY_DROPICON — event not running
- [ ] halloween2012.getEvent - HALLOWEEN2012_GET_EVENT — event not running
- [ ] halloween2012.putDrop - HALLOWEEN2012_PUT_DROPICON — event not running
- [ ] loan.dI - BABY_CARAVAN_FINISH — event not running
- [ ] loan.gI - BABY_CARAVAN_DO_LOAN — event not running
- [ ] valentine.getConfig - VALENTINES_GET_CONFIG — event not running
- [ ] valentine.move - VALENTINES_MAKE_A_MOVE — event not running
- [ ] valentine.redeem - VALENTINES_REDEEM — event not running
- [ ] valentine.reset - VALENTINES_RESET — event not running
- [ ] xmas.dR - XMAS_GIVE_REINDEED_TO_SANTA_CLAUS — event not running
- [ ] xmas.redeem - XMAS_REDEEM_TREE — event not running
- [ ] xmas2012.buyDrop - XMAS2012_BUY_DROPICON — event not running
- [ ] xmas2012.getEvent - XMAS2012_GET_EVENT — event not running
- [ ] xmas2012.putDrop - XMAS2012_PUT_DROP — event not running
