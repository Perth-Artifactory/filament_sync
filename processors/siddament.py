from pprint import pprint
import re
import sys
import const
import json
import time
import requests


def all(mapping=False, daemon=False) -> list:
    # Load the siddament.csv file
    with open("siddament.csv", "r", encoding="utf8") as f:
        # Read the file
        data = f.read()
    # Split the data by newlines
    data = data.split("\n")
    # Remove the header
    header = data.pop(0)
    # Create a list to store the filaments
    filaments = []

    # Construct a list of current filaments to avoid duplicates
    current_filament = []

    # Get the list of filament from spoolman
    with open("config.json", "r") as f:
        config = json.load(f)
    r = requests.get(f"{config['spoolman_url']}/filament")

    if r.status_code != 200:
        print("Failed to get filament list")
        sys.exit(1)

    for filament in r.json():
        if filament["vendor"]["name"] == "Siddament":
            current_filament.append(const.construct_spoolman_name(filament))

    print(f"Found {len(current_filament)} Siddament filaments in spoolman")

    # Iterate over the data
    for line in data:
        # Split the line by commas
        line = line.split(",")
        # Create a dictionary to store the filament details
        filament_raw = {}
        # Iterate over the header
        for i, key in enumerate(header.split(",")):
            # Add the key and value to the dictionary
            try:
                filament_raw[key] = line[i]
            except IndexError:
                pass

        # Decide if this line is a valid filament
        if "Filament" in filament_raw.get(
            "Collection", ""
        ) or "Filament" in filament_raw.get("Category", ""):

            # Some collections are duds
            if filament_raw.get("Collection", "") in [
                "3D Printer Bed Adhesion",
                " heat treatable PLA Filament which maintains strength and form at much higher temperatures than PLA",
            ]:
                continue

            # Check if the filament contains carbon fiber
            carbon = False
            cf_suffix = ""
            for search in ["Carbon Fiber", "CF"]:
                if search in filament_raw.get("Name", ""):
                    cf_suffix = "-CF"
                    carbon = True

            # Look for standard filament materials in the name
            # When adding new materials here make sure that substrings are later in the list
            material = "?"
            for search in [
                "ABS Pro",
                "PC-ABS",
                "ABS",
                "HTPLA",
                "PLA",
                "PETG",
                "TPU",
                "ASA",
                "Nylon",
            ]:
                if search in filament_raw.get("Name", ""):
                    material = search
                    break

            material += cf_suffix

            # Check weight
            weight = 1000
            if "kg" in filament_raw.get("Variant Name", "").lower():
                weight = (
                    float(filament_raw.get("Variant Name", "").lower().split("kg")[0])
                    * 1000
                )
            elif "g coil" in filament_raw.get("Variant Name", "").lower():
                weight = filament_raw.get("Variant Name", "").lower().split("g coil")[0]

            elif "g spool" in filament_raw.get("Variant Name", "").lower():
                weight = (
                    filament_raw.get("Variant Name", "").lower().split("g spool")[0]
                )

            # Try to guess colour from name
            colour_source = "string"
            colour = filament_raw.get("Name", "").lower()
            colour = colour.replace(material.lower(), "")
            for s in [
                material.lower(),
                "filament",
                "3d",
                "printer",
                "carbon fiber",
                "cf",
                "( cf)",
                "1kg",
                "()",
                "( )",
            ]:
                colour = colour.replace(s, "")
            colour = colour.replace("  ", " ")
            # If the colour starts and ends with quotes, remove them
            if colour[0] == '"' and colour[-1] == '"':
                colour = colour[1:-1]

            colour = colour.strip()
            colour = " ".join([word.capitalize() for word in colour.split(" ")])
            # Capitalise the first letter after any slashes
            if "/" in colour:
                colour = "/".join(
                    [word[0].upper() + word[1:] for word in colour.split("/")]
                )

            if '"' in colour:
                temp = ""
                apos = True
                for char in colour:
                    if char == '"':
                        apos = True
                        temp += char
                    elif apos:
                        apos = False
                        temp += char.upper()
                    else:
                        temp += char
                colour = temp

            for brand in ["Coext"]:
                colour = colour.replace(brand, brand.upper())

            # Search for hex codes in the description that aren't part of a html tag
            pattern1 = re.compile(r"HEX #([0-9a-fA-F]{6})", re.IGNORECASE)
            pattern2 = re.compile(r"(?<!color:)#([0-9a-fA-F]{6})", re.IGNORECASE)
            # See if pattern is in the body
            match = pattern1.search(filament_raw.get("Body", ""))
            if match:
                colour = match.group(1)
                colour_source = "hex"
            else:
                match = pattern2.search(filament_raw.get("Body", "").replace(" ", ""))
                if match:
                    colour = match.group(1)
                    colour_source = "hex"

            if colour == "":
                colour = None

            # load colour map from file
            with open("colour_map.json", "r") as f:
                colour_map = json.load(f)

            if isinstance(colour, str):
                if colour_source == "string" and colour.lower() in colour_map:
                    colour = colour_map[colour.lower()]
                    colour_source = "hex"

            pprint(filament_raw)

            if not material:
                sys.exit(1)

            try:
                weight = float(weight)
            except ValueError:
                if isinstance(weight, str):
                    weight = weight.replace("g", "")
                    weight = float(weight)

            if weight < 51:
                continue

            print(f"Is carbon: {carbon}")
            print(f"Material: {material}")
            print(f"Weight: {weight}g")
            print(f"Colour: {colour}")

            if mapping and colour_source == "string" and isinstance(colour, str):
                print(
                    f"In colour mapping mode and colour is '{colour}' which is not mapped or a hex code"
                )
                hex_s = input("Enter a hex code: ").lower()
                while not const.check_hex(hex_s):
                    print("Invalid")
                    hex_s = input("Enter a hex code: ").lower()
                colour_map[colour.lower()] = hex_s
                colour_source = "hex"
                colour = hex_s
                # Write to file
                with open("colour_map.json", "w") as f:
                    json.dump(colour_map, f, indent=4)

            # Validate that price is a number
            try:
                float(filament_raw.get("Price", ""))
            except ValueError:
                print(
                    f'Price is not a number: "{filament_raw.get("Price", "")}" - SKIPPED'
                )
                continue

            # Strip the material from the name
            name = filament_raw.get("Name", "")
            name = name.replace(material, "")
            name = name.strip()
            if name[-1] == "-":
                name = name[:-1]
                name = name.strip()

            # Create the filament
            filament = const.Filament(
                name=name,
                vendor_id=1,
                material=material,
                price=filament_raw.get("Price", ""),
                weight=weight,
                colour_hex=str(colour),
                diameter=1.75,
                density=1.25,
                url=filament_raw.get("URL", ""),
            )

            # ask if we should upload
            upload = True
            fake_spoolman = filament.formatted()
            fake_spoolman["vendor"] = {"name": "Siddament"}
            name = const.construct_spoolman_name(fake_spoolman)
            if name in current_filament:
                print(f"Filament '{name}' already exists in spoolman, skipping")
                continue
            else:
                print(f"Filament '{name}' not found in spoolman")

            if not mapping:
                if not daemon:
                    q = input("Upload? [y/N]: ")
                    if q == "y":
                        upload = filament.upload()
                        time.sleep(0.5)
                else:
                    upload = filament.upload()
                    time.sleep(0.5)

            if not upload:
                input()

            filaments.append(filament)

    return filaments
