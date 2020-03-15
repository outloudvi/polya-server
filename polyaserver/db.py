from polyaserver.staticdb import DB, TEMPDB
import json

def savedata():
    json.dump(DB, open("db.json", "w"))


def loaddata():
    global DB
    db = json.load(open("db.json"))
    client_config = json.load(open("client_config.json"))
    for _, v in enumerate(db):
        DB[v] = db[v]
    DB["client_config"] = client_config