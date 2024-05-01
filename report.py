import json
import sys
from pprint import pprint

import requests
from tabulate import tabulate
import argparse


def format_weight(weight: int | str) -> str:
    weight = int(weight)
    if weight < 999:
        return f"{weight}g"
    return f"{weight / 1000}kg"


parser = argparse.ArgumentParser(description="Generate a report of spools")
parser.add_argument("output", type=str, nargs="?", help="The output file")
args = parser.parse_args()

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# Check whether spoolman is up
r = requests.get(f"{config['spoolman_url']}/info")
if r.status_code != 200:
    print("Failed to connect to spoolman")
    sys.exit(1)

print(f"Connected to spoolman with version {r.json()['version']}")

# get a full list of filaments
r = requests.get(f"{config['spoolman_url']}/filament")
filaments = r.json()

print(f"Found {len(filaments)} filaments")

# get a list of current spools
r = requests.get(f"{config['spoolman_url']}/spool")
spools = r.json()

print(f"Found {len(spools)} spools")

materials = {}

# Split spools up into materials
for spool in spools:
    if spool["archived"]:
        continue

    if spool["filament"]["material"] not in materials:
        materials[spool["filament"]["material"]] = []
    materials[spool["filament"]["material"]].append(spool)

print("--------------------------")
outfile_contents = []

for material in materials:
    outfile_contents.append(f"## {material}\n")

    outfile_contents.append(f"* Spools: {len(materials[material])}")
    weight = 0
    for spool in materials[material]:
        weight += spool["remaining_weight"]
    outfile_contents.append(f"* Total weight: {format_weight(weight)}")
    outfile_contents.append("")

    # Split spools into names
    spool_names = {}
    for spool in materials[material]:
        # construct a name
        name = f'{spool["filament"]["name"]} ({spool["filament"]["vendor"]["name"]})'
        colour = spool["filament"].get("color_hex", "ffffff")
        if name not in spool_names:
            spool_names[name] = {
                "spools": [],
                "weight": 0,
                "colour": colour,
                "url": spool["filament"].get("extra", {"url": ""}).get("url", ""),
            }
        spool_names[name]["spools"].append(spool["remaining_weight"])
        spool_names[name]["weight"] += spool["remaining_weight"]

    table_data = []
    table_data.append(["Name", "Spools", "Total left", "Individual left", "Colour"])
    for name in spool_names:
        individual = ""
        for spool in spool_names[name]["spools"]:
            individual += f"{format_weight(spool)}, "

        individual = individual[:-2]

        table_data.append(
            [
                f'[{name}]({spool_names[name]["url"]})',
                len(spool_names[name]["spools"]),
                f'{format_weight(spool_names[name]["weight"])}',
                individual,
                f'<span style="color:#{spool_names[name]["colour"]}">■</span>',
            ]
        )

    table = tabulate(table_data, headers="firstrow", tablefmt="pipe")

    outfile_contents.append(table)

    outfile_contents.append("")

if args.output:
    with open(args.output, "w") as f:
        f.write("\n".join(outfile_contents))
        print(f"Report written to {args.output}")
else:
    print("\n".join(outfile_contents))