from signal import signal, SIGINT, SIGTERM
import falcon
import time

from polyaserver.db import DB, TEMPDB
from polyaserver.resources import AuthRes, RevokeRes, ConfigRes, ImageRes, NextRes, StudentListRes, StudentRes, InfoRes, SaveRes, RawRes, AdminRes
from polyaserver.classes import Student
from polyaserver.hooks import Authorized
from polyaserver.db import savedata, loaddata
from polyaserver.utils import read_next_ungraded_student, get_tar_result, readdir, unlockStudent, lockStudent

sigTermOn = False

def SigtermHandler(signal_received, frame):
    global sigTermOn
    if sigTermOn:
        return
    sigTermOn = True
    print("Saving data to db...")
    conn = savedata()
    conn.close()
    print("Connection closed")
    exit(0)


readdir()
signal(SIGTERM, SigtermHandler)
api = falcon.API()
api.add_route("/register", AuthRes())
api.add_route("/revoke", RevokeRes())
api.add_route("/config", ConfigRes())
api.add_route("/image.sfs", ImageRes())
api.add_route("/next", NextRes())
api.add_route("/students", StudentListRes())
api.add_route("/student/{id}/{action}", StudentRes())
api.add_route("/save", SaveRes())
api.add_route("/raw/{action}", RawRes())
api.add_route("/admin/{action}", AdminRes())
api.add_route("/", InfoRes())
