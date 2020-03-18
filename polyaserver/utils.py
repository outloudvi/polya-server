from polyaserver.staticdb import DB, TEMPDB
from polyaserver.internal_const import DEFAULT_GRADING_STATUS
import config
from polyaserver.classes import Student
from tempfile import NamedTemporaryFile
import tarfile
import os
import json


def valid_login(req):
    if req.auth is None:
        return False
    key = req.auth
    key_info = key.split(" ")
    return key_info[0] == "Bearer" and key_info[1] in DB["sessions"]


def read_next_ungraded_student():
    for _, id in enumerate(DB["grading_students"]):
        if DB["grading_students"][id]["finished"] == False and DB["grading_students"][id]["skipped"] == False and (id not in TEMPDB["lockdowns"]):
            return Student(id)
    return None


def get_tar_result(path):
    f = NamedTemporaryFile()
    tar = tarfile.open(f.name, "w")
    if os.path.isfile(path):
        # For regular file, just add it
        paths = path.split("/")
        tar.add(path, paths[-1])
    elif os.path.isdir(path):
        # For directory, add everything inside
        for item in os.listdir(path):
            tar.add(os.path.join(path, item), item)
    tar.close()
    return f


def readdir():
    for student_id in os.listdir(config.SUBMISSION_DIR):
        DB["grading_students"][student_id] = DEFAULT_GRADING_STATUS
    print("Searching dir {}, {} submissions found.".format(
        config.SUBMISSION_DIR, len(DB["grading_students"])))


def unlockStudent(sid):
    TEMPDB["lockdowns"].remove(sid)


def lockStudent(sid):
    TEMPDB["lockdowns"].append(sid)

def readJSON(req):
    data = req.stream.read(req.content_length or 0)
    try:
        ret = json.loads(data)
    except Exception as e:
        print(e)
        return None
    return ret