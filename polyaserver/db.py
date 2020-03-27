import json
import ZODB, ZODB.FileStorage, transaction

def savedata():
    transaction.commit()
    print("Transcation committed")
    return CONN


def loaddata():
    storage = ZODB.FileStorage.FileStorage('db.fs')
    db = ZODB.DB(storage)
    conn = db.open()
    root = conn.root
    client_config = json.load(open("client_config.json"))
    print("Updating client config")
    root.client_config = client_config
    initialize_temp_db(root)
    if "initialized" not in root._root:
        initialize_db(root)
    print("Database connected")
    return root, conn

def initialize_db(root):
    root.sessions = []
    root.students = {}
    root.grading_students = {}
    root.initialized = True
    print("Database initialized")

def initialize_temp_db(root):
    root.temp = {}
    root.temp["lockdowns"] = {}

DB, CONN = loaddata()
TEMPDB = DB.temp