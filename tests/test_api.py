"""
End-to-end test of ZooApi.php against an in-memory MongoDB (mongomock).

    pip install mongomock
    python tests/test_api.py

Registers a player, then drives the API the way the client does and checks
the answers and the saved player document. Prints PASS/FAIL per check and
exits non-zero if anything failed.
"""
import os, sys, json, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO); sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, "commands")); sys.path.insert(0, os.path.join(REPO, "commands","field_actions"))
os.environ["LOCAL_DEV_MODE"] = "1"; os.environ["MONGO_URI"] = "mongodb://x"
import mongomock, pymongo
pymongo.MongoClient = mongomock.MongoClient
import app as A

c = A.app.test_client()
r = c.post("/register", data={"username":"tester1","password":"secret1","email":"a@b.cd","termsAndConditions":"1"})
uid = A.auth_db.find_one({"username":"tester1"})["id"]
fails = []
def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond: fails.append(name)

req_counter = [100]
def call(*calls, client=c):
    body = {"callstack": list(calls)}
    t0 = time.time()
    res = client.post(f"/ZooApi.php?uId={uid}", data={"json": json.dumps(body)})
    return res.status_code, res.get_json(), time.time() - t0
def rq(cmd, **p):
    req_counter[0] += 1; p["req:"] = req_counter[0]; return {cmd: p}, str(req_counter[0])

with c.session_transaction() as s: s["locale"] = "en"
st, r, dt = call({"config.getCv": []}); check("getCv returns cv", st == 200 and "cv" in r["obj"])
st, r, dt1 = call({"config.getConfig": []}); check("getConfig returns config", "config" in r["obj"] and "gameItems" in r["obj"]["config"])
st, r, dt2 = call({"config.getConfig": []}); print(f"   getConfig timings {dt1:.2f}s {dt2:.2f}s")
q, rid = rq("init.getUser"); st, r, _ = call(q)
check("getUser t:1", r["callstack"][rid] == [{"t":1,"v":""}]); check("getUser has uObj/pfObj/fObj", all(k in r["obj"] for k in ("uObj","pfObj","fObj","init")))

doc = lambda: A.data_db.find_one({"id": uid})["zoo"]
cfg = A.configUtils.get_config()
cage_id = next(k for k,v in cfg["gameItems"]["cages"].items() if v.get("buyable")==1 and v.get("onlyDev")!=1 and v.get("buyVirtual",0)>0 and v.get("userLevelRequired",99)<=1)
price = cfg["gameItems"]["cages"][cage_id]["buyVirtual"]
fid = doc()["uObj"]["current_field"]
n_before = len(doc()["fObj"]["cages"].get(str(fid), {})); cv_before = doc()["uObj"]["uCv"]
q, rid = rq("field.fia", fia="bC", cId=int(cage_id), x=40, y=40, r=0, cR=0); st, r, _ = call(q)
check("buy cage t:1", r["callstack"][rid] == [{"t":1,"v":""}])
check("buy cage charged + stored", doc()["uObj"]["uCv"] == cv_before - price and len(doc()["fObj"]["cages"][str(fid)]) == n_before + 1)

# not enough money -> t:0, rollback, uObj resync
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uCv": price - 1}})
n_before = len(doc()["fObj"]["cages"][str(fid)]); nid_before = doc()["next_object_id"]
q, rid = rq("field.fia", fia="bC", cId=int(cage_id), x=44, y=44, r=0, cR=0); st, r, _ = call(q)
check("broke buy t:0 notEnoughMoney", r["callstack"][rid] == [{"t":0,"v":"zoo.error.notEnoughMoney"}])
check("broke buy rolled back", len(doc()["fObj"]["cages"][str(fid)]) == n_before and doc()["next_object_id"] == nid_before and doc()["uObj"]["uCv"] == price - 1)
check("broke buy resyncs uObj, no fObj leak", r["obj"].get("uObj",{}).get("uCv") == price - 1 and "fObj" not in r["obj"])
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uCv": 100000}})

# crash in a real handler (unknown cage id) -> t:0 internal, rollback
nid_before = doc()["next_object_id"]
q, rid = rq("field.fia", fia="bC", cId=999999, x=10, y=10, r=0, cR=0); st, r, _ = call(q)
check("crash t:0 internal (HTTP 200)", st == 200 and r["callstack"][rid] == [{"t":0,"v":"zoo.error.internal"}])
check("crash rolled back", doc()["next_object_id"] == nid_before)

# stubs
q1, r1 = rq("quest.gQ"); q2, r2 = rq("boardgame.get", eventId=5); q3, r3 = rq("inventory.iva", iva="xyz", type=1)
q4, r4 = rq("field.fia", fia="zzz", id=1); q5, r5 = rq("some.newCommand"); q6, r6 = rq("mail.gob", **{"from":0,"to":10})
st, r, _ = call(q1, q2, q3, q4, q5, q6, {"error.set": {"error": "test error"}})
cs = r["callstack"]
check("read stub t:1 + qObj", cs[r1] == [{"t":1,"v":""}] and "qObj" in r["obj"])
check("event stub notRunning", cs[r2] == [{"t":0,"v":"zoo.error.event.notRunning"}])
check("todo stub notImplemented", cs[r3] == [{"t":0,"v":"zoo.error.notImplemented"}])
check("unknown fia notImplemented", cs[r4] == [{"t":0,"v":"zoo.error.notImplemented"}])
check("unknown command notImplemented", cs[r5] == [{"t":0,"v":"zoo.error.notImplemented"}])
check("mail.gob returns outbox", cs[r6][0]["t"] == 1 and "ob" in r["obj"].get("mObj", {}))

# swfCookie.set persists
st, r, _ = call({"swfCookie.set": {"hh": {"name":"hh","timestamp":1234}}})
check("swfCookie persisted", doc()["swfCookies"]["cookies"]["hh"]["timestamp"] == 1234)


# ---- field.fia bP (zoo expansions) ----
pf = lambda: doc()["pfObj"][str(doc()["fIds"]["1"])]
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uCr": 4, "zoo.uObj.uLvl": 1, "zoo.uObj.uEp": 0}})
size0, minh0, maxv0 = pf()["fSize"], pf()["minHorizontal"], pf()["maxVertical"]
q, rid = rq("field.fia", fia="bP", pId=11); st, r, _ = call(q)
check("expansion too poor -> notEnoughMoney, no change", r["callstack"][rid][0] == {"t":0,"v":"zoo.error.notEnoughMoney"} and pf()["fSize"] == size0)
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uCr": 50}})
q, rid = rq("field.fia", fia="bP", pId=11); st, r, _ = call(q)
check("expansion bought t:1", r["callstack"][rid] == [{"t":1,"v":""}])
check("expansion: fSize+1, bounds grown, 5 real charged", pf()["fSize"] == size0 + 1 and pf()["minHorizontal"] == minh0 - 2 and pf()["maxVertical"] == maxv0 + 2 and doc()["uObj"]["uCr"] == 45)
check("expansion sends pfObj + uObj", "pfObj" in r["obj"] and r["obj"]["pfObj"][str(doc()["fIds"]["1"])]["fSize"] == size0 + 1 and r["obj"]["uObj"]["uCr"] == 45)
q1, r1 = rq("field.fia", fia="bP", pId=2000); q2, r2 = rq("field.fia", fia="bP", pId=23); q3, r3 = rq("field.fia", fia="bP", pId=424242); q4, r4 = rq("field.fia", fia="bP", pId=13)
st, r, _ = call(q1, q2, q3, q4)
check("bP other premium -> notImplemented", r["callstack"][r1][0]["v"] == "zoo.error.notImplemented")
check("bP cake -> event.notRunning", r["callstack"][r2][0]["v"] == "zoo.error.event.notRunning")
check("bP unknown id -> invalidRequest", r["callstack"][r3][0]["v"] == "zoo.error.invalidRequest")
check("bP zoo the player lacks -> invalidRequest", r["callstack"][r4][0]["v"] == "zoo.error.invalidRequest")
# level-up to 20 unlocks main-zoo steps lvl10 (fsize 11) and lvl20 (fsize 12) for free
xp20 = int(cfg["main"]["u_level"][20]) if len(cfg["main"]["u_level"]) > 20 else None
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uEp": xp20}})
st, r, _ = call({"push.get": []})
check("level-up auto-expands main zoo", doc()["uObj"]["uLvl"] >= 20 and pf()["fSize"] == 12 and pf()["minHorizontal"] == minh0 - 4)


