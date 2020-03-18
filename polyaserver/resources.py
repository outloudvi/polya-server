import config
from polyaserver.staticdb import DB, TEMPDB
from polyaserver.internal_const import DEFAULT_GRADING_STATUS

from polyaserver.classes import Student
from polyaserver.hooks import Authorized
from polyaserver.utils import get_tar_result, lockStudent, read_next_ungraded_student, unlockStudent, readJSON, get_auth_key

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from threading import Timer
import falcon
import os
import uuid

ph = PasswordHasher()


class PublicRes:
    def __init__(self):
        self.return_immediately = False


# ---- /register ----
class AuthRes(PublicRes):
    def on_get(self, req, resp):
        if req.auth is None:
            resp.media = {
                "failure": "Register token not found"
            }
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
            resp.media = {
                "failure": "Bad bearer token format"
            }
            resp.status = falcon.HTTP_BAD_REQUEST
            return
        uuidid = hash[1]
        if uuidid in DB["sessions"]:
            print("Revoked", uuidid)
            DB["sessions"].remove(uuidid)
            for i in TEMPDB["lockdowns"]:
                if TEMPDB["lockdowns"][i] == uuidid:
                    del TEMPDB["lockdowns"][i]


# ---- /config ----
@falcon.before(Authorized)
class ConfigRes(PublicRes):
    def on_get(self, req, resp):
        if "client_config" in DB:
            conf = DB["client_config"]
        else:
            conf = {}
        resp.media = {
            "config": conf
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
                "failure": "No ungraded students"
            }
            return
        resp.media = {
            "student": student.__dict__
        }

    on_post = on_get

# ---- /students ----
@falcon.before(Authorized)
class StudentListRes(PublicRes):
    def on_get(self, req, resp):
        if req.get_param_as_bool("detail"):
            ret = []
            for _, id in enumerate(DB["grading_students"]):
                obj = {}
                obj["student_id"] = id
                obj["grades"] = DB["students"].get(id, {})
                obj["status"] = DB["grading_students"].get(
                    id, DEFAULT_GRADING_STATUS)
                ret.append(obj)
            resp.media = ret
        else:
            resp.media = {
                "students": list(DB["grading_students"].keys())
            }

# ---- /student/{id} ----
@falcon.before(Authorized)
class StudentRes(PublicRes):
    def on_put(self, req, resp, id, action):
        student: Student = Student(id)
        if not student.valid:
            resp.status = falcon.HTTP_NOT_FOUND
            resp.media = {
                "failure": "Student not found"
            }
            return
        if action == "ack":
            DB["grading_students"][student.student_id]["finished"] = True
        elif action == "grades":
            by = get_auth_key(req)
            if (student.student_id not in TEMPDB["lockdowns"]) or (TEMPDB["lockdowns"][student.student_id] != by):
                resp.status = falcon.HTTP_FORBIDDEN
                resp.media = {
                    "failure": "Object locked by other client" if (TEMPDB["lockdowns"][student.student_id] != by) else "Object not locked, lock first"
                }
                return
            data = readJSON(req)
            if data is None:
                resp.media = {
                    "failure": "Bad JSON format"
                }
                resp.status = falcon.HTTP_BAD_REQUEST
                return
            if DB["students"].get(student.student_id):
                if data.get("override") != True:
                    resp.media = {
                        "failure": "Grade already exists. Use override:true to override."
                    }
                    resp.status = falcon.HTTP_CONFLICT
            DB["students"][student.student_id] = data
            DB["grading_students"][student.student_id]["finished"] = True
            unlockStudent(student.student_id)
            resp.media = {}
        elif action == "skip":
            DB["grading_students"][student.student_id]["skipped"] = True
            resp.media = {}
        else:
            resp.media = {
                "failure": "Unrecognized action"
            }
            resp.status = falcon.HTTP_BAD_REQUEST

    def on_delete(self, req, resp, id, action):
        student: Student = Student(id)
        if not student.valid:
            resp.status = falcon.HTTP_NOT_FOUND
            resp.media = {
                "failure": "Student not found"
            }
            return
        if action == "grades":
            DB["students"][student.student_id] = {}
            DB["grading_students"][student.student_id]["finished"] = False
            resp.media = {}
        elif action == "skip":
            DB["grading_students"][student.student_id]["skipped"] = False
            resp.media = {}
        else:
            resp.media = {
                "failure": "Unrecognized action"
            }
            resp.status = falcon.HTTP_BAD_REQUEST

    def on_get(self, req, resp, id, action):
        student: Student = Student(id)
        if not student.valid:
            resp.status = falcon.HTTP_NOT_FOUND
            resp.media = {
                "failure": "Student not found"
            }
            return
        if action == "tar":
            by = get_auth_key(req)
            self.return_tar(student, resp, by)
        elif action == "info":
            self.return_info(student, resp)
        elif action == "grades":
            if student.student_id not in DB["students"]:
                resp.staticdb = falcon.HTTP_NOT_FOUND
                return
            resp.media = DB["students"][student.student_id]

        else:
            resp.media = {
                "failure": "Unrecognized action"
            }
            resp.status = falcon.HTTP_BAD_REQUEST

    @staticmethod
    def return_tar(student, resp, by):
        resp.stream = get_tar_result(os.path.join(
            config.SUBMISSION_DIR, student.student_id))
        resp.content_type = "application/x-tar"
        lockStudent(student.student_id, by)
        t = Timer(config.MUTEX_TIMEOUT,
                  lambda: unlockStudent(student.student_id))
        t.start()

    @staticmethod
    def return_info(student: Student, resp):
        retn = student.__dict__
        retn["graded"] = DB["grading_students"][student.student_id]
        retn["locked"] = student.student_id in TEMPDB["lockdowns"].keys()
        resp.media = retn

    on_post = on_get
