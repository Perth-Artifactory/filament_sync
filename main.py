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

processors = [siddament]

filaments = []

# iterate over processors
for processor in processors:
    filaments += processor.all()
