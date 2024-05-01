import argparse
import requests
import json
import sys
from pprint import pprint

parser = argparse.ArgumentParser(description="Purge filament for specific vendor")
parser.add_argument("--id", type=int, help="The id of the filament")
args = parser.parse_args()
if not args.id:
    print("No vendor id provided")
    sys.exit(1)


# load config
with open("config.json", "r") as f:
    config = json.load(f)

# get a list of filaments
r = requests.get(f"{config['spoolman_url']}/filament", json={"vendor_id": args.id})
filaments = r.json()

if r.status_code != 200:
    print("Failed to get filament list")
    sys.exit(1)

print(f"Found {len(filaments)} filaments for vendor {filaments[0]['vendor']['name']}")
d = input("Delete? (y/N)")
if d != "y":
    sys.exit(0)
else:
    for filament in filaments:
        r = requests.delete(f"{config['spoolman_url']}/filament/{filament['id']}")
        if r.status_code != 200:
            print(f"Failed to delete filament {filament['id']}")
            pprint(filament)
            sys.exit(1)