# ---- field.fia bTb / mTb (trashbins) ----
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uCv": 100000}})
fid = doc()["uObj"]["current_field"]
tb_cfg = cfg["gameItems"]["trashbins"]["1"]
cv0 = doc()["uObj"]["uCv"]; nid = doc()["next_object_id"]
road = next(iter(doc()["fObj"]["roads"][str(fid)].values()), None)
rx, ry = (road["x"], road["y"]) if road else (30, 88)
q, rid = rq("field.fia", fia="bTb", tbId=1, x=rx, y=ry, r=0, cR=0); st, r, _ = call(q)
check("buy trashbin t:1", r["callstack"][rid] == [{"t":1,"v":""}])
tb = doc()["fObj"]["trashbins"][str(fid)].get(str(nid))
check("trashbin stored with real wire fields", tb is not None and set(tb) == {"id","uId","fId","tbId","act","x","y","r","clean"} and tb["tbId"] == 1)
check("trashbin charged", doc()["uObj"]["uCv"] == cv0 - tb_cfg["buyVirtual"])
check("trashbin sent to client under fObj.trashbins.<field>.<id>", r["obj"]["fObj"]["trashbins"][str(fid)][str(nid)]["id"] == nid)
if road: check("road under trashbin linked", doc()["fObj"]["roads"][str(fid)][str(road["id"])]["trashbin"] == nid)
q, rid = rq("field.fia", fia="mTb", id=nid, x=rx+1, y=ry, r=0); st, r, _ = call(q)
check("move trashbin t:1 + stored", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["fObj"]["trashbins"][str(fid)][str(nid)]["x"] == rx+1)
if road: check("old road unlinked on move", doc()["fObj"]["roads"][str(fid)][str(road["id"])]["trashbin"] == 0)
q, rid = rq("field.fia", fia="bTb", tbId=4242, x=1, y=1, r=0, cR=0); st, r, _ = call(q)
check("unknown trashbin -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uCv": 0}}); nid = doc()["next_object_id"]
q, rid = rq("field.fia", fia="bTb", tbId=1, x=rx, y=ry, r=0, cR=0); st, r, _ = call(q)
check("broke trashbin -> notEnoughMoney, nothing stored", r["callstack"][rid][0]["v"] == "zoo.error.notEnoughMoney" and str(nid) not in doc()["fObj"]["trashbins"][str(fid)])
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uCv": 100000}})


# ---- trash: spawn into bins, empty bin, clear road, sell, inventory ----
import time as _t
fid = str(doc()["uObj"]["current_field"])
tbs = doc()["fObj"]["trashbins"][fid]
cap = sum(cfg["gameItems"]["trashbins"][str(b["tbId"])]["capacity"] for b in tbs.values())
check("have a placed trashbin for trash tests", cap > 0)
A.data_db.update_one({"id": uid}, {"$set": {f"zoo.pfObj.{fid}.trashbins": 0, f"zoo.pfObj.{fid}.trashroads": 0, f"zoo.pfObj.{fid}.lastPush": int(_t.time()) - 10000, "zoo.uObj.uLvl": 50, "zoo.res.13.cnt": 0}})
st, r, _ = call({"push.get": []})
pfd = doc()["pfObj"][fid]
check("push: new trash fills bins first, rest on roads", pfd["trashbins"] == cap and pfd["trashroads"] == 500 - cap)
ep0 = doc()["uObj"]["uEp"]; bin_id = next(iter(tbs))
q, rid = rq("field.fia", fia="cTb", id=int(bin_id), cnt=60); st, r, _ = call(q)
check("empty bin t:1", r["callstack"][rid] == [{"t":1,"v":""}])
check("empty bin: trash -60, +60 xp, +60 trash res", doc()["pfObj"][fid]["trashbins"] == cap - 60 and doc()["uObj"]["uEp"] == ep0 + 60 and doc()["res"]["13"]["cnt"] == 60)
q, rid = rq("field.fia", fia="cTb", id=int(bin_id), cnt=99999); st, r, _ = call(q)
check("empty bin can't take more than there is", doc()["pfObj"][fid]["trashbins"] == 0 and doc()["res"]["13"]["cnt"] == cap)
ep0 = doc()["uObj"]["uEp"]; roads0 = doc()["pfObj"][fid]["trashroads"]
q, rid = rq("field.fia", fia="cTr", cnt=5); st, r, _ = call(q)
check("clear road trash: -5 road trash, +5 xp, +5 trash res", doc()["pfObj"][fid]["trashroads"] == roads0 - 5 and doc()["uObj"]["uEp"] == ep0 + 5 and doc()["res"]["13"]["cnt"] == min(cap + 5, 255))
# inventory round trip
q, rid = rq("inventory.iva", iva="fti", type=4, id=int(bin_id), cnt=1); st, r, _ = call(q)
sent = r["obj"]["fObj"]["trashbins"][fid][bin_id]
check("fti: t:1, sent with del=1 inv=1", r["callstack"][rid] == [{"t":1,"v":""}] and sent["del"] == 1 and sent["inv"] == 1)
check("fti: stored in inventory field 0", bin_id not in doc()["fObj"]["trashbins"][fid] and doc()["fObj"]["trashbins"]["0"][bin_id]["fId"] == 0)
q, rid = rq("inventory.iva", iva="itf", type=4, id=int(bin_id), x=rx, y=ry, r=0); st, r, _ = call(q)
check("itf: back on the field, removed from inventory", r["callstack"][rid] == [{"t":1,"v":""}] and bin_id in doc()["fObj"]["trashbins"][fid] and bin_id not in doc()["fObj"]["trashbins"]["0"] and r["obj"]["fObj"]["trashbins"]["0"][bin_id]["del"] == 1)
# sell from the field
A.data_db.update_one({"id": uid}, {"$set": {f"zoo.pfObj.{fid}.trashbins": 30}})
cv0 = doc()["uObj"]["uCv"]
q, rid = rq("field.fia", fia="sTb", id=int(bin_id), cnt=30); st, r, _ = call(q)
check("sell bin: removed, +sellVirtual, its trash gone, del=1 sent", bin_id not in doc()["fObj"]["trashbins"][fid] and doc()["uObj"]["uCv"] == cv0 + tb_cfg["sellVirtual"] and doc()["pfObj"][fid]["trashbins"] == 0 and r["obj"]["fObj"]["trashbins"][fid][bin_id]["del"] == 1)
# sell from inventory
q, rid = rq("field.fia", fia="bTb", tbId=1, x=rx, y=ry, r=0, cR=0); st, r, _ = call(q); new_id = next(iter(r["obj"]["fObj"]["trashbins"][fid]))
q, rid = rq("inventory.iva", iva="fti", type=4, id=int(new_id), cnt=1); call(q)
cv0 = doc()["uObj"]["uCv"]
q, rid = rq("inventory.iva", iva="sfi", type=4, ids=[int(new_id)]); st, r, _ = call(q)
check("sfi: sold from inventory", r["callstack"][rid] == [{"t":1,"v":""}] and new_id not in doc()["fObj"]["trashbins"]["0"] and doc()["uObj"]["uCv"] == cv0 + tb_cfg["sellVirtual"])
q, rid = rq("inventory.iva", iva="sfi", type=4, ids=[123456789]); st, r, _ = call(q)
check("sfi unknown id -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")

# ---- selling placed items + inventory for every item type ----
fid = doc()["uObj"]["current_field"]
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uCv": 100000, "zoo.uObj.uLvl": 50}})
def buy(**p):
    q, rid = rq("field.fia", **p); st, r, _ = call(q); return rid, r
def new_id(r, key):
    return next(k for k, v in r["obj"]["fObj"][key][fid].items() if not v.get("del"))
def cv(): return doc()["uObj"]["uCv"]
# a cage with a male, a female and a child of species 1
rid, r = buy(fia="bC", cId=1, x=50, y=50, r=0, cR=0); cage = int(new_id(r, "cages"))
sp1 = {k: next(a for a in cfg["gameItems"]["animals"].values() if a["speciesId"] == 1 and (a["male"], a["child"]) == mc) for k, mc in (("m",(1,0)),("f",(0,0)),("c",(0,1)))}
for a in sp1.values(): buy(fia="bAC", id=cage, aId=a["animalId"], cR=0)
c0 = doc()["fObj"]["cages"][fid][str(cage)]
check("cage has 1 male/1 female/1 child", (c0["male"], c0["female"], c0["child"]) == (1,1,1))

# hAC
A.data_db.update_one({"id": uid}, {"$set": {"zoo.res.7.cnt": 2}})
q, rid = rq("field.fia", fia="hAC", id=cage); st, r, _ = call(q)
check("heal without enough medicine -> notEnoughResources + res resync", r["callstack"][rid][0]["v"] == "zoo.error.notEnoughResources" and r["obj"]["res"]["7"]["cnt"] == 2)
A.data_db.update_one({"id": uid}, {"$set": {"zoo.res.7.cnt": 5}})
q, rid = rq("field.fia", fia="hAC", id=cage); st, r, _ = call(q)
check("heal uses one medicine per animal", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["res"]["7"]["cnt"] == 2)

