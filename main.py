import falcon
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import config
import uuid

ph = PasswordHasher()

AUTHORIZED_SESSIONS = []


def Authorized(req, resp, resource, params):
    if not valid_login(req):
        resp.status = falcon.HTTP_UNAUTHORIZED
        resp.media = {"reason": "No 'Authorization' header"}
        raise falcon.HTTPUnauthorized('Unauthorized', "No 'Authorization' header")


def valid_login(req):
    if req.auth is None:
        return False
    key = req.auth
    key_info = key.split(" ")
    return key_info[0] == "Bearer" and key_info[1] in AUTHORIZED_SESSIONS


# ---- /register ----
class AuthRes:
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
        AUTHORIZED_SESSIONS.append(uuidid)
        print("Authenticated:", uuidid)
        resp.media = {
            "token": uuidid
        }

# ---- /revoke ----
@falcon.before(Authorized)
class RevokeRes:
    def on_delete(self, req, resp):
        hash = req.auth.split(" ")
        if len(hash) != 2 or hash[0] != "Bearer":
            resp.status = falcon.HTTP_BAD_REQUEST
            return
        uuidid = hash[1]
        if uuidid in AUTHORIZED_SESSIONS:
            print("Revoked", uuidid)
            AUTHORIZED_SESSIONS.remove(uuidid)


# --- / ----
@falcon.before(Authorized)
class InfoRes:
    def on_post(self, req, resp):
        if resp.return_directly:
            return
        resp.media = {"c": "4"}

    on_get = on_post


api = falcon.API()
api.add_route("/register", AuthRes())
api.add_route("/revoke", RevokeRes())
api.add_route("/", InfoRes())
