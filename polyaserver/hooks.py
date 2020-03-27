from falcon import HTTP_UNAUTHORIZED, HTTPUnauthorized
from polyaserver.utils import valid_login


def Authorized(req, resp, resource, params):
    if not valid_login(req):
        resp.status = HTTP_UNAUTHORIZED
        resp.media = {"reason": "No 'Authorization' header"}
        raise HTTPUnauthorized(
            'Unauthorized', "No 'Authorization' header")


def FromLocal(req, resp, resource, params):
    src = req.remote_addr
    if src == "127.0.0.1" or src == "::1":
        return
    resp.status = HTTP_UNAUTHORIZED
    resp.media = {"reason": "This endpoint is only accessible from localhost."}
    raise HTTPUnauthorized(
        'Unauthorized', "This endpoint is only accessible from localhost.")
