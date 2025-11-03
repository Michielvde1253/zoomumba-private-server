empty_cage = {"id":-1,"uId":0,"fId":0,"cId":1,"sId":0,"act":0,"level":1,"x":34,"y":84,"r":0,"male":0,"female":0,"child":0,"build":1605824682,"breed":0,"clean":0,"feed":0,"water":0,"cuddle":0,"sick":0,"health":0,"sfeed":0,"eventId":0,"evEnd":0,"drops":{"cu":{"col":0,"eItem":0,"eCol":0},"cl":{"col":{"id":244,"amount":1},"eItem":0,"eCol":0},"wa":{"col":0,"eItem":0,"eCol":0},"fe":{"col":0,"pp":2,"pl":0,"eItem":0,"eCol":0},"sf":{"col":0,"pp":2,"pl":0,"eItem":0},"pf":{"col":0,"pp":2,"pl":0,"eItem":0},"hl":{"pp":2,"pl":0},"sh":{"pp":3,"pl":0},"eb":{"pp":2,"pl":0},"db":{"pp":2,"pl":0}}}
empty_animal = {"id":-1,"uId":0,"aId":0,"sId":0,"cId":0,"fId":0,"fTime":0,"act":0}
empty_road = {"id": -1,"uId": 0,"fId": 0,"rId": 6,"act": 0,"x": 24,"y": 72,"r": 0,"deco": 0,"trashbin": 6341202}
empty_deco = {"id": -1,"uId": 0,"fId": 0,"dId": 76,"act": 0,"x": 37,"y": 82,"r": 0,"build": 1315636007}
empty_store = {"id": -1,"uId": 0,"fId": 0,"stId": 1,"act": 0,"x": 32,"y": 86,"r": 0,"build": 1313749616,"collect": 1387812591,"fTime": 1387796606}


def get_empty_cage():
    return empty_cage.copy()

def get_empty_animal():
    return empty_animal.copy()

def get_empty_road():
    return empty_road.copy()

def get_empty_deco():
    return empty_deco.copy()

def get_empty_store():
    return empty_store.copy()