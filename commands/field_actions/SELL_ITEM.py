from utils import fieldItemUtils as items

# field.fia sC / sSt / sD / sR / sSB: {"id": <uniqueId>}
#
# The client adds the sell price itself for cages, stores, decos and roads
# (PlayFieldManager.sell*) and removes the item from the field before the
# answer arrives; for specials (sSB) it adds nothing. We always send uObj back
# so the server's number wins, and the item with del=1.


def _sell(obj, json_data, config_data, field_id, key, item_id):
    item = items.get_item(json_data, key, field_id, item_id)
    config = items.item_config(config_data, key, item)
    items.check_sellable(config, key)
    virtual, real = items.sell_price(config_data, key, item)

    del items.get_items(json_data, key, field_id)[str(item_id)]
    items.pay_out(json_data, virtual, real)

    items.send_item(obj, key, field_id, items.deleted_copy(item))
    obj["uObj"] = json_data["uObj"]
    return item


def handle_sellCage(request, user_id, obj, json_data, config_data, current_field_id):
    cage = _sell(obj, json_data, config_data, current_field_id, "cages", request["id"])
    # The animals go with the cage (their price is part of the cage's)
    field_animals = items.get_cage_animals(json_data, current_field_id, cage["id"])
    for animal in field_animals.values():
        items.send_animal(obj, current_field_id, cage["id"], items.deleted_copy(animal))
    del json_data["animals"][str(current_field_id)][str(cage["id"])]


def handle_sellStore(request, user_id, obj, json_data, config_data, current_field_id):
    _sell(obj, json_data, config_data, current_field_id, "stores", request["id"])


def handle_sellDeco(request, user_id, obj, json_data, config_data, current_field_id):
    _sell(obj, json_data, config_data, current_field_id, "decos", request["id"])


def handle_sellRoad(request, user_id, obj, json_data, config_data, current_field_id):
    road = _sell(obj, json_data, config_data, current_field_id, "roads", request["id"])
    items.refresh_activity(obj, json_data, config_data, current_field_id, road["x"], road["y"])


def handle_sellSpecial(request, user_id, obj, json_data, config_data, current_field_id):
    _sell(obj, json_data, config_data, current_field_id, "specials", request["id"])
