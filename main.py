from processors import siddament
from pprint import pprint
import json
import requests


# Load config
with open("config.json", "r") as f:
    config = json.load(f)

# Check whether spoolman is up
r = requests.get(f"{config['spoolman_url']}/info")
print(f"Connected to spoolman, version is: {r.json()['version']}")

processors = [siddament]

filaments = []

# iterate over processors
for processor in processors:
    filaments += processor.all()