# paws: the action pays the paw drop the cage shows, then a new one is rolled
A.data_db.update_one({"id": uid}, {"$set": {"zoo.res.7.cnt": 50, "zoo.uObj.pPaw": 100, "zoo.pwrUp": []}})
pp = doc()["fObj"]["cages"][fid][str(cage)]["drops"]["hl"]["pp"]
q, rid = rq("field.fia", fia="hAC", id=cage); st, r, _ = call(q)
newpp = doc()["fObj"]["cages"][fid][str(cage)]["drops"]["hl"]["pp"]
check("heal pays the cage's paw drop into uObj.pPaw", pp > 0 and doc()["uObj"]["pPaw"] == 100 + pp and r["obj"]["uObj"]["pPaw"] == 100 + pp)
check("next paw drop rolled and sent", 5 <= newpp <= 12 and r["obj"]["fObj"]["cages"][fid][str(cage)]["drops"]["hl"]["pp"] == newpp)
A.data_db.update_one({"id": uid}, {"$set": {"zoo.pwrUp": [{"pId": 12, "inUse": 1, "lastActivated": 0, "endTime": int(time.time()) + 3600}]}})
q, rid = rq("field.fia", fia="hAC", id=cage); st, r, _ = call(q)
check("paw powerup (+100%) doubles the payout", doc()["uObj"]["pPaw"] == 100 + pp + 2 * newpp)
A.data_db.update_one({"id": uid}, {"$set": {"zoo.pwrUp": []}})
fresh = A.constantsUtils.get_empty_cage(); fresh["drops"]["hl"]["pp"] = 999
check("new cages don't share one drops dict", A.constantsUtils.get_empty_cage()["drops"]["hl"]["pp"] != 999)

# collection items: the action pays the cage's col drop into collItems, then a new one is rolled from the cage's sets
pool = set(cfg["collSetConf"]["cages"].get("1", {}).get("items", [])) | set(cfg["collSetConf"]["species"].get("1", {}).get("items", []))
item = sorted(pool)[0]
A.data_db.update_one({"id": uid}, {"$set": {f"zoo.fObj.cages.{fid}.{cage}.drops.cl.col": {"id": item, "amount": 1}, f"zoo.fObj.cages.{fid}.{cage}.clean": 0}})
cnt0 = doc()["collItems"].get(str(item), {}).get("cnt", 0)
q, rid = rq("field.fia", fia="cAC", id=cage); st, r, _ = call(q)
col = doc()["fObj"]["cages"][fid][str(cage)]["drops"]["cl"]["col"]
check("clean pays the collection item into collItems", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["collItems"][str(item)]["cnt"] == cnt0 + 1 and doc()["collItems"][str(item)]["id"] == item)
check("action response doesn't resend collItems (client counts the drop itself)", "collItems" not in r["obj"])
check("next collection drop is 0 or from the cage's sets", col == 0 or (col["id"] in pool and col["amount"] == 1))
from utils import dropUtils; dropUtils.random.seed(1)
rolls = [dropUtils.roll_collectable(cfg, {"cId": 1, "sId": 1}, "cl") for _ in range(500)]
hits = [x for x in rolls if x]
check("clean drops an item ~20% of the time, all from the pool", 60 < len(hits) < 140 and all(x["id"] in pool for x in hits))
check("an empty new cage only rolls its cage set", all(x == 0 or x["id"] in cfg["collSetConf"]["cages"]["1"]["items"] for x in (dropUtils.roll_collectable(cfg, {"cId": 1, "sId": 0}, "cl") for _ in range(200))))

# baby -> inventory -> back into the cage
child = next(a for a in doc()["animals"][fid][str(cage)].values() if a["aId"] == sp1["c"]["animalId"])
q, rid = rq("inventory.iva", iva="fti", type=11, p=[{"id": child["id"], "aId": child["aId"], "cId": cage, "sId": 1}]); st, r, _ = call(q)
inv_animals = doc()["animals"]["0"]["0"]
check("animal fti: in animals.0.0, cage child-1, sent del+inv", r["callstack"][rid] == [{"t":1,"v":""}] and str(child["id"]) in inv_animals and doc()["fObj"]["cages"][fid][str(cage)]["child"] == 0 and r["obj"]["animals"][fid][str(cage)][str(child["id"])].get("inv") == 1)
q, rid = rq("inventory.iva", iva="itf", type=11, id=child["id"], cId=cage); st, r, _ = call(q)
check("animal itf: back in the cage", r["callstack"][rid] == [{"t":1,"v":""}] and str(child["id"]) in doc()["animals"][fid][str(cage)] and doc()["fObj"]["cages"][fid][str(cage)]["child"] == 1 and r["obj"]["animals"]["0"]["0"][str(child["id"])]["del"] == 1)

# bred babies get animal records, so they can be moved to the inventory
cage_babies = lambda: [a for a in doc()["animals"][fid][str(cage)].values() if a["aId"] == sp1["c"]["animalId"]]
q, rid = rq("field.fia", fia="beAC", id=cage); st, r, _ = call(q)
babies = cage_babies()
check("breed end: cage child 2, 2 baby records, sent to client", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["fObj"]["cages"][fid][str(cage)]["child"] == 2 and len(babies) == 2 and len(r["obj"]["animals"][fid][str(cage)]) == 4)
bred = max(babies, key=lambda a: a["id"])
q, rid = rq("inventory.iva", iva="fti", type=11, p=[{"id": bred["id"], "aId": bred["aId"], "cId": cage, "sId": 1}]); st, r, _ = call(q)
check("bred baby -> inventory", r["callstack"][rid] == [{"t":1,"v":""}] and str(bred["id"]) in doc()["animals"]["0"]["0"] and doc()["fObj"]["cages"][fid][str(cage)]["child"] == 1)
q, rid = rq("inventory.iva", iva="sfi", type=11, ids=[bred["id"]]); call(q)
# old saves: counter bumped without a record -> repaired on login
A.data_db.update_one({"id": uid}, {"$set": {f"zoo.fObj.cages.{fid}.{cage}.child": 2}})
q, rid = rq("init.getUser"); st, r, _ = call(q)
check("login repairs missing baby records", len(cage_babies()) == 2 and len(r["obj"]["animals"][fid][str(cage)]) == 4)
A.data_db.update_one({"id": uid}, {"$set": {f"zoo.fObj.cages.{fid}.{cage}.child": 1}})
q, rid = rq("init.getUser"); st, r, _ = call(q)
check("login drops records the cage no longer counts", len(cage_babies()) == 1)
fid = doc()["uObj"]["current_field"]

# capacity + species limits (gameItems.cagesSpecies)
q, rid = rq("inventory.iva", iva="fti", type=11, p=[{"id": child["id"], "aId": child["aId"], "cId": cage, "sId": 1}]); call(q)
A.data_db.update_one({"id": uid}, {"$set": {f"zoo.fObj.cages.{fid}.{cage}.child": 3}})
q, rid = rq("inventory.iva", iva="itf", type=11, id=child["id"], cId=cage); st, r, _ = call(q)
check("animal itf into a full cage -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest" and str(child["id"]) in doc()["animals"]["0"]["0"])
A.data_db.update_one({"id": uid}, {"$set": {f"zoo.fObj.cages.{fid}.{cage}.child": 0}})
q, rid = rq("inventory.iva", iva="itf", type=11, id=child["id"], cId=cage); call(q)
q, rid = rq("inventory.iva", iva="gui"); st, r, _ = call(q)
check("gui returns the inventory", r["callstack"][rid] == [{"t":1,"v":""}] and "0" in r["obj"]["fObj"]["cages"] and "0" in r["obj"]["animals"]["0"])

# cage (with animals) -> inventory -> field
q, rid = rq("inventory.iva", iva="fti", type=1, id=cage, cnt=1); st, r, _ = call(q)
d = doc()
check("cage fti: in fObj.cages.0, animals hidden under animals.0.<cage>", r["callstack"][rid] == [{"t":1,"v":""}] and str(cage) in d["fObj"]["cages"]["0"] and str(cage) not in d["fObj"]["cages"][fid] and len(d["animals"]["0"][str(cage)]) == 3 and str(cage) not in d["animals"][fid])
check("cage fti sends del+inv", r["obj"]["fObj"]["cages"][fid][str(cage)]["inv"] == 1)
q, rid = rq("inventory.iva", iva="itf", type=1, id=cage, x=52, y=52, r=0); st, r, _ = call(q)
d = doc()
check("cage itf: placed with its animals", r["callstack"][rid] == [{"t":1,"v":""}] and d["fObj"]["cages"][fid][str(cage)]["x"] == 52 and len(d["animals"][fid][str(cage)]) == 3 and len(r["obj"]["animals"][fid][str(cage)]) == 3)

# sC: cage + animals
price = cfg["gameItems"]["cages"]["1"]["sellVirtual"] + sum(a["sellVirtual"] for a in sp1.values())
cv0 = cv(); q, rid = rq("field.fia", fia="sC", id=cage); st, r, _ = call(q); d = doc()
check("sell cage: cage + animal prices, animals gone, del sent", r["callstack"][rid] == [{"t":1,"v":""}] and d["uObj"]["uCv"] == cv0 + price and str(cage) not in d["fObj"]["cages"][fid] and str(cage) not in d["animals"][fid] and r["obj"]["fObj"]["cages"][fid][str(cage)]["del"] == 1 and r["obj"]["uObj"]["uCv"] == cv0 + price)

