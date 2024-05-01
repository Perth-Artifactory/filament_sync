from processors import siddament
from pprint import pprint
import json
import requests
import sys

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# Check whether spoolman is up
r = requests.get(f"{config['spoolman_url']}/info")
if r.status_code != 200:
    print("Failed to connect to spoolman")
    sys.exit(1)
spoolman_info = r.json()
if "version" not in spoolman_info:
    print("Failed to connect to spoolman")
    sys.exit(1)

print(f"Connected to spoolman, version is: {spoolman_info['version']}")

# Check for colour map and daemon modes
mapping = False
daemon = False
if "-map" in sys.argv:
    mapping = True
    print("Colour mapping mode enabled. No uploads, only mapping")
if "-d" in sys.argv:
    print("Daemon mode enabled. No prompts")
    daemon = True

processors = [siddament]

filaments = []

# iterate over processors
for processor in processors:
    filaments += processor.all(mapping=mapping, daemon=daemon)
