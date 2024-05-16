import requests
import json
from pprint import pprint
import argparse
import sys
from tabulate import tabulate
import const

parser = argparse.ArgumentParser(
    description="Generate a report of spools that need restocking"
)
parser.add_argument("outfile", type=str, nargs="?", help="The output file")
parser.add_argument("wiki", type=bool, nargs="?", help="Write to configured wiki page")
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

# Get a list of filaments
r = requests.get(f"{config['spoolman_url']}/filament")
filaments = r.json()

if r.status_code != 200:
    print("Failed to get filament list")
    sys.exit(1)

print(f"Found {len(filaments)} filaments")

# Get a list of spools
r = requests.get(f"{config['spoolman_url']}/spool")
spools = r.json()

if r.status_code != 200:
    print("Failed to get spool list")
    sys.exit(1)

print(f"Found {len(spools)} spools")

# Iterate over filament and spools to find out which need restocking
restock = []
for filament in filaments:
    if filament["extra"].get("restock") == "true":
        # Look for active spools of this filament
        active_spools = [
            spool
            for spool in spools
            if spool["filament"]["id"] == filament["id"] and not spool["archived"]
        ]
        # Get the total weight of all active spools
        if len(active_spools) == 0:
            total_weight = 0
        else:
            total_weight = sum([spool["remaining_weight"] for spool in active_spools])
        # If the total weight is less than the threshold, add to restock list
        if total_weight < 300:
            restock.append((filament, total_weight))

table_data = []
table_data.append(["Filament", "Weight Left", "Tier", "Spool cost"])
for filament, weight in restock:
    table_data.append(
        [
            const.construct_spoolman_name(filament, link=True),
            weight,
            filament.get("extra", {"tier": 0}).get("tier", 0),
            f'${filament.get("price", 0)}',
        ]
    )

table_data.append(
    [
        "",
        "",
        "",
        f'${round(sum([filament.get("price", 0) for filament, weight in restock]))}',
    ]
)

if args.outfile:
    with open(args.outfile, "w") as f:
        f.write(tabulate(table_data, headers="firstrow", tablefmt="pipe"))
        print(f"Report written to {args.outfile}")

if args.wiki:
    import wiki

    wiki.write(
        content=tabulate(table_data, headers="firstrow", tablefmt="pipe") + "\n---\n",
        id=config["report_ids"]["restock"],
        timestamp=True,
        force=True,
    )

if not args.outfile and not args.wiki:
    print(tabulate(table_data, headers="firstrow", tablefmt="pipe"))
