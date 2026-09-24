#######################
# Import server stuff #
#######################
from bundle import TEMPLATES_DIR, STUB_DIR, STYLES_DIR, ASSETS_DIR
from commands import *
from utils import constantsUtils, configUtils
import utils.zooErrors as zooErrors
import utils.userUtils as userUtils
import utils.attractionUtils as attractionUtils

##########################
# Import 3rd party stuff #
##########################
print(" [+] Importing libraries...")
from flask import Flask, jsonify, render_template, send_from_directory, request, redirect, session
from flask_httpauth import HTTPBasicAuth
import re
import secrets
import time
import bcrypt
from pathlib import Path
import json
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import copy
from urllib.parse import urlparse
import traceback

print(" [+] Loading server...")

###############################
# Setup list of game commands #
###############################

available_commands = {
    "config.getCv": handle_getCv,
    "config.getConfig": handle_getConfig,
    "init.getUser": handle_getUser,
    "swfCookie.set": handle_swfCookieSet,
    "tutorial.rS": handle_tutorialRs,
    "field.fia": handle_fieldFia,
    "gameitems.get": handle_gameitemsGet,
    "swfOpt.set": handle_swfOptSet,
    "managementCenter.get": handle_managementCenterGet,
    "init.sP": handle_switchPlayfield,
    "push.get": handle_pushGet,
    "coupon.redeem": handle_couponRedeem,
    "tombola.bTT": handle_tombolaBuyTicket,
    "mail.gib": handle_mailGetInbox,
    "tombola.rTT": handle_tombolaRedeemTicket
}

#########################
# Load global game data #
#########################
print(" [+] Loading init data...")

p = Path(__file__).parents[0]

load_dotenv()
LOCAL_DEV_MODE = os.getenv("LOCAL_DEV_MODE") == "1"

if LOCAL_DEV_MODE:
    host = "127.0.0.1"
else:
    host = "0.0.0.0"

port = 5050

app = Flask(__name__, template_folder=TEMPLATES_DIR)
app.secret_key = 'my-zoomumba-key'

# Used for the account emulation panel
auth = HTTPBasicAuth()
@auth.verify_password
def verify_password(username, password):
    # username = account id you want to emulate
    if password == os.getenv('STAFF_PASSWORD'):
        return username
    
# Load language files for templates
langstrings = {}
for filename in os.listdir(os.path.join(p, "templates", "languages")):
    with open(os.path.join(p, "templates", "languages", filename), "rb") as f:
        langstrings[filename[0:-5]] = json.loads(f.read())

# Load CVs
constantsUtils.generate_cvs()

# Load the global game config once (it used to be re-read on every API call)
configUtils.get_config()

######################
# Connect to MongoDB #
######################
print(" [+] Connecting to database...")

client = MongoClient(os.getenv('MONGO_URI'))
db_id = "zoo-dev" if LOCAL_DEV_MODE else "zoo"
db = client[db_id]
auth_db = db["zoo-auth"]
data_db = db["zoo-data"]

userUtils.set_total_user_count(auth_db.estimated_document_count())

##########
# ROUTES #
##########
print(" [+] Configuring server routes...")

@app.route('/')
def homepage():
    locale = request.args.get('locale')
    if not locale:
        if "locale" in session:
            locale = session["locale"]
        else:
            locale = "en"
    session["locale"] = locale

    action = request.args.get('action')

    if "msg" not in session:
        session["msg"] = ""
    msg = session["msg"]
    session["msg"] = ""

    if action == "externalSignUp":
        return render_template("signup.html", ASSETSIP=request.host_url, LOCALE=locale, LOCALESTRINGS=langstrings[locale], msg=msg)
    else:
        return render_template("home.html", ASSETSIP=request.host_url, SERVERIP=request.host_url, LOCALE=locale, LOCALESTRINGS=langstrings[locale], msg=msg, registered=userUtils.get_total_user_count())


