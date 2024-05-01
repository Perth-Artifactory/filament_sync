import json
import requests


class Filament:
    def __init__(
        self,
        name: str = "",
        vendor_id: int = -1,
        material: str = "UNKNOWN",
        price: float | int = 0,
        density: float | int = 999999,
        diameter: float | int = 1.75,
        weight: float | int = 0,
        spool_weight: float | int = 0,
        article_number: str = "",
        comment: str = "",
        settings_extruder_temp: int = -1,
        settings_bed_temp: int = -1,
        color_hex: str = "FFFFFF",
    ):
        if 0 < len(name) <= 64:
            self.name = name
        if vendor_id >= 0:
            self.vendor_id = vendor_id
        if 0 < len(material) <= 64:
            self.material = material
            if material not in ["PLA", "ABS", "PETG", "TPU", "Nylon", "PC", "PVA"]:
                raise ValueError(f"Invalid material {material}")
        if float(price) > 0:
            self.price = float(price)
        if density > 0:
            self.density = density
        if diameter > 0:
            self.diameter = diameter
        if weight > 0:
            self.weight = weight
        if spool_weight > 0:
            self.spool_weight = spool_weight
        if 0 < len(article_number) <= 64:
            self.article_number = article_number
        if 0 < len(comment) <= 1024:
            self.comment = comment
        if settings_extruder_temp >= 0:
            self.settings_extruder_temp = settings_extruder_temp
        if settings_bed_temp >= 0:
            self.settings_bed_temp = settings_bed_temp

        # Check if the color is a valid hex color
        if color_hex != "":
            # strip the # if it is present
            if color_hex[0] == "#":
                color_hex = color_hex[1:]
            # check the length
            if len(color_hex) != 6:
                raise ValueError("Invalid color (length)")
            # check that all characters are hex
            if not all(c in "0123456789ABCDEF" for c in color_hex):
                raise ValueError("Invalid color (not hex)")
            if len(color_hex) != 6:
                raise ValueError("Invalid color (length)")
            self.color_hex = color_hex

    def formatted(self) -> dict:
        details = {}
        if hasattr(self, "name"):
            details["name"] = self.name
        if hasattr(self, "vendor_id"):
            details["vendor_id"] = self.vendor_id
        if hasattr(self, "material"):
            details["material"] = self.material
        if hasattr(self, "price"):
            details["price"] = self.price
        if hasattr(self, "density"):
            details["density"] = self.density
        else:
            raise ValueError("Required field not set (density)")
        if hasattr(self, "diameter"):
            details["diameter"] = self.diameter
        else:
            raise ValueError("Required field not set (diameter)")
        if hasattr(self, "weight"):
            details["weight"] = self.weight
        if hasattr(self, "spool_weight"):
            details["spool_weight"] = self.spool_weight
        if hasattr(self, "article_number"):
            details["article_number"] = self.article_number
        if hasattr(self, "comment"):
            details["comment"] = self.comment
        if hasattr(self, "settings_extruder_temp"):
            details["settings_extruder_temp"] = self.settings_extruder_temp
        if hasattr(self, "settings_bed_temp"):
            details["settings_bed_temp"] = self.settings_bed_temp
        if hasattr(self, "color_hex"):
            details["color_hex"] = self.color_hex

        return details

    def upload(self):
        # Get the spoolman credentials
        with open("config.json", "r") as f:
            config: dict = json.load(f)

        # Send data to spoolman
        r = requests.post(f"{config['spoolman_url']}/filament", json=self.formatted())
        print(r.status_code)
