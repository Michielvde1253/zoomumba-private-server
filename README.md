
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

## AI disclaimer
Parts of the code in this repository has been written by AI. While we're not fully against this, it is really important that any code you submit has been read and understood by a human and is of decent quality.

## Assets
We're still looking for some of Zoomumba's assets. If you have them or know how to get them, feel free to contact us!

## List of game commands

This is a list of all the commands that the client mentions in its `Net.as` file and that the server should be able to handle.
For developers: you can regenerate this list with `python tools/command_status.py <NET.as>`.

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

### Stubbed

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

- [ ] avatar.set - AVATAR_SAVE
- [ ] friends.aFbI - FRIENDS_ACCEPT_FRIEND
- [ ] friends.cFbI - FRIENDS_CANCEL_FRIENDSHIP
- [ ] friends.dFbI - FRIENDS_DECLINE_FRIEND
- [ ] friends.iFbI - FRIENDS_INVITE_FRIEND
- [ ] gifts.redeem - REDEEM_GIFT
- [ ] init.getNeighbour - GET_NEIGHBOUR
- [ ] item.buyPU - BUY_POWERUP_SHOP
- [ ] mail.dm - MAIL_DELETE_ITEM
- [ ] mail.rm - MAIL_IS_READ
- [ ] mail.sm - MAIL_SEND_BY_ID
- [ ] managementCenter.upgrade - MANAGMENTCENTER_UPGRADE
- [ ] packs.buy - BUY_PROMO_PACK
- [ ] safari.bG - BUY_SAFARI_FUEL
- [ ] safari.bJ - SAFARI_BUY_JOKER
- [ ] safari.eA - EXPLORE_SAFARI_TILE
- [ ] safari.eG - SAFARI_END
- [ ] safari.sS - START_SAFARI
- [ ] safari.sT - SKIP_SAFARI_TIMER
- [ ] safari.uJ - USE_SAFARI_JOKER
- [ ] user.swap - SWAP_CURRENCY
- [ ] user.uBN - SEARCH_USER_BY_NAME

### Unimplemented event commands

- [ ] advBreedEvt.getConfig - ADVANCED_BREEDING_EVENT_CONFIG
- [ ] advBreedEvt.redeem - ADVANCED_BREEDING_EVENT_REDEEM
- [ ] boardgame.buy - BOARDGAME_BUY
- [ ] boardgame.explodeBallon - EXPLODE_BALLONS
- [ ] boardgame.explodeBallon - EXPLODE_BALLONS_TYPE
- [ ] boardgame.get - BOARDGAME_GET
- [ ] boardgame.put - BOARDGAME_PUT
- [ ] boardgame.put - BOARDGAME_PUT_INSTANT_BUY
- [ ] caravan.redeem - BABY_EVENT_REDEEM
- [ ] caravan.wTp - BABY_EVENT_TRADE_COLLECTABLE
- [ ] circus.bMc - CIRCUS_BUY_BOX
- [ ] circus.oMb - CIRCUS_OPEN_BOX
- [ ] communityPayin.getEvent - COMMUNITY_PAYIN_GET_EVENT
- [ ] communityPayin.putDrop - COMMUNITY_PAYIN_PUTDROP
- [ ] communityPayin.redeem - COMMUNITY_PAYIN_REDEEM
- [ ] easter.buyEgg - EASTER_BUY_EGG
- [ ] easter.getEvent - EASTER_GET_EVENT
- [ ] easter.putEgg - EASTER_PUT_EGG
- [ ] frog.buyDrop - FROG_BUY_DROPICON
- [ ] frog.getEvent - FROG_GET_EVENT
- [ ] frog.putDrop - FROG_PUT_DROPICON
- [ ] frog.swapBalloons - FROG_BUY_ANNIVERSARY
- [ ] halloween2012.buyDrop - HALLOWEEN2012_BUY_DROPICON
- [ ] halloween2012.getEvent - HALLOWEEN2012_GET_EVENT
- [ ] halloween2012.putDrop - HALLOWEEN2012_PUT_DROPICON
- [ ] loan.dI - BABY_CARAVAN_FINISH
- [ ] loan.gI - BABY_CARAVAN_DO_LOAN
- [ ] valentine.getConfig - VALENTINES_GET_CONFIG
- [ ] valentine.move - VALENTINES_MAKE_A_MOVE
- [ ] valentine.redeem - VALENTINES_REDEEM
- [ ] valentine.reset - VALENTINES_RESET
- [ ] xmas.dR - XMAS_GIVE_REINDEED_TO_SANTA_CLAUS
- [ ] xmas.redeem - XMAS_REDEEM_TREE
- [ ] xmas2012.buyDrop - XMAS2012_BUY_DROPICON
- [ ] xmas2012.getEvent - XMAS2012_GET_EVENT
- [ ] xmas2012.putDrop - XMAS2012_PUT_DROP
