import argparse
import json
import re
import sys
from pprint import pprint

import requests

import const

# load config
with open("config.json", "r") as f:
    config = json.load(f)

# get a list of filaments
r = requests.get(f"{config['spoolman_url']}/filament")
filaments = r.json()

if r.status_code != 200:
    print("Failed to get filament list")
    sys.exit(1)

print(f"Found {len(filaments)} filaments")

# CHANGE SEARCH PATTERN HERE
name_filter = re.compile(r"Translucent (.*)")
for filament in filaments:
    new_info = {}
    match = name_filter.match(filament["name"])
    if match:
        print(f"{filament['name']} matches filter")

        new_info["name"] = match.group(1)
        new_info["material"] = f'{filament["material"]} (Translucent)'

        pprint(new_info)

        # Write updated data back to spoolman
        r = requests.patch(
            f"{config['spoolman_url']}/filament/{filament['id']}", json=new_info
        )
        input()
