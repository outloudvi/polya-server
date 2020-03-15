from signal import signal, SIGINT
from sys import exit
import falcon
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import config
import uuid
import json
import os
from collections import defaultdict

ph = PasswordHasher()

DB = {
    "sessions": [],
    "grading_students": {}
}


def savedata():
    json.dump(DB, open("db.json", "w"))


def loaddata():
    global DB
    db = json.load(open("db.json"))
    client_config = json.load(open("client_config.json"))
    DB = db
    DB["client_config"] = client_config
    DB["grading_students"] = readSubmissions(config.SUBMISSION_DIR)
    print("Searching dir {}, {} submissions found.".format(
        config.SUBMISSION_DIR, len(DB["grading_students"])))


def readSubmissions(direc):
    for (dirpath, dirnames, _) in os.walk(direc):
        if dirpath == direc:
            return dirnames


class PublicRes:
    def __init__(self):
        self.return_immediately = False


def Authorized(req, resp, resource, params):
    if not valid_login(req):
        resp.status = falcon.HTTP_UNAUTHORIZED
        resp.media = {"reason": "No 'Authorization' header"}
        raise falcon.HTTPUnauthorized(
            'Unauthorized', "No 'Authorization' header")


def valid_login(req):
    if req.auth is None:
        return False
    key = req.auth
    key_info = key.split(" ")
    return key_info[0] == "Bearer" and key_info[1] in DB["sessions"]


# ---- /register ----
class AuthRes(PublicRes):
    def on_get(self, req, resp):
        if req.auth is None:
            resp.status = falcon.HTTP_BAD_REQUEST
            return
        hash = req.auth.split(" ")
        if len(hash) != 2 or hash[0] != "Bearer":
            resp.status = falcon.HTTP_BAD_REQUEST
            return
        try:
            ph.verify(hash[1], config.AUTH_KEY)
        except VerifyMismatchError:
            resp.status = falcon.HTTP_UNAUTHORIZED
            return

        uuidid = str(uuid.uuid4())
        DB["sessions"].append(uuidid)
        print("Authenticated:", uuidid)
        resp.media = {
            "token": uuidid
        }

# ---- /revoke ----
@falcon.before(Authorized)
class RevokeRes(PublicRes):
    def on_delete(self, req, resp):
        hash = req.auth.split(" ")
        if len(hash) != 2 or hash[0] != "Bearer":
            resp.status = falcon.HTTP_BAD_REQUEST
            return
        uuidid = hash[1]
        if uuidid in DB["sessions"]:
            print("Revoked", uuidid)
            DB["sessions"].remove(uuidid)

# ---- /config ----
@falcon.before(Authorized)
class ConfigRes(PublicRes):
    def on_get(self, req, resp):
        resp.media = {
            "config": DB["client_config"]
        }

    on_post = on_get

# --- / ----
@falcon.before(Authorized)
class InfoRes(PublicRes):
    def on_post(self, req, resp):
        resp.media = {"c": "4"}

    on_get = on_post

# --- /image.tar ----
@falcon.before(Authorized)
class ImageRes(PublicRes):
    def on_post(self, req, resp):
        print("Fetched file")
        resp.stream = open("./image.tar")

    on_get = on_post


def SigintHandler(signal_received, frame):
    print("Saving data to db...")
    savedata()


try:
    loaddata()
except Exception:
    print("Data not loaded. Starting clean.")
    pass
signal(SIGINT, SigintHandler)
api = falcon.API()
api.add_route("/register", AuthRes())
api.add_route("/revoke", RevokeRes())
api.add_route("/config", ConfigRes())
api.add_route("/image.tar", ImageRes())
api.add_route("/", InfoRes())
