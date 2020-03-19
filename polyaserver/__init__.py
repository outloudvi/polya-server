from signal import signal, SIGINT
import falcon

from polyaserver.staticdb import DB, TEMPDB
from polyaserver.resources import AuthRes, RevokeRes, ConfigRes, ImageRes, NextRes, StudentListRes, StudentRes, InfoRes, SaveRes
from polyaserver.classes import Student
from polyaserver.hooks import Authorized
from polyaserver.db import savedata, loaddata
from polyaserver.utils import read_next_ungraded_student, get_tar_result, readdir, unlockStudent, lockStudent


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
api.add_route("/save", SaveRes())
api.add_route("/", InfoRes())
