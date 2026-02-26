from flask import session
from utils import constantsUtils

def handle_getCv(request, user_id, obj, json_data, config_data):
    obj["cv"] = constantsUtils.get_cv(session["locale"])