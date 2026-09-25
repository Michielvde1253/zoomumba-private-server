from field_actions import *
from utils.zooErrors import ZooError, NOT_IMPLEMENTED

available_field_actions = {
    "bC": handle_buyCage,
    "bAC": handle_buyAnimalCage,
    "bR": handle_buyRoad,
    "bD": handle_buyDeco,
    "bIr": handle_buyResource,
    "bSt": handle_buyStore,
    "fAC": handle_feedWaterAnimalCage,
    "wAC": handle_feedWaterAnimalCage,
    "cAC": handle_cleanCuddleAnimalCage,
    "cuAC": handle_cleanCuddleAnimalCage,
    "bdAC": handle_directBreed,
    "bsAC": handle_breedStart,
    "beAC": handle_breedEnd,
    "cEf": handle_collectEntranceFee,
    "cSt": handle_collectStoreMoney,
    "mC": handle_moveCage,
    "mR": handle_moveRoad,
    "cTr": handle_clearTrashRoad,
    "mD": handle_moveDeco,
    "mSt": handle_moveStore,
    "bP": handle_buyPremium,
    "bTb": handle_buyTrashbin,
    "mTb": handle_moveTrashbin,
    "sTb": handle_sellTrashbin,
    "cTb": handle_clearTrashbin,
    "hAC": handle_healAnimalCage,
    "sC": handle_sellCage,
    "sSt": handle_sellStore,
    "sD": handle_sellDeco,
    "sR": handle_sellRoad,
    "sSB": handle_sellSpecial,
    "bSB": handle_buySpecial,
    # instant build
    "bdC": handle_buildInstant,
    "bdD": handle_buildInstant,
    "bdSt": handle_buildInstant,
    # cage care extras
    "shAC": handle_cageCareAction,
    "sfAC": handle_cageCareAction,
    "pfAC": handle_cageCareAction,
    "uc": handle_upgradeCage,
    "uCa": handle_upgradeEventCage,
    # animals (not sent by this client)
    "sAC": handle_sellAnimalCage,
    "mAC": handle_moveAnimalCage,
    "bAInv": handle_buyAnimalToInventory,
    # specials / entrance
    "mSB": handle_moveSpecial,
    "sEb": handle_selectEntranceBuilding,
    # assistants
    "bAs": handle_buyAssistant,
    "uA": handle_useAssistant,
    "cAt": handle_clearAssistantTimer,
    "uAsfA": handle_superFeedAssistant,
    "uApfA": handle_powerFeedAssistant,
    "uAshC": handle_superHealAssistant,
    # breeding lab / nursery
    "bsASB": handle_startAdvancedBreeding,
    "bdASB": handle_useElixir,
    "beASB": handle_endAdvancedBreeding,
    "rsASB": handle_startNurseryBreeding,
    "arASB": handle_useRaisingPotion,
    "reASB": handle_endNurseryBreeding,
    "rdASB": handle_instantNurseryBreeding,
}

def handle_fieldFia(request, user_id, obj, json_data, config_data):
    current_field_id = json_data["uObj"]["current_field"]
    
    fia_type = request["fia"]
    if fia_type in available_field_actions:
        handler = available_field_actions[fia_type]
        handler(request, user_id, obj, json_data, config_data, current_field_id)
    else:
        print(f"field.fia case {fia_type} not handled")
        raise ZooError(NOT_IMPLEMENTED, f"field.fia {fia_type}")