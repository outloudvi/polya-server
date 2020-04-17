import csv
import json
import argparse
import os
from urllib.request import urlopen


def getfirststr(arr):
    return arr if type(arr) == str else arr[0]


def main():
    parser = argparse.ArgumentParser(
        description='Export the report of students.')
    parser.add_argument('--output', '-o', nargs=1, type=str,
                        default="reports", help='Output directory')
    parser.add_argument('--student', '-s', nargs='*', type=str,
                        help='Student ID for report exporting')
    parser.add_argument('--server-port', '-p', nargs=1, type=int,
                        default=8000, help='Port of the server')
    parser.add_argument('--all', '-a', action='store_true',
                        help='Export the result for all students')

    args = parser.parse_args()

    host = "http://127.0.0.1:{}".format(args.server_port[0])

    studentIds = args.student or []
    if args.all:
        resp = urlopen("{}/students".format(host)
                       ).read().decode()
        studentIds = json.loads(resp)["students"]
    for i in studentIds:
        basePath = getfirststr(args.output)
        if not os.access(basePath, os.W_OK):
            os.mkdir(basePath)
        result = urlopen(
            "{}/admin/report?id={}".format(host, i)).read().decode()
        with open(os.path.join(getfirststr(args.output), i), 'w', newline='') as file:
            file.write(result)
    print("Done")


if __name__ == "__main__":
    main()
