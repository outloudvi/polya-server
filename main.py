from signal import signal, SIGINT
from sys import exit
import falcon
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import config
import uuid
import json
import os
import yaml
import tarfile
import tempfile
from collections import defaultdict

ph = PasswordHasher()

DB = {
    "sessions": [],
    "grading_students": {}
}


class Student:
    def __init__(self, student_id):
        filename = os.path.join(config.SUBMISSION_DIR, student_id, "init.yml")
        try:
            with open(filename) as fp:
                content = yaml.load(fp, Loader=yaml.BaseLoader)
        except Exception as es:
            print("Failed reading {}: {}".format(student_id, es))
            self.valid = False
            return
        self.student_id: str = student_id
        self.build_shell: str = content["build_shell"] or ""
        self.run_shell: str = content["run_shell"] or ""
        self.notification: str = content["notification"] or ""
        self.valid = True


def savedata():
    json.dump(DB, open("db.json", "w"))


def loaddata():
    global DB
    db = json.load(open("db.json"))
    client_config = json.load(open("client_config.json"))
    for _, v in enumerate(db):
        DB[v] = db[v]
    DB["client_config"] = client_config

def readdir():
    for student_id in readSubmissions(config.SUBMISSION_DIR):
        DB["grading_students"][student_id] = False
    print("Searching dir {}, {} submissions found.".format(
        config.SUBMISSION_DIR, len(DB["grading_students"])))


def readSubmissions(direc):
    for (dirpath, dirnames, _) in os.walk(direc):
        if dirpath == direc:
            return dirnames


def get_tar_result(file, name):
    f = tempfile.NamedTemporaryFile()
    tar = tarfile.open(f.name, "w")
    tar.add(file, name)
    tar.close()
    return f


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


def read_next_ungraded_student():
    for _, id in enumerate(DB["grading_students"]):
        if DB["grading_students"][id] == False:
            print("fs")
            return Student(id)
    return None


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

# ---- /next ----
@falcon.before(Authorized)
class NextRes(PublicRes):
    def on_get(self, req, resp):
        student: Student = read_next_ungraded_student()
        if student == None:
            resp.status = falcon.HTTP_NOT_FOUND
            resp.media = {
                "failure": "No ungraded students",
                "student": {}
            }
            return
        resp.media = {
            "student": student.__dict__
        }
        DB["grading_students"][student.student_id] = True

    on_post = on_get

# ---- /students ----
@falcon.before(Authorized)
class StudentListRes(PublicRes):
    def on_get(self, req, resp,):
        resp.media = {
            "students": list(DB["grading_students"].keys())
        }

# ---- /student/{id} ----
@falcon.before(Authorized)
class StudentRes(PublicRes):
    def on_get(self, req, resp, id, action):
        student: Student = Student(id)
        if not student.valid:
            resp.status = falcon.HTTP_NOT_FOUND
            resp.media = {
                "failure": "Student not found"
            }
            return
        if action == "tar":
            self.return_tar(student, resp)
        elif action == "info":
            self.return_info(student, resp)
        else:
            resp.status = falcon.HTTP_BAD_GATEWAY

    @staticmethod
    def return_tar(student, resp):
        resp.stream = get_tar_result(os.path.join(
            config.SUBMISSION_DIR, student.student_id),
            student.student_id)
        resp.content_type = "application/x-tar"

    @staticmethod
    def return_info(student: Student, resp):
        retn = student.__dict__
        retn["graded"] = DB["grading_students"][student.student_id]
        resp.media = retn

    on_post = on_get


def SigintHandler(signal_received, frame):
    print("Saving data to db...")
    savedata()


try:
    loaddata()
except Exception:
    print("Data not loaded. Starting clean.")
    pass
readdir()
signal(SIGINT, SigintHandler)
api = falcon.API()
api.add_route("/register", AuthRes())
api.add_route("/revoke", RevokeRes())
api.add_route("/config", ConfigRes())
api.add_route("/image.tar", ImageRes())
api.add_route("/next", NextRes())
api.add_route("/students", StudentListRes())
api.add_route("/student/{id}/{action}", StudentRes())
api.add_route("/", InfoRes())