@app.route('/authenticate', methods=['POST'])
def authenticate():
    msg = ''
    if 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        account_in_db = auth_db.find_one({'username': username})
        if account_in_db and bcrypt.checkpw(password.encode('utf-8'), account_in_db["password"].encode('utf-8')):
            session["username"] = username
            session["userid"] = account_in_db["id"]
            session["token"] = secrets.token_urlsafe(32)
            data_db.update_one({"id": int(account_in_db["id"])}, {"$set": {"token": session["token"]}})
            return redirect("/game")
        else:
            msg = "bgc.error.login_invalidCredentials"
    elif 'username' not in request.form:
        msg = "bgc.error.username_notGiven"
    elif 'password' not in request.form:
        msg = "bgc.error.password_notGiven"
    session["msg"] = msg
    return redirect("/")


@app.route('/register', methods=['POST'])
def register():
    msg = ''
    if not request.args.get('locale'):
        if "locale" in session:
            locale = session["locale"]
        else:
            locale = "en"
    else:
        locale = request.args.get('locale')
    
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    termsAndConditions = request.form['termsAndConditions']
    # Check requirements
    if username == "":
        msg = "bgc.error.username_notGiven"
    elif password == "":
        msg = "bgc.error.password_notGiven"
    elif email == "":
        msg = "bgc.error.email_notGiven"
    elif len(username) < 4:
        msg = "bgc.error.username_isTooShort"
    elif len(username) > 20:
        msg = "bgc.error.username_isTooLong"
    elif not username.isalnum(): # check for non-alphanumeric characters
        msg = "bgc.error.username_containsInvalidCharacters"
    elif len(password) < 4:
        msg = "bgc.error.password_isTooShort"
    elif len(password) > 45:
        msg = "bgc.error.password_isTooLong"
    elif username == password:
        msg = "bgc.error.password_matchesUsername"
    elif re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email) is None:
        msg = "bgc.error.email_invalidAddress"
    elif termsAndConditions == "0":
        msg = "bgc.error.termsAndConditions_notAccepted"
    elif auth_db.find_one({"username": username}):
        msg = "bgc.error.username_alreadyExists"
    # We're accepting multiple accounts with the same email because why not
    if msg != "":
        return render_template("signup.html", ASSETSIP=request.host_url, LOCALE=locale, LOCALESTRINGS=langstrings[locale], msg=msg)
    password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf8')

    highest_id = auth_db.find().sort('id', -1).limit(1) # Find highest id in database (hopefully this doesn't eat performance xd)
    list_highest_id = list(highest_id)
    print(list_highest_id)
    if(len(list_highest_id) == 0):
        # First user
        id = 1
    else:
        id = list_highest_id[0]["id"] + 1
    secret_id = secrets.token_urlsafe(32)
    if auth_db.find_one({"sid": secret_id}): # Useless check but you never know xD
        secret_id = secrets.token_urlsafe(32)
    doc_data = {
        "id": id,
        "sid": secret_id,
        "username": username,
        "password": password,
        "email": email,
        "newsletter": "newsletter" in request.form and request.form["newsletter"] == "1", 
    }
    auth_db.insert_one(doc_data)
    f = open(os.path.join(p, "data", "new_player.json.def"), "r")
    new_player_data = json.loads(str(f.read()))
    f.close()
    new_player_data = userUtils.replace_placeholders(new_player_data, "PLACEHOLDER_USERID", str(id))
    new_player_data = userUtils.replace_placeholders(new_player_data, "01PLACEHOLDER_USERID", "01" + str(id))
    new_player_data = userUtils.replace_placeholders(new_player_data, "PLACEHOLDER_SID", secret_id)
    new_player_data["uObj"]["uName"] = username
    new_player_data["pfObj"]["01" + str(id)]["lastPush"] = int(time.time())
    # NOTE:
    # We handle field ids different than the original game, instead of a random (probably global) number we do
    # fId = fType (with leading 0 if needed) + userid
    # For example: 018299495 for field type 1 with userid 8299495
    token = secrets.token_urlsafe(32)
    session["token"] = token
    session["username"] = username
    session["userid"] = id
    doc_data = {
        "id": id,
        "sid": secret_id,
        "username": username,
        "token": token,
        "zoo": new_player_data
    }
    data_db.insert_one(doc_data)
    userUtils.set_total_user_count(userUtils.get_total_user_count() + 1)
    return redirect("/game")


