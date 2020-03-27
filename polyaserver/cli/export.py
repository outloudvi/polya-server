import csv
import json
import argparse


DBNAME = "db.json"


def getfirststr(arr):
    return arr if type(arr) == str else arr[0]


def main():
    parser = argparse.ArgumentParser(
        description='Export the grades to CSV file.')
    parser.add_argument('--db', '-d', nargs=1, type=str,
                        default="db.json", help='Database file path')
    parser.add_argument('--output', '-o', nargs=1, type=str,
                        default="grades.csv", help='Output file path')

    args = parser.parse_args()

    try:
        db = json.load(open(getfirststr(args.db)))
    except Exception as e:
        print("Error reading database:", e)
        exit(1)
    resultList = db.get("students", {})
    with open(getfirststr(args.output), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile,
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for key in resultList:
            score = resultList[key].get("graded")
            writer.writerow([key, score or 0])
    print("Done")


if __name__ == "__main__":
    main()
