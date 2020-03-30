import csv
import json
import argparse
from urllib.request import urlopen


def getfirststr(arr):
    return arr if type(arr) == str else arr[0]


def main():
    parser = argparse.ArgumentParser(
        description='Export the grades to CSV file.')
    parser.add_argument('--output', '-o', nargs=1, type=str,
                        default="grades.csv", help='Output file path')
    parser.add_argument('--server-port', '-p', nargs=1, type=int,
                        default=8000, help='Port of the server')

    args = parser.parse_args()

    result = urlopen(
        "http://127.0.0.1:{}/admin/export".format(args.server_port)).read().decode()
    with open(getfirststr(args.output), 'w', newline='') as csvfile:
        csvfile.write(result)
    print("Done")


if __name__ == "__main__":
    main()
