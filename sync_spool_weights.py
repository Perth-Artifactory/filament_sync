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

for filament in filaments:
    # Skip specific vendors
    if filament["vendor"]["name"] in ["Siddament"]:
        continue

    # Check if there's already a spool weight set
    if filament.get("spool_weight", 0) > 0:
        continue

    # Check if this vendor has a stored spool weight
    spool_weight = filament["vendor"].get("extra", {}).get("default_spool_weight", 0)
    if spool_weight == 0:
        continue

    new_info = {}
    new_info["spool_weight"] = spool_weight

    print(const.construct_spoolman_name(filament))
    pprint(new_info)
    # Write updated data back to spoolman
    r = requests.patch(
        f"{config['spoolman_url']}/filament/{filament['id']}", json=new_info
    )
    input()
