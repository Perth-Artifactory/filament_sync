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
parser.add_argument("--wiki", action="store_true", help="Write to configured wiki page")
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

# Load a list of shipments
with open("upcoming_shipments.json", "r") as f:
    shipments = json.load(f)

print(
    f"Found {len(shipments)} shipments with {sum([len(s['items']) for s in shipments])} items"
)

# Iterate over filament and spools to find out which need restocking
restock = []
restocking = []
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
            for shipment in shipments:
                for item in shipments[shipment]:
                    if item == filament["id"]:
                        restocking.append((filament, shipment))
            restock.append((filament, total_weight))

restock_table_data = []
restock_table_data.append(["Filament", "Weight Left", "Tier", "Spool cost"])
for filament, weight in restock:
    restock_table_data.append(
        [
            const.construct_spoolman_name(filament, link=True),
            weight,
            filament.get("extra", {"tier": 0}).get("tier", 0),
            f'${filament.get("price", 0)}',
        ]
    )

restock_table_data.append(
    [
        "",
        "",
        "",
        f'${round(sum([filament.get("price", 0) for filament, weight in restock]))}',
    ]
)

restock_table = tabulate(restock_table_data, headers="firstrow", tablefmt="pipe")

stocking_table_data = []
stocking_table_data.append(["Filament", "Shipment"])
for filament, shipment in restocking:
    stocking_table_data.append(
        [const.construct_spoolman_name(filament, link=True), shipment]
    )

stocking_table = tabulate(stocking_table_data, headers="firstrow", tablefmt="pipe")

out = f"""## Filament needing restock

{restock_table}

## Filament being restocked

{stocking_table}

---
"""

if args.outfile:
    with open(args.outfile, "w") as f:
        f.write(out)
        print(f"Report written to {args.outfile}")

if args.wiki:
    import wiki

    wiki.write(
        content=out,
        id=config["report_ids"]["restock"],
        timestamp=True,
        force=False,
    )

if not args.outfile and not args.wiki:
    print(out)