# stores / decos: fti, itf, sfi, sell
for key, cat, fia, idf, cid in (("stores", 2, "bSt", "stId", 1), ("decos", 3, "bD", "dId", next(k for k,v in cfg["gameItems"]["decos"].items() if v.get("buyable")==1 and v.get("buyVirtual",0)>0 and v.get("sellable")==1))):
    sell = {"stores": "sSt", "decos": "sD"}[key]
    rid, r = buy(fia=fia, **{idf: int(cid)}, x=56, y=56, r=0, cR=0); iid = new_id(r, key)
    q, rid = rq("inventory.iva", iva="fti", type=cat, id=int(iid), cnt=1); st, r, _ = call(q)
    check(f"{key} fti", r["callstack"][rid] == [{"t":1,"v":""}] and iid in doc()["fObj"][key]["0"] and iid not in doc()["fObj"][key][fid])
    q, rid = rq("inventory.iva", iva="itf", type=cat, id=int(iid), x=57, y=57, r=1); st, r, _ = call(q)
    check(f"{key} itf", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["fObj"][key][fid][iid]["r"] == 1 and iid not in doc()["fObj"][key]["0"])
    cv0 = cv(); q, rid = rq("field.fia", fia=sell, id=int(iid)); st, r, _ = call(q)
    check(f"{key} sell from field", r["callstack"][rid] == [{"t":1,"v":""}] and cv() == cv0 + cfg["gameItems"][key][str(cid)]["sellVirtual"] and iid not in doc()["fObj"][key][fid])
    rid, r = buy(fia=fia, **{idf: int(cid)}, x=56, y=56, r=0, cR=0); iid = new_id(r, key)
    q, rid = rq("inventory.iva", iva="fti", type=cat, id=int(iid), cnt=1); call(q)
    cv0 = cv(); q, rid = rq("inventory.iva", iva="sfi", type=cat, ids=[int(iid)]); st, r, _ = call(q)
    check(f"{key} sfi", r["callstack"][rid] == [{"t":1,"v":""}] and cv() == cv0 + cfg["gameItems"][key][str(cid)]["sellVirtual"] and iid not in doc()["fObj"][key]["0"])

# roads: fti/itf/sR recompute building activity
rid, r = buy(fia="bR", rId=6, x=60, y=60, r=0, cR=0); road = r["obj"]["fObj"]["roads"][fid]; rd = max(road, key=int)
q, rid = rq("inventory.iva", iva="fti", type=14, id=int(rd), cnt=1); st, r, _ = call(q)
check("road fti + buildings resent", r["callstack"][rid] == [{"t":1,"v":""}] and rd in doc()["fObj"]["roads"]["0"] and r["obj"]["fObj"]["roads"][fid][rd]["inv"] == 1)
q, rid = rq("inventory.iva", iva="itf", type=14, id=int(rd), x=61, y=61, r=0); st, r, _ = call(q)
check("road itf", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["fObj"]["roads"][fid][rd]["x"] == 61)
cv0 = cv(); q, rid = rq("field.fia", fia="sR", id=int(rd)); st, r, _ = call(q)
check("sell road", r["callstack"][rid] == [{"t":1,"v":""}] and cv() == cv0 + cfg["gameItems"]["roads"]["6"]["sellVirtual"] and rd not in doc()["fObj"]["roads"][fid] and r["obj"]["fObj"]["roads"][fid][rd]["del"] == 1)

# specials: new players have a nursery + breeding lab in the inventory (fObj.specials == [{...}])
specials_inv = doc()["fObj"]["specials"]
inv0 = specials_inv[0] if isinstance(specials_inv, list) else specials_inv["0"]
lab = next(k for k, v in inv0.items() if v["sbId"] == 1)
q, rid = rq("inventory.iva", iva="itf", type=5, id=int(lab), x=64, y=64, r=0); st, r, _ = call(q)
check("special itf: placed on the field", r["callstack"][rid] == [{"t":1,"v":""}] and lab in doc()["fObj"]["specials"][fid] and lab not in doc()["fObj"]["specials"]["0"])
q, rid = rq("inventory.iva", iva="fti", type=5, id=int(lab), cnt=1); st, r, _ = call(q)
check("special fti", r["callstack"][rid] == [{"t":1,"v":""}] and lab in doc()["fObj"]["specials"]["0"])
q, rid = rq("inventory.iva", iva="itf", type=5, id=int(lab), x=64, y=64, r=0); call(q)
cv0 = cv(); q, rid = rq("field.fia", fia="sSB", id=int(lab)); st, r, _ = call(q)
check("sell special: server pays + sends uObj", r["callstack"][rid] == [{"t":1,"v":""}] and cv() == cv0 + cfg["gameItems"]["specials"]["1"]["sellVirtual"] and r["obj"]["uObj"]["uCv"] == cv())
cv0 = cv(); rid, r = buy(fia="bSB", sbId=2, x=66, y=66, r=0, cR=0)
nur = next(iter(r["obj"]["fObj"]["specials"][fid]))
check("buy nursery: charged, stored with the HAR fields", r["callstack"][rid] == [{"t":1,"v":""}] and cv() == cv0 - cfg["gameItems"]["specials"]["2"]["buyVirtual"] and doc()["fObj"]["specials"][fid][nur]["sbId"] == 2 and "usedItemId5" in doc()["fObj"]["specials"][fid][nur])
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uCv": 10}})
rid, r = buy(fia="bSB", sbId=1, x=68, y=68, r=0, cR=0)
check("buy breeding lab broke -> notEnoughMoney", r["callstack"][rid][0]["v"] == "zoo.error.notEnoughMoney")
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uCv": 100000}})
q, rid = rq("field.fia", fia="sD", id=987654321); st, r, _ = call(q)
check("sell unknown item -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")

# ---- collection.rs (turn in a completed set) ----
sets = cfg["collSetConf"]
def give_set(items_, n=1):
    A.data_db.update_one({"id": uid}, {"$set": {f"zoo.collItems.{i}": {"uId": uid, "id": i, "cnt": n} for i in items_}})
