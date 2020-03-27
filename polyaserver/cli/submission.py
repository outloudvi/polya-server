import csv
import json
import argparse
from urllib.request import urlopen

def getfirststr(arr):
    return arr if type(arr) == str else arr[0]


def main():
    parser = argparse.ArgumentParser(
        description='Submission management')
    parser.add_argument('--unlock', '-u', nargs='*', type=str,
                        help='Unlock submissions')
    parser.add_argument('--unlock-all', action='store_true',
                        help='Unlock submissions')
    parser.add_argument('--server-port', '-p', nargs=1, type=int,
                        default=8000, help='Port of the server')

    args = parser.parse_args()

    if args.unlock:
        urlopen("http://127.0.0.1:{}/admin/unlock".format(args.server_port), data=json.dumps({
            "students": args.unlock
        }))
    elif args.unlock_all:
        urlopen("http://127.0.0.1:{}/admin/unlock_all".format(args.server_port), data=b"")

    print("Done")


if __name__ == "__main__":
    main()
