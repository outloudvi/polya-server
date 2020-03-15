from falcon import HTTP_UNAUTHORIZED, HTTPUnauthorized
from polyaserver.utils import valid_login


def Authorized(req, resp, resource, params):
    if not valid_login(req):
        resp.status = HTTP_UNAUTHORIZED
        resp.media = {"reason": "No 'Authorization' header"}
        raise HTTPUnauthorized(
            'Unauthorized', "No 'Authorization' header")