@app.route("/game")
def gamepage():
    if "userid" not in session:
        return redirect("/")
    
    json_data = userUtils.get_zoo_from_db_by_userid(data_db, session["userid"])
    tutS = json_data["zoo"]["uObj"]["tutS"]
    tutT = json_data["zoo"]["uObj"]["tutT"]
    token = json_data["token"]

    # Quick ducktape fix to remove the http(s):// from the host url (because the flashvars need it like that)
    # There's probably a more efficient way than to check this every time again
    host_name = urlparse(request.host_url).hostname
    host_port = urlparse(request.host_url).port
    if host_port:
        host_url = host_name + ":" + str(host_port)
    else:
        host_url = host_name

    return render_template("play.html", tutS=tutS, tutT=tutT, userid=session["userid"], token=token, SERVERIP=host_url, isHTTPS=int(LOCAL_DEV_MODE == False), DEBUGSWF="-DEBUG" if LOCAL_DEV_MODE else "")

@app.route("/emulate/<user_id>")
@auth.login_required
def emulate(user_id):
    user_id = int(user_id)

    json_data = userUtils.get_zoo_from_db_by_userid(data_db, user_id)
    tutS = json_data["zoo"]["uObj"]["tutS"]
    tutT = json_data["zoo"]["uObj"]["tutT"]
    token = json_data["token"]
    session["token"] = token

    # Quick ducktape fix to remove the http(s):// from the host url (because the flashvars need it like that)
    # There's probably a more efficient way than to check this every time again
    host_name = urlparse(request.host_url).hostname
    host_port = urlparse(request.host_url).port
    if host_port:
        host_url = host_name + ":" + str(host_port)
    else:
        host_url = host_name

    return render_template("play.html", tutS=tutS, tutT=tutT, userid=user_id, token=token, SERVERIP=host_url, isHTTPS=int(LOCAL_DEV_MODE == False))

@app.route("/admin")
@auth.login_required
def admin():
    return render_template("admin.html")

@app.route("/admin-fetch-users", methods=['POST'])
@auth.login_required
def admin_fetch_users():
    data = request.get_json()
    query = str(data["query"]).strip()
    limit = 20
    if "limit" in data:
        limit = int(data["limit"])
        if limit > 20:
            limit = 20

    if not query:
        return jsonify([])

    # Filters
    if query.isdigit():
        filter = {
            "$or": [
                {"id": int(query)},
                {"username": {"$regex": re.escape(query), "$options": "i"}}
            ]
        }
    else:
        filter = {
            "username": {"$regex": re.escape(query), "$options": "i"}
        }

    result = (
        auth_db.find(filter, {"_id": 0, "id": 1, "username": 1}).limit(limit)
    )

    users = list(result)
    return jsonify(users)


@app.route("/crossdomain.xml")
def crossdomain():
    return send_from_directory(STUB_DIR, "crossdomain.xml")

###############
# GAME STATIC #
###############

@app.route("/assets/<path:path>")
def static_assets_loader(path):
    return send_from_directory(ASSETS_DIR, path)
    

@app.route("/templates/styles/<path:path>")
def styles(path):
    return send_from_directory(STYLES_DIR, path)

################
# GAME DYNAMIC #
################


