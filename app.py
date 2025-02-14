#######################
# Import server stuff #
#######################
from bundle import TEMPLATES_DIR, STUB_DIR, STYLES_DIR, ASSETS_DIR
from commands import *
import utils.userUtils as userUtils
import utils.attractionUtils as attractionUtils

##########################
# Import 3rd party stuff #
##########################
print(" [+] Importing libraries...")
from flask import Flask, render_template, send_from_directory, request, redirect, session
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
    "swfOpt.set": handle_swfOptSet
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

port = 5050 # doesn't matter on Ploomber (neither does the host url actually xd)

app = Flask(__name__, template_folder=TEMPLATES_DIR)
app.secret_key = 'my-zoomumba-key'

load_dotenv()
# Used for the account emulation panel
auth = HTTPBasicAuth()
@auth.verify_password
def verify_password(username, password):
    # username = account id you want to emulate
    print(password)
    print(os.getenv('STAFF_PASSWORD'))
    if password == os.getenv('STAFF_PASSWORD'):
        print("yes")
        return username

######################
# Connect to MongoDB #
######################
print(" [+] Connecting to database...")

client = MongoClient(os.getenv('MONGO_URI'))
db = client["zoo-dev"]
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
        locale = "en"
    session["locale"] = locale

    action = request.args.get('action')

    if "msg" not in session:
        session["msg"] = ""
    msg = session["msg"]
    session["msg"] = ""

    if action == "externalSignUp":
        return render_template("signup.html", ASSETSIP=request.host_url, SERVERIP=request.host_url, LOCALE=locale, msg=msg)
    else:
        return render_template("home.html", ASSETSIP=request.host_url, SERVERIP=request.host_url, LOCALE=locale, msg=msg, registered=userUtils.get_total_user_count())


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
        msg = "A user with this name already exists"
    if msg != "":
        return render_template("signup.html", ASSETSIP=request.host_url, SERVERIP=request.host_url, LOCALE=locale, msg=msg)
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

    return render_template("play.html", tutS=tutS, tutT=tutT, userid=session["userid"], token=token, SERVERIP=host_url, isHTTPS=int(LOCAL_DEV_MODE == True))

@app.route("/emulate")
@auth.login_required
def emulate():
    user_id = int(auth.current_user())

    json_data = userUtils.get_zoo_from_db_by_userid(data_db, user_id)
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

    return render_template("play.html", tutS=tutS, tutT=tutT, userid=user_id, token=token, SERVERIP=host_url, isHTTPS=int(LOCAL_DEV_MODE == False))

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
    print(request.form["json"])
    total_response = {}
    total_response["callstack"] = [[]]
    obj = {}

    # Load from database
    all_data = userUtils.get_zoo_from_db_by_userid(data_db, int(request.args["uId"]))
    json_data = all_data["zoo"]
    initial_json_data = copy.deepcopy(json_data) # Make a copy so we can compare differences later (probably not very efficient but should do for now)

    # Send secret id
    if "sid" in request.form:
        obj["zoo_sid"] = request.form["sid"]
    else:
        obj["zoo_sid"] = json_data["zoo_sid"]

    # Send server time
    if "sData" not in obj:
        obj["sData"] = {}
    obj["sData"]["time"] = int(time.time())

    # Load config (this probably should be saved in a variable but that's for later xD)
    f = open(os.path.join(p, "data", "global_config_data.json.def"), "r")
    config_data = json.loads(str(f.read()))
    f.close()

    # Check if token is correct
    if session["token"] != all_data["token"] and not LOCAL_DEV_MODE:
        print("Wrong token")
        return
    
    # Add entrance fee for current field
    current_field_id = json_data["uObj"]["current_field"]
    entrance_fee_per_second = attractionUtils.calculate_entrance_fee_per_hour(json_data, config_data, current_field_id) / 3600
    print(f"Entrance fee per second = {entrance_fee_per_second}")
    time_since_last_push = obj["sData"]["time"] - json_data["pfObj"][current_field_id]["lastPush"]
    print(f"Time since last push = {time_since_last_push}")
    entrance_fee_gained = entrance_fee_per_second * time_since_last_push
    print(f"Entrance fee gained = {entrance_fee_gained}")
    json_data["uObj"]["entranceFee"] += round(entrance_fee_gained)
    entrance_fee_limit = attractionUtils.calculate_entrance_fee_limit(json_data)
    print(f"Entrance fee limit = {entrance_fee_limit}")
    if json_data["uObj"]["entranceFee"] > entrance_fee_limit:
        json_data["uObj"]["entranceFee"] = entrance_fee_limit

    # Handle commands
    callstack = json.loads(request.form["json"])["callstack"]
    for i in callstack:
        command = list(i.keys())[0]
        if command in available_commands:
            print("Command " + command + " handled")
            handler = available_commands[command]
            handler(i[command], request.args["uId"], obj, json_data, config_data)
            total_response["callstack"][0].append({"t":1,"v":""})
        else:
            print("Command " + command + " not handled")
    total_response["obj"] = obj

    # Save last push time
    json_data["pfObj"][current_field_id]["lastPush"] = obj["sData"]["time"]
    # Save to database

    added, removed, modified = userUtils.get_differences(initial_json_data, json_data)
    userUtils.save_zoo(data_db, int(request.args["uId"]), added, removed, modified)
    return total_response
    
    
    ########
    # MAIN #
    ########

if __name__ == '__main__':
    print(" [+] Running server...")

    app.secret_key = 'my-zoomumba-key'
    app.run(host=host, port=port, debug=True)
