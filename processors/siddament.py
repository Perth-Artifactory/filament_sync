from pprint import pprint
import re
import sys
import const


def all() -> list:
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

            pprint(filament_raw)

            if not material:
                sys.exit(1)

            if weight < 51:
                continue

            print(f"Is carbon: {carbon}")
            print(f"Material: {material}")
            print(f"Weight: {weight}g")
            print(f"Colour: {colour}")

            fin = input("Quit? (q): ")
            if fin == "q":
                return filaments

            # Create the filament
            filament = const.Filament(
                name=filament_raw.get("Name", ""),
                vendor_id=1,
                material=material,
                price=filament_raw.get("Price", ""),
                weight=weight,
                colour_hex=str(colour),
                diameter=1.75,
                density=1.25,
            )

            # ask if we should upload
            q = input("Upload? [y/N]: ")
            if q == "y":
                filament.upload()

            filaments.append(filament)

    return filaments
