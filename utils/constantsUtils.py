from pathlib import Path
import os
import json
import copy

empty_cage = {"id":-1,"uId":0,"fId":0,"cId":1,"sId":0,"act":0,"level":1,"x":34,"y":84,"r":0,"male":0,"female":0,"child":0,"build":1605824682,"breed":0,"clean":0,"feed":0,"water":0,"cuddle":0,"sick":0,"health":0,"sfeed":0,"eventId":0,"evEnd":0,"drops":{"cu":{"col":0,"eItem":0,"eCol":0},"cl":{"col":{"id":244,"amount":1},"eItem":0,"eCol":0},"wa":{"col":0,"eItem":0,"eCol":0},"fe":{"col":0,"pp":2,"pl":0,"eItem":0,"eCol":0},"sf":{"col":0,"pp":2,"pl":0,"eItem":0},"pf":{"col":0,"pp":2,"pl":0,"eItem":0},"hl":{"pp":2,"pl":0},"sh":{"pp":3,"pl":0},"eb":{"pp":2,"pl":0},"db":{"pp":2,"pl":0}}}
empty_animal = {"id":-1,"uId":0,"aId":0,"sId":0,"cId":0,"fId":0,"fTime":0,"act":0}
empty_road = {"id": -1,"uId": 0,"fId": 0,"rId": 6,"act": 0,"x": 24,"y": 72,"r": 0,"deco": 0,"trashbin": 6341202}
empty_deco = {"id": -1,"uId": 0,"fId": 0,"dId": 76,"act": 0,"x": 37,"y": 82,"r": 0,"build": 1315636007}
empty_store = {"id": -1,"uId": 0,"fId": 0,"stId": 1,"act": 0,"x": 32,"y": 86,"r": 0,"build": 1313749616,"collect": 1387812591,"fTime": 1387796606}
empty_powerup = {"id": -1,"uId": 0,"pId": 0, "inUse": 0, "lastActivated": 0, "endTime": 0}

# Tombola
TOMBOLA_TICKET_PRICE = 2  # hardcoded because so does the client
TOMBOLA_WEIGHTS = [1, 49, 49, 28, 1, 49, 49, 28]

# Translations
LANGUAGES = ["bg", "br", "cs", "da", "de", "el", "en", "es", "fi", "fr", "hu", "it", "nl", "no", "pl", "pt", "ro", "ru", "sk", "sv", "tr"]
CVS = {}

# Resources
PET_PAWS, PEARLS = 3, 4
WATER, MEDICINE, SUPERFOOD, SUPERMEDICINE, POWERFOOD = 1, 7, 8, 9, 10
OCEAN_SUPERFOOD, OCEAN_POWERFOOD = 21, 22

# Super and power feed only once food bar is below this threshold (MainConfig.PERCENTAGE_FOR_SUPER_ACTIONS)
SUPER_ACTION_THRESHOLD = 0.8

# Field types
OCEAN_FIELD_TYPE = 6


def get_cv(lang):
    if lang in CVS:
        return CVS[lang]
    else:
        return CVS["en"] # Fallback to english, just in case

def generate_cvs():
    # To-do later: actually generate the hashes
    p = Path(__file__).parents[1]
    f = open(os.path.join(p, "data", "cvs.json.def"), "r")
    cv_str = f.read()
    for lang in LANGUAGES:
        CVS[lang] = json.loads(cv_str.replace("{PLACEHOLDER_LANG}", lang))

def get_empty_cage():
    return copy.deepcopy(empty_cage)

def get_empty_animal():
    return copy.deepcopy(empty_animal)

def get_empty_road():
    return copy.deepcopy(empty_road)

def get_empty_deco():
    return copy.deepcopy(empty_deco)

def get_empty_store():
    return copy.deepcopy(empty_store)

def get_empty_powerup():
    return copy.deepcopy(empty_powerup)