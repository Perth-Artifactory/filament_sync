import argparse
import json
import re
import sys
from pprint import pprint

import requests

import const

# Specify ID of filament to duplicate
master_id = 371
changes = [
    {"name": "Natural", "color_hex": "c7c9aa"},
    {"name": "Black", "color_hex": "000000"},
]

# load config
with open("config.json", "r") as f:
    config = json.load(f)

# get a list of filaments
r = requests.get(f"{config['spoolman_url']}/filament/{master_id}")
filament = r.json()

if r.status_code != 200:
    print("Failed to get original filament")
    sys.exit(1)

print("Original filament:")
pprint(filament)

# Replace the vendor info with the vendor ID
vendor_id = filament.get("vendor", {}).get("id", None)
if vendor_id:
    filament["vendor_id"] = vendor_id
    filament.pop("vendor")

# Remove the ID and registered fields
filament.pop("id")
filament.pop("registered")

for change in changes:
    new_filament = filament.copy()
    if change == "extra":
        if not filament.get("extra"):
            new_filament["extra"] = change["extra"]
        else:
            new_filament["extra"].update(change["extra"])
    else:
        new_filament.update(change)

    print("New filament:")
    pprint(new_filament)
    input()
    # Write new filament to spoolman
    r = requests.post(f"{config['spoolman_url']}/filament", json=new_filament)