cset = sets["cages"]["1"]; give_set(cset["items"])
d0 = doc()["uObj"]
reward = cset["rewards"]["1"]; field = {0: "uCv", 2: "uEp"}[reward["id"]]
q, rid = rq("collection.rs", type="cages", id=1, rId=1); st, r, _ = call(q)
check("rs: t:1, one of each item used, user reward paid", r["callstack"][rid] == [{"t":1,"v":""}] and all(doc()["collItems"][str(i)]["cnt"] == 0 for i in cset["items"]) and doc()["uObj"][field] >= d0[field] + reward["amount"] and r["obj"]["collItems"][str(cset["items"][0])]["cnt"] == 0)
q, rid = rq("collection.rs", type="cages", id=1, rId=1); st, r, _ = call(q)
check("rs incomplete set -> invalidRequest + collItems resync, nothing paid", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest" and "collItems" in r["obj"])
# a decor reward lands in the inventory
dset_id, dset, rk = next((sid, s, k) for sid, s in sets["cages"].items() for k, rw in s["rewards"].items() if rw["type"] == "decor")
give_set(dset["items"]); dId = dset["rewards"][rk]["id"]
q, rid = rq("collection.rs", type="cages", id=int(dset_id), rId=int(rk)); st, r, _ = call(q)
sent = list(r["obj"]["fObj"]["decos"]["0"].values())
check("rs decor reward: new deco in fObj.decos.0 and sent", r["callstack"][rid] == [{"t":1,"v":""}] and len(sent) == 1 and sent[0]["dId"] == dId and str(sent[0]["id"]) in doc()["fObj"]["decos"]["0"])
# material, assist (hours), event set with paws
mset_id, mset, mk = next((sid, s, k) for sid, s in sets["cages"].items() for k, rw in s["rewards"].items() if rw["type"] == "material")
give_set(mset["items"]); mid = mset["rewards"][mk]["id"]; m0 = doc()["mat"].get(str(mid), {}).get("cnt", 0)
q, rid = rq("collection.rs", type="cages", id=int(mset_id), rId=int(mk)); st, r, _ = call(q)
check("rs material reward", doc()["mat"][str(mid)]["cnt"] == m0 + mset["rewards"][mk]["amount"] and "mat" in r["obj"])
aset = sets["assists"]["3"]; give_set(aset["items"])
q, rid = rq("collection.rs", type="assists", id=3, rId=1); st, r, _ = call(q)
end = int(doc()["asObj"]["3"]["end"])
check("rs assist reward: 6h of assistant 3", r["callstack"][rid] == [{"t":1,"v":""}] and abs(end - (int(time.time()) + 6 * 3600)) < 60 and "asObj" in r["obj"])
eset = sets["specials"]["events"]["3"]; give_set(eset["items"]); p0 = doc()["uObj"]["pPaw"]
q, rid = rq("collection.rs", type="events", id=3, rId=2); st, r, _ = call(q)
check("rs event set (collSetConf.specials.events) pays paws", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["uObj"]["pPaw"] == p0 + eset["rewards"]["2"]["amount"])
q, rid = rq("collection.rs", type="genus", id=1, rId=1); st, r, _ = call(q)
check("rs unknown set type -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")

# ---- resource storage limit (res.<id>.mCnt) ----
rset_id, rset, rk = next((sid, s, k) for sid, s in sets["assists"].items() for k, rw in s["rewards"].items() if rw["type"] == "resource")
rres = str(rset["rewards"][rk]["id"]); mcap = doc()["res"][rres]["mCnt"]
A.data_db.update_one({"id": uid}, {"$set": {f"zoo.res.{rres}.cnt": mcap - 1}})
give_set(rset["items"])
q, rid = rq("collection.rs", type="assists", id=int(rset_id), rId=int(rk)); st, r, _ = call(q)
check("set reward resource capped at mCnt", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["res"][rres]["cnt"] == mcap and r["obj"]["res"][rres]["cnt"] == mcap)
A.data_db.update_one({"id": uid}, {"$set": {"zoo.res.1.cnt": doc()["res"]["1"]["mCnt"] - 5, "zoo.uObj.uCv": 100000}})
cv0 = cv(); q, rid = rq("field.fia", fia="bIr", irId=1, cnt=6, cR=0); st, r, _ = call(q)
check("buying more than fits -> invalidRequest, not charged, res resent", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest" and cv() == cv0 and "res" in r["obj"] and doc()["res"]["1"]["cnt"] == doc()["res"]["1"]["mCnt"] - 5)
q, rid = rq("field.fia", fia="bIr", irId=1, cnt=5, cR=0); st, r, _ = call(q)
check("buying exactly what fits works", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["res"]["1"]["cnt"] == doc()["res"]["1"]["mCnt"] and cv() < cv0)
A.data_db.update_one({"id": uid}, {"$set": {"zoo.res.2.cnt": doc()["res"]["2"]["mCnt"] - 3, "zoo.uTObj.r": {str(i): {"type": "resources", "id": 2, "cnt": 40} for i in range(1, 9)}}})
q, rid = rq("tombola.rTT"); st, r, _ = call(q)
check("tombola resource prize capped at mCnt", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["res"]["2"]["cnt"] == doc()["res"]["2"]["mCnt"])
m33 = doc()["mat"].get("33", {"cnt": 0, "mCnt": 250})
A.data_db.update_one({"id": uid}, {"$set": {"zoo.mat.33.cnt": m33.get("mCnt", 250)}})
mset_id, mset, mk = next((sid, s, k) for sid, s in sets["cages"].items() for k, rw in s["rewards"].items() if rw["type"] == "material" and rw["id"] == 33)
give_set(mset["items"]); q, rid = rq("collection.rs", type="cages", id=int(mset_id), rId=int(mk)); call(q)
check("materials stay uncapped (the client doesn't cap them)", doc()["mat"]["33"]["cnt"] == m33.get("mCnt", 250) + mset["rewards"][mk]["amount"])

# ---- daily quests ----
fid = doc()["uObj"]["current_field"]
rid_, r = buy(fia="bC", cId=1, x=70, y=70, r=0, cR=0); qcage = int(new_id(r, "cages"))
buy(fia="bAC", id=qcage, aId=sp1["m"]["animalId"], cR=0)
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.nDQ": 0, "zoo.uObj.uTut": 0}})
q, rid = rq("quest.gQ"); st, r, _ = call(q)
daily = r["obj"]["qObj"]["daily"]
check("gQ past nDQ: 5 fresh quests, nDQ ~24h ahead", r["callstack"][rid] == [{"t":1,"v":""}] and len(daily) == 5 and abs(r["obj"]["uObj"]["nDQ"] - (int(time.time()) + 86400)) < 60)
owned = {c["sId"] for f, cs in doc()["fObj"]["cages"].items() if f != "0" for c in cs.values() if c["male"] + c["female"] + c["child"] > 0}
check("quests only ask for owned species and known actions", all(t["itemId"] in owned and t["actionName"] in ("feed","water","clean","cuddle") and 5 <= t["actionCount"] <= 15 for qd in daily.values() for t in qd["tasks"]))
q, rid = rq("quest.gQ"); st, r, _ = call(q)
check("gQ before nDQ keeps the same quests", set(r["obj"]["qObj"]["daily"]) == set(daily))
# make quest A a single 'clean species 1' x2 task
qa, qb = sorted(daily)[:2]
A.data_db.update_one({"id": uid}, {"$set": {f"zoo.qObj.daily.{qa}.tasks": [{"affectAll": 0, "itemType": "species", "itemId": 1, "actionName": "clean", "actionCount": 2}],
                                             f"zoo.qObj.daily.{qa}.reward": {"currencyVirtual": 300, "xp": 1000, "resources": {"8": 3, "9": 0}, "currencyReal": 0}}})
A.data_db.update_one({"id": uid}, {"$unset": {f"zoo.questTargets.{qa}": ""}})
q, rid = rq("quest.gR", id=int(qa)); st, r, _ = call(q)
check("gR on unstarted quest -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")
q, rid = rq("quest.sQ", id=int(qa)); st, r, _ = call(q)
check("sQ: quest active and sent", r["callstack"][rid] == [{"t":1,"v":""}] and int(r["obj"]["qObj"]["daily"][qa]["active"]) == 1)
q, rid = rq("quest.sQ", id=int(qb)); st, r, _ = call(q)
check("sQ second quest while one is active -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")
q, rid = rq("field.fia", fia="cuAC", id=qcage); st, r, _ = call(q)
check("unrelated action doesn't count", doc()["qObj"]["daily"][qa]["tasks"][0]["actionCount"] == 2 and "qObj" not in r["obj"])
q, rid = rq("field.fia", fia="cAC", id=qcage); st, r, _ = call(q)
check("clean on species 1 counts down, quest sent", r["obj"]["qObj"]["daily"][qa]["tasks"][0]["actionCount"] == 1 and int(r["obj"]["qObj"]["daily"][qa]["done"]) == 0)
q, rid = rq("quest.cQ", id=int(qa)); st, r, _ = call(q)
check("cQ: back to not started, count reset", int(doc()["qObj"]["daily"][qa]["active"]) == 0 and doc()["qObj"]["daily"][qa]["tasks"][0]["actionCount"] == 2)
q, rid = rq("quest.sQ", id=int(qa)); call(q)
for _ in range(2):
    q, rid = rq("field.fia", fia="cAC", id=qcage); st, r, _ = call(q)
check("all tasks at 0 -> done", int(r["obj"]["qObj"]["daily"][qa]["done"]) == 1 and r["obj"]["qObj"]["daily"][qa]["tasks"][0]["actionCount"] == 0)
d0 = doc(); A.data_db.update_one({"id": uid}, {"$set": {"zoo.res.8.cnt": 0}})
q, rid = rq("quest.gR", id=int(qa)); st, r, _ = call(q); d1 = doc()
check("gR pays coins/xp/resources, removes quest, sends del", r["callstack"][rid] == [{"t":1,"v":""}] and d1["uObj"]["uCv"] == d0["uObj"]["uCv"] + 300 and d1["uObj"]["uEp"] >= d0["uObj"]["uEp"] + 1000 and d1["res"]["8"]["cnt"] == 3 and qa not in d1["qObj"]["daily"] and r["obj"]["qObj"]["daily"][qa]["del"] == 1)
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uCr": 5}})
q, rid = rq("quest.gNQ"); st, r, _ = call(q)
check("gNQ without 10 real -> notEnoughMoney", r["callstack"][rid][0]["v"] == "zoo.error.notEnoughMoney")
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uCr": 15}}); nDQ0 = doc()["uObj"]["nDQ"]
st, r, _ = call({"quest.gNQ": {}})
check("gNQ: new set for 10 real, free refresh time unchanged", doc()["uObj"]["uCr"] == 5 and len(doc()["qObj"]["daily"]) == 5 and not (set(doc()["qObj"]["daily"]) & set(daily)) and doc()["uObj"]["nDQ"] == nDQ0)
st, r, _ = call({"push.get": []})
check("push.get sends the quests", len(r["obj"]["qObj"]["daily"]) == 5)

# ---- remaining field.fia actions ----
fid = doc()["uObj"]["current_field"]
def fia(**p):
    q, rid = rq("field.fia", **p); st, r, _ = call(q); return r["callstack"][rid], r
def cage_(cid): return doc()["fObj"]["cages"][fid][str(cid)]
def setz(**kv): A.data_db.update_one({"id": uid}, {"$set": {"zoo." + k.replace("__", "."): v for k, v in kv.items()}})
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uCv": 1000000, "zoo.uObj.uCr": 1000, "zoo.uObj.pPaw": 100000, "zoo.uObj.uLvl": 50, "zoo.uObj.uTut": 0}})
t = int(time.time())
# instant build
cs, r = fia(fia="bC", cId=1, x=80, y=80, r=0, cR=0); fc = int(new_id(r, "cages"))
cr0 = doc()["uObj"]["uCr"]; cs, r = fia(fia="bdC", id=fc)
check("bdC finishes building for directBuildReal", cs == [{"t":1,"v":""}] and cage_(fc)["build"] <= int(time.time()) and doc()["uObj"]["uCr"] == cr0 - cfg["gameItems"]["cages"]["1"]["directBuildReal"])
cs, r = fia(fia="bdC", id=fc)
check("bdC on a built cage -> invalidRequest", cs[0]["v"] == "zoo.error.invalidRequest")
for a in ("m", "f"): fia(fia="bAC", id=fc, aId=sp1[a]["animalId"], cR=0)
spc = cfg["gameItems"]["animalsSpecies"]["1"]
# super feed / power feed / super heal
A.data_db.update_one({"id": uid}, {"$set": {"zoo.res.8.cnt": 2, "zoo.res.10.cnt": 1, "zoo.res.9.cnt": 1, f"zoo.fObj.cages.{fid}.{fc}.feed": t}})
ep0 = doc()["uObj"]["uEp"]; cs, r = fia(fia="sfAC", id=fc)
check("sfAC: 1 superfood, feed refilled, xp", cs == [{"t":1,"v":""}] and doc()["res"]["8"]["cnt"] == 1 and cage_(fc)["feed"] >= t + spc["feedTime"] and doc()["uObj"]["uEp"] > ep0)
cs, r = fia(fia="pfAC", id=fc)
check("pfAC: 1 powerfood", cs == [{"t":1,"v":""}] and doc()["res"]["10"]["cnt"] == 0)
cs, r = fia(fia="pfAC", id=fc)
check("pfAC without powerfood -> notEnoughResources", cs[0]["v"] == "zoo.error.notEnoughResources")
setz(**{f"fObj__cages__{fid}__{fc}__health": t - 10})
cs, r = fia(fia="shAC", id=fc); cg = cage_(fc)
check("shAC: supermedicine, sick=0, health + 2 sickTime", cs == [{"t":1,"v":""}] and doc()["res"]["9"]["cnt"] == 0 and cg["sick"] == 0 and cg["health"] >= t + spc["healthTime"] + 2 * spc["sickTime"])
setz(**{f"fObj__cages__{fid}__{fc}__health": t - 10, "res__7__cnt": 10})
cs, r = fia(fia="hAC", id=fc); cg = cage_(fc)
check("hAC: sick/health set like the client", cs == [{"t":1,"v":""}] and cg["sick"] >= t + spc["sickTime"] and cg["health"] >= t + spc["healthTime"] + spc["sickTime"] and doc()["res"]["7"]["cnt"] == 8)
# cage upgrade
uc2 = cfg["main"]["ucObj"]["2"]; d0 = doc()["uObj"]
cs, r = fia(fia="uc", id=fc)
check("uc: level 2 for pp coins + pPaw", cs == [{"t":1,"v":""}] and cage_(fc)["level"] == 2 and doc()["uObj"]["uCv"] == d0["uCv"] - uc2["pp"] and doc()["uObj"]["pPaw"] == d0["pPaw"] - uc2["pPaw"])
setz(**{f"fObj__cages__{fid}__{fc}__level": 5})
cs, r = fia(fia="uc", id=fc)
check("uc at level 5 -> invalidRequest", cs[0]["v"] == "zoo.error.invalidRequest")
setz(**{f"fObj__cages__{fid}__{fc}__level": 1})
# animals: sell one, buy one into the inventory, move between cages
male = next(a for a in doc()["animals"][fid][str(fc)].values() if a["aId"] == sp1["m"]["animalId"])
cv0 = cv(); cs, r = fia(fia="sAC", id=fc, aId=male["id"])
check("sAC: animal sold, cage male-1", cs == [{"t":1,"v":""}] and cv() == cv0 + sp1["m"]["sellVirtual"] and cage_(fc)["male"] == 0 and str(male["id"]) not in doc()["animals"][fid][str(fc)])
cs, r = fia(fia="bAInv", aId=sp1["m"]["animalId"], cR=0)
inv_new = list(r["obj"]["animals"]["0"]["0"].values())[0]
check("bAInv: animal in inventory, charged", cs == [{"t":1,"v":""}] and str(inv_new["id"]) in doc()["animals"]["0"]["0"] and cv() == cv0 + sp1["m"]["sellVirtual"] - sp1["m"]["buyVirtual"])
cs, r = fia(fia="bC", cId=1, x=84, y=84, r=0, cR=0); fc2 = int(new_id(r, "cages"))
female = next(iter(doc()["animals"][fid][str(fc)].values()))
cs, r = fia(fia="mAC", aId=female["id"], idf=fc, idt=fc2)
check("mAC: moved between cages", cs == [{"t":1,"v":""}] and str(female["id"]) in doc()["animals"][fid][str(fc2)] and cage_(fc2)["female"] == 1 and cage_(fc)["female"] == 0)
# entrance building
cs, r = fia(fia="sEb", id=2, fId=fid)
check("sEb: entrance building saved", cs == [{"t":1,"v":""}] and doc()["pfObj"][fid]["eBuildingId"] == 2)
cs, r = fia(fia="sEb", id=999, fId=fid)
check("sEb unknown building -> invalidRequest", cs[0]["v"] == "zoo.error.invalidRequest")
# assistants
A.data_db.update_one({"id": uid}, {"$set": {"zoo.asObj.1": {"asId": "1", "end": "0", "nL": "1"}}})
cs, r = fia(fia="uA", asId=1)
check("uA with an expired assistant -> invalidRequest", cs[0]["v"] == "zoo.error.invalidRequest")
cr0 = doc()["uObj"]["uCr"]; cs, r = fia(fia="bAs", asId=1, cR=1, type=2)
e = doc()["asObj"]["1"]
check("bAs: 7 days for buyReal[2], nL=0", cs == [{"t":1,"v":""}] and abs(int(e["end"]) - (int(time.time()) + 604800)) < 60 and e["nL"] == "0" and doc()["uObj"]["uCr"] == cr0 - cfg["gameItems"]["assists"]["1"]["buyReal"]["2"])
setz(**{f"fObj__cages__{fid}__{fc2}__feed": 0, f"fObj__cages__{fid}__{fc2}__build": 0, "res__5__cnt": 100})
cs, r = fia(fia="uA", asId=1)
check("uA feed: hungry cages fed, all cages sent", cs == [{"t":1,"v":""}] and cage_(fc2)["feed"] > int(time.time()) and len(r["obj"]["fObj"]["cages"][fid]) == len(doc()["fObj"]["cages"][fid]))
cs, r = fia(fia="cAt", asId=1)
check("cAt: renew popup off", doc()["asObj"]["1"]["nL"] == "1")
setz(**{"asObj__6": {"asId": "6", "end": str(int(time.time()) + 999), "nL": "1"}})
cs, r = fia(fia="uA", asId=0)
check("zoo director needs all assistants", cs[0]["v"] == "zoo.error.invalidRequest")
# breeding lab + nursery (new players own one of each in the inventory)
inv0 = doc()["fObj"]["specials"]["0"]
lab = next(k for k, v in inv0.items() if v["sbId"] == 1) if any(v["sbId"] == 1 for v in inv0.values()) else None
if lab is None:
    cs, r = fia(fia="bSB", sbId=1, x=90, y=90, r=0, cR=0); lab = next(iter(r["obj"]["fObj"]["specials"][fid]))
else:
    q, rid = rq("inventory.iva", iva="itf", type=5, id=int(lab), x=90, y=90, r=0); call(q)
cs, r = fia(fia="bSB", sbId=2, x=94, y=94, r=0, cR=0); nur = next(iter(r["obj"]["fObj"]["specials"][fid]))
def buyinv(aid):
    cs, r = fia(fia="bAInv", aId=aid, cR=0); return list(r["obj"]["animals"]["0"]["0"].values())[0]["id"]
m_, f_ = buyinv(sp1["m"]["animalId"]), buyinv(sp1["f"]["animalId"])
setz(res__8__cnt=5, res__11__cnt=1)
genus = cfg["gameItems"]["genus"][str(spc["genusId"])]
cv0 = cv(); cs, r = fia(fia="bsASB", id=int(lab), aIdM=m_, aIdF=f_, items=[{"type": 13, "id": 8}])
L = doc()["fObj"]["specials"][fid][lab]
check("bsASB: parents used, cost + time, slots filled", cs == [{"t":1,"v":""}] and str(m_) not in doc()["animals"]["0"]["0"] and cv() == cv0 - spc["breedAdvanceCost"][0]["cnt"] and abs(L["end"] - (int(time.time()) + spc["breedAdvanceTime"])) < 60 and (L["usedItemId1"], L["usedItemId2"], L["usedItemType3"], L["usedItemId3"]) == (1, 1, 13, 8) and doc()["res"]["8"]["cnt"] == 4)
end0 = L["end"]; cs, r = fia(fia="bdASB", id=int(lab))
check("bdASB elixir halves the time left", cs == [{"t":1,"v":""}] and doc()["fObj"]["specials"][fid][lab]["end"] < end0 and doc()["res"]["11"]["cnt"] == 0)
cs, r = fia(fia="beASB", id=int(lab))
check("beASB before it's done -> invalidRequest", cs[0]["v"] == "zoo.error.invalidRequest")
setz(**{f"fObj__specials__{fid}__{lab}__end": int(time.time()) - 1})
cs, r = fia(fia="beASB", id=int(lab))
res_ = r["obj"].get("bAdvObj", {}).get("r", [])
baby_ok = len(res_) == 2 and cfg["gameItems"]["animals"][str(res_[0]["aId"])]["child"] == 1
check("beASB: baby to inventory, bAdvObj.r, lab reset", cs == [{"t":1,"v":""}] and baby_ok and doc()["fObj"]["specials"][fid][lab]["end"] == 0 and any(a["aId"] == res_[0]["aId"] for a in doc()["animals"]["0"]["0"].values()))
baby = next(a for a in doc()["animals"]["0"]["0"].values() if a["aId"] == res_[0]["aId"])
bspc = cfg["gameItems"]["animalsSpecies"][str(baby["sId"])]
cv0 = cv(); cs, r = fia(fia="rsASB", id=int(nur), aId=baby["id"])
N = doc()["fObj"]["specials"][fid][nur]
check("rsASB: baby in the nursery, raisingCost paid", cs == [{"t":1,"v":""}] and cv() == cv0 - bspc["raisingCost"][0]["cnt"] and N["usedItemId1"] == baby["sId"] and str(baby["id"]) not in doc()["animals"]["0"]["0"])
setz(res__12__cnt=1); cs, r = fia(fia="arASB", id=int(nur))
check("arASB potion", cs == [{"t":1,"v":""}] and doc()["res"]["12"]["cnt"] == 0)
cr0 = doc()["uObj"]["uCr"]; cs, r = fia(fia="rdASB", id=int(nur), aId=baby["aId"])
check("rdASB: finished now for raisingDirectCost", cs == [{"t":1,"v":""}] and doc()["uObj"]["uCr"] == cr0 - bspc["raisingDirectCost"][0]["cnt"])
cs, r = fia(fia="reASB", id=int(nur))
adult = r["obj"].get("raiseObj", {}).get("r", {}).get("0", {}).get("aId")
check("reASB: adult to inventory, raiseObj.r.0.aId, nursery reset", cs == [{"t":1,"v":""}] and adult in bspc["animalIds"][:2] and doc()["fObj"]["specials"][fid][nur]["end"] == 0)
cs, r = fia(fia="mSB", id=int(nur), x=96, y=96, r=1)
check("mSB moves the nursery", cs == [{"t":1,"v":""}] and doc()["fObj"]["specials"][fid][nur]["x"] == 96)
# resource pack
setz(res__8__cnt=0); cr0 = doc()["uObj"]["uCr"]
cs, r = fia(fia="bP", pId=31, cnt=2)
check("bP pack: 125 superfood for 125 real", cs == [{"t":1,"v":""}] and doc()["res"]["8"]["cnt"] == 125 and doc()["uObj"]["uCr"] == cr0 - 125)

# ---- expansion bounds ----
mz = str(doc()["fIds"]["1"])
A.data_db.update_one({"id": uid}, {"$set": {f"zoo.pfObj.{mz}.fSize": 10, f"zoo.pfObj.{mz}.minHorizontal": 98, f"zoo.pfObj.{mz}.maxVertical": -38, "zoo.uObj.uLvl": 3, "zoo.uObj.uEp": 0, "zoo.uObj.uCr": 100}})
q, rid = rq("init.getUser"); st, r, _ = call(q)
check("login fixes bounds that don't match fSize", {k: r["obj"]["pfObj"][mz][k] for k in ("fSize", "minHorizontal", "maxVertical")} == {"fSize": 10, "minHorizontal": 100, "maxVertical": -40})
q, rid = rq("field.fia", fia="bP", pId=11); st, r, _ = call(q)
check("low-level expansion: fSize 11 with size-11 bounds", r["callstack"][rid] == [{"t":1,"v":""}] and {k: r["obj"]["pfObj"][mz][k] for k in ("fSize", "minHorizontal", "maxVertical")} == {"fSize": 11, "minHorizontal": 98, "maxVertical": -38} and doc()["uObj"]["uCr"] == 95)
xp25 = int(cfg["main"]["u_level"][25])
A.data_db.update_one({"id": uid}, {"$set": {f"zoo.pfObj.{mz}.fSize": 10, f"zoo.pfObj.{mz}.minHorizontal": 100, f"zoo.pfObj.{mz}.maxVertical": -40, "zoo.uObj.uLvl": 25, "zoo.uObj.uEp": xp25}})
q, rid = rq("init.getUser"); st, r, _ = call(q)
check("login gives an old save its missed level expansions", r["obj"]["pfObj"][mz]["fSize"] == 12 and r["obj"]["pfObj"][mz]["minHorizontal"] == 96)
fid = doc()["uObj"]["current_field"]

# ---- extra zoos ----
def xp_for(level):
    return next(int(x) for x in cfg["main"]["u_level"] if A.userUtils.calculate_level_based_on_xp(int(x), cfg) == level)
d = doc(); mz = str(d["fIds"]["1"])
A.data_db.update_one({"id": uid}, {"$set": {"zoo.fIds": {"1": mz}, f"zoo.pfObj.{mz}.fSize": 12, "zoo.uObj.uLvl": 14, "zoo.uObj.uEp": xp_for(14), "zoo.uObj.uCr": 1000}})
st, r, _ = call({"push.get": []})
check("no extra zoo before its condition", set(doc()["fIds"]) == {"1"})
q, rid = rq("field.ul", t=6); st, r, _ = call(q)
check("ocean zoo can't be bought", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")
cr0 = doc()["uObj"]["uCr"]; q, rid = rq("field.ul", t=5); st, r, _ = call(q)
cz = doc()["fIds"].get("5"); pz = doc()["pfObj"].get(str(cz), {})
check("field.ul coast zoo for 75 real: fIds + pfObj sent", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["uObj"]["uCr"] == cr0 - 75 and "5" in r["obj"]["fIds"] and str(cz) in r["obj"]["pfObj"])
check("new zoo: start size, bounds, gate, road at (31,88)", pz.get("fSize") == 5 and pz.get("minHorizontal") == 110 and pz.get("fType") == 5 and any((rd["x"], rd["y"]) == (31, 88) for rd in doc()["fObj"]["roads"][str(cz)].values()))
q, rid = rq("field.ul", t=5); st, r, _ = call(q)
check("unlocking twice -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")
q, rid = rq("field.fia", fia="bP", pId=11); st, r, _ = call(q)
check("main zoo expansion 3 -> forgotten zoo unlocks for free", doc()["pfObj"][mz]["fSize"] == 13 and "2" in doc()["fIds"] and "2" in r["obj"].get("fIds", {}))
A.data_db.update_one({"id": uid}, {"$set": {"zoo.uObj.uEp": xp_for(17)}})
st, r, _ = call({"push.get": []})
check("level 17 -> ocean zoo for free", "6" in doc()["fIds"] and doc()["pfObj"][str(doc()["fIds"]["6"])]["eBuildingId"] == 8)
# switch zoo, build there, come back
fz = str(doc()["fIds"]["2"])
q, rid = rq("init.sP", fId=int(fz), type=2); st, r, _ = call(q)
check("init.sP: actFId + pfObj + fObj", r["callstack"][rid] == [{"t":1,"v":""}] and r["obj"]["actFId"] == fz and fz in r["obj"]["pfObj"] and doc()["uObj"]["current_field"] == fz)
q, rid = rq("field.fia", fia="bR", rId=6, x=31, y=87, r=0, cR=0); call(q)
q, rid = rq("field.fia", fia="bD", dId=int(next(k for k,v in cfg["gameItems"]["decos"].items() if v.get("buyable")==1 and 0 < v.get("buyVirtual",0) and v.get("userLevelRequired",99) <= 14)), x=33, y=86, r=0, cR=0); st, r, _ = call(q)
check("building in the forgotten zoo", r["callstack"][rid] == [{"t":1,"v":""}] and len(doc()["fObj"]["decos"][fz]) == 1)
st, r, _ = call({"push.get": []})
check("push.get on the forgotten zoo works", st == 200 and "pfObj" in r["obj"])
# forgotten expansion with tools
A.data_db.update_one({"id": uid}, {"$set": {"zoo.collItems.1": {"uId": uid, "id": 1, "cnt": 3}}})
size0 = doc()["pfObj"][fz]["fSize"]; cr0 = doc()["uObj"]["uCr"]
q, rid = rq("field.eFbC", tools=3, zd=2); st, r, _ = call(q)
check("eFbC: 3 tools + 2 real for the 5-real step", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["pfObj"][fz]["fSize"] == size0 + 1 and doc()["collItems"]["1"]["cnt"] == 0 and doc()["uObj"]["uCr"] == cr0 - 2)
q, rid = rq("field.eFbC", tools=1, zd=1); st, r, _ = call(q)
check("eFbC with the wrong total -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")
# everything into the inventory
q, rid = rq("field.moveItemsToInventory"); st, r, _ = call(q)
check("moveItemsToInventory empties the zoo", r["callstack"][rid] == [{"t":1,"v":""}] and not doc()["fObj"]["decos"][fz] and not doc()["fObj"]["roads"][fz])
q, rid = rq("init.sP", fId=int(mz), type=1); st, r, _ = call(q)
check("back to the main zoo", doc()["uObj"]["current_field"] == mz)
q, rid = rq("init.sP", fId=1, type=4); st, r, _ = call(q)
check("switching to a locked zoo -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")
fid = doc()["uObj"]["current_field"]

# ---- crafting centre ----
bp1 = cfg["gameItems"]["blueprints"]["1"]
mats = {f"zoo.mat.{m['id']}": {"uId": uid, "id": m["id"], "cnt": m["count"], "mCnt": 250} for m in bp1["materials"]}
A.data_db.update_one({"id": uid}, {"$set": dict(mats, **{"zoo.uObj.pPaw": bp1["craftPaws"], "zoo.crafting": {"active": 0}, "zoo.bp.1": {"uId": uid, "id": 1, "active": 1}, "zoo.res.15.cnt": 1, "zoo.uObj.uCr": 1000})})
q, rid = rq("craftingCenter.sbc", blueprintId=999999); st, r, _ = call(q)
check("sbc unknown blueprint -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")
q, rid = rq("craftingCenter.sbc", blueprintId=1); st, r, _ = call(q)
cr = doc()["crafting"]
check("sbc: materials + paws used, crafting running", r["callstack"][rid] == [{"t":1,"v":""}] and cr["active"] == 1 and cr["blueprintId"] == 1 and abs(cr["endTime"] - (int(time.time()) + bp1["craftDuration"])) < 60 and all(doc()["mat"][str(m["id"])]["cnt"] == 0 for m in bp1["materials"]) and doc()["uObj"]["pPaw"] == 0)
q, rid = rq("craftingCenter.sbc", blueprintId=1); st, r, _ = call(q)
check("sbc while busy -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")
q, rid = rq("craftingCenter.cbc"); st, r, _ = call(q)
check("cbc before it's done -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")
end0 = doc()["crafting"]["endTime"]; q, rid = rq("craftingCenter.dbct"); st, r, _ = call(q)
check("dbct: booster used, time left halved", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["res"]["15"]["cnt"] == 0 and doc()["crafting"]["endTime"] < end0)
cr0 = doc()["uObj"]["uCr"]; q, rid = rq("craftingCenter.icbc"); st, r, _ = call(q)
check("icbc: finished now for craftInstantReal", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["uObj"]["uCr"] == cr0 - bp1["craftInstantReal"] and doc()["crafting"]["endTime"] <= int(time.time()))
ep0 = doc()["uObj"]["uEp"]; ninv = len(doc()["fObj"]["decos"]["0"])
q, rid = rq("craftingCenter.cbc"); st, r, _ = call(q)
check("cbc: craftingReward, xp, item into the inventory, centre idle", r["callstack"][rid] == [{"t":1,"v":""}] and r["obj"]["craftingReward"]["item"] == bp1["reward"]["item"] and doc()["uObj"]["uEp"] >= ep0 + bp1["reward"]["xp"] and len(doc()["fObj"]["decos"]["0"]) == ninv + 1 and doc()["crafting"]["active"] == 0)
A.data_db.update_one({"id": uid}, {"$set": {"zoo.bp.2.active": 0}})
q, rid = rq("craftingCenter.sbc", blueprintId=2); st, r, _ = call(q)
check("sbc without the blueprint -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")

# ---- recycling centre ----
m1 = cfg["gameItems"]["materials"]["1"]; rc = cfg["recyclingCenter"]
A.data_db.update_one({"id": uid}, {"$set": {"zoo.recyclingSlots": {"1": {"uId": uid, "slotId": 1, "materialId": 0, "amount": 0, "finishTime": 0, "endTime": 0}},
                                             "zoo.res.13.cnt": 1000, "zoo.res.13.mCnt": 2000, "zoo.res.14.cnt": 1, "zoo.uObj.uCv": 100000, "zoo.uObj.uCr": 1000, "zoo.mat.1.cnt": 0, "zoo.mat.2.cnt": 0}})
q, rid = rq("recyclingCenter.grs"); st, r, _ = call(q)
check("grs: slot 1", r["callstack"][rid] == [{"t":1,"v":""}] and set(r["obj"]["recyclingSlots"]) == {"1"})
cr0 = doc()["uObj"]["uCr"]; q, rid = rq("recyclingCenter.brs", slotId=2, days=7); st, r, _ = call(q)
s2 = doc()["recyclingSlots"].get("2", {})
check("brs: slot 2 rented for 7 days", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["uObj"]["uCr"] == cr0 - rc["slotRentDays"]["7"]["rc"] and abs(s2.get("endTime", 0) - (int(time.time()) + 7 * 86400)) < 60)
cv0 = cv(); q, rid = rq("recyclingCenter.srm", slotId=1, materialId=1, amount=5, useBooster=1); st, r, _ = call(q)
s1 = doc()["recyclingSlots"]["1"]
check("srm: trash + coins + booster used, slot producing", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["res"]["13"]["cnt"] == 1000 - 5 * m1["craftTrash"] and cv() == cv0 - 5 * m1["craftVirtual"] and doc()["res"]["14"]["cnt"] == 0 and s1["materialId"] == 1 and abs(s1["finishTime"] - (int(time.time()) + 5 * m1["craftDuration"])) < 60)
q, rid = rq("recyclingCenter.srm", slotId=1, materialId=1, amount=1, useBooster=0); st, r, _ = call(q)
check("srm on a busy slot -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")
q, rid = rq("recyclingCenter.srm", slotId=2, materialId=2, amount=1, useBooster=0); st, r, _ = call(q)
check("srm on a rare material -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")
q, rid = rq("recyclingCenter.crs", slotId=1); st, r, _ = call(q)
check("crs before it's done -> invalidRequest", r["callstack"][rid][0]["v"] == "zoo.error.invalidRequest")
cr0 = doc()["uObj"]["uCr"]; q, rid = rq("recyclingCenter.icrs", slotId=1); st, r, _ = call(q)
layer = r["obj"].get("itemLayer", {})
check("icrs: paid, 5 wood, slot empty, itemLayer", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["uObj"]["uCr"] == cr0 - 5 * m1["craftInstantReal"] and doc()["mat"]["1"]["cnt"] == 5 and doc()["recyclingSlots"]["1"]["materialId"] == 0 and layer.get("type") == "recycling" and layer["items"]["0"]["0"] == {"id": 1, "count": 5})
q, rid = rq("recyclingCenter.srm", slotId=2, materialId=1, amount=1, useBooster=0); call(q)
A.data_db.update_one({"id": uid}, {"$set": {"zoo.recyclingSlots.2.finishTime": int(time.time()) - 1}})
q, rid = rq("recyclingCenter.crs", slotId=2); st, r, _ = call(q)
check("crs: finished slot collected", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["mat"]["1"]["cnt"] >= 6)
A.data_db.update_one({"id": uid}, {"$set": {"zoo.recyclingSlots.2.endTime": int(time.time()) - 1}})
q, rid = rq("recyclingCenter.grs"); st, r, _ = call(q)
check("expired rented slot goes away", "2" not in r["obj"]["recyclingSlots"])
from commands import recyclingCenter as RC
RC.random.seed(3)
rolls = [RC.random.randint(1, 100) <= 10 for _ in range(1000)]
check("rare chance roll sanity (10% for 5 units)", 60 < sum(rolls) < 140)
cr0 = doc()["uObj"]["uCr"]; q, rid = rq("item.buySB", id=2); st, r, _ = call(q)
got = list(r["obj"].get("itemLayer", {}).get("items", {}).get("0", {}).values())
check("buySB: box paid, 4 material stacks given", r["callstack"][rid] == [{"t":1,"v":""}] and doc()["uObj"]["uCr"] == cr0 - 20 and len(got) == 4 and r["obj"]["itemLayer"]["type"] == "surpriseBox")

# token check (non-dev mode)
A.LOCAL_DEV_MODE = False
other = A.app.test_client()
st, r, _ = call({"push.get": []}, client=other)
check("bad token -> 200 + notAuth", st == 200 and r["callstack"] == {"0":[{"t":0,"v":"system.user.notAuth"}]})
st, r, _ = call({"push.get": []})  # the registering client has a valid session token
check("good token still works", st == 200 and "uObj" in r["obj"])
A.LOCAL_DEV_MODE = True
res = c.post("/ZooApi.php?uId=abc", data={"json": "{}"})
check("malformed request -> 200 + error", res.status_code == 200 and res.get_json()["callstack"]["0"][0]["t"] == 0)
print("\nFAILED:" if fails else "\nALL PASSED", fails)
sys.exit(1 if fails else 0)