@app.route("/ZooApi.php", methods=['POST'])
def handle_request():
    # Parse the batch: json={"callstack":[{"<service>.<method>": {...params...}}, ...]}
    try:
        callstack = json.loads(request.form["json"])["callstack"]
    except (KeyError, TypeError, ValueError):
        print("ZooApi.php: malformed request")
        return error_response(zooErrors.INVALID_REQUEST)

    # Load the player (the client sends its user id as ?uId=)
    try:
        user_id = request.args["uId"]
        all_data = userUtils.get_zoo_from_db_by_userid(data_db, int(user_id))
    except (KeyError, ValueError):
        all_data = None
    if all_data is None:
        print("ZooApi.php: unknown user")
        return error_response(zooErrors.NOT_AUTH)

    # Check if token is correct. Answering with system.user.notAuth makes the
    # client show its "not authorised" window instead of hanging on an HTTP 500.
    if session.get("token") != all_data["token"] and not LOCAL_DEV_MODE:
        print("Wrong token")
        return error_response(zooErrors.NOT_AUTH)

    json_data = all_data["zoo"]
    initial_json_data = copy.deepcopy(json_data) # Make a copy so we can compare differences later (probably not very efficient but should do for now)
    config_data = configUtils.get_config() # Loaded once, shared between requests

    total_response = {}
    total_response["callstack"] = {}
    obj = {}

    # Send secret id
    if "sid" in request.form:
        obj["zoo_sid"] = request.form["sid"]
    else:
        obj["zoo_sid"] = json_data["zoo_sid"]

    # Send server time
    obj["sData"] = {"time": int(time.time())}

    # Handle commands
    for call in callstack:
        if not isinstance(call, dict) or len(call) == 0:
            continue
        command = next(iter(call))
        params = call[command]
        req_id = params.get("req:") if isinstance(params, dict) else None

        handler = available_commands.get(command)
        if handler is None:
            print("Command " + command + " not handled (stub)")
            handler = get_stub_handler(command)
        else:
            print("Command " + command + " handled")

        # t = 0 means error (1 = no error), v = message code (see utils/zooErrors.py)
        status = {"t": 1, "v": ""}
        data_snapshot = copy.deepcopy(json_data)
        obj_snapshot = copy.deepcopy(obj)
        try:
            handler(params, user_id, obj, json_data, config_data)
        except Exception as e:
            if isinstance(e, zooErrors.ZooError):
                print(f"Command {command} failed: {e.code} ({e})")
                code, resync = e.code, e.resync
            else:
                print(f"Command {command} crashed:")
                traceback.print_exc()
                code, resync = zooErrors.INTERNAL, ("uObj",)

            # Roll back whatever the handler changed before it failed
            json_data.clear()
            json_data.update(data_snapshot)
            obj.clear()
            obj.update(obj_snapshot)

            # Re-send authoritative state so the client drops optimistic changes
            for key in resync:
                if key in json_data:
                    obj[key] = json_data[key]
            status = {"t": 0, "v": code}

        if req_id is not None:
            total_response["callstack"].setdefault(str(req_id), []).append(status)

    # Remove level-up from last time if needed
    json_data["uObj"]["lvlUp"] = None

    # Calculate level based on xp, show level up message if needed
    old_level = json_data["uObj"]["uLvl"]
    new_level = userUtils.calculate_level_based_on_xp(json_data["uObj"]["uEp"], config_data)

    if old_level != new_level:
        # Give rewards
        if new_level <= 10:
            json_data["uObj"]["uCv"] += (250 + new_level * 250)
        else:
            json_data["uObj"]["uCr"] += 3
        json_data["uObj"]["uLvl"] = new_level
        json_data["uObj"]["lvlUp"] = 1 # Show level-up popup
        obj["uObj"] = json_data["uObj"]

    total_response["obj"] = obj

    # Save to database
    added, removed, modified = userUtils.get_differences(initial_json_data, json_data)
    userUtils.save_zoo(data_db, int(user_id), added, removed, modified)
    return total_response


def error_response(code):
    """A response that fails the whole batch with one status code."""
    return {"callstack": {"0": [{"t": 0, "v": code}]}, "obj": {}}

    ########
    # MAIN #
    ########

if __name__ == '__main__':
    print(" [+] Running server...")

    app.secret_key = 'my-zoomumba-key'
    app.run(host=host, port=port, debug=True)
