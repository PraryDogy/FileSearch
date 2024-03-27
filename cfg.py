import json
import os
import shutil

class Cfg:
    app_name = "MiuzCatSearch"
    app_ver = "1.0.1"

    home_dir = os.path.expanduser("~")

    app_dir = os.path.join(
        home_dir,
        "Library",
        "Application Support",
        app_name,
        )

    catalog_json_dir = os.path.join(
        app_dir,
        "catalog.json"
        )

    cfg_json_dir = os.path.join(
        app_dir,
        "cfg.json"
        )
    
    data = None

    @staticmethod
    def check():
        os.makedirs(Cfg.app_dir, exist_ok=True)

        if not os.path.exists(Cfg.catalog_json_dir):
            shutil.copy2("catalog.json", Cfg.catalog_json_dir)

        if not os.path.exists(Cfg.cfg_json_dir):
            shutil.copy2("cfg.json", Cfg.cfg_json_dir)

        with open(Cfg.cfg_json_dir, "r", encoding="utf=8") as file:
            Cfg.data = json.load(file)

        if type(Cfg.data) != dict:
            shutil.copy2("cfg.json", Cfg.cfg_json_dir)
            with open(Cfg.cfg_json_dir, "r", encoding="utf=8") as file:
                Cfg.data = json.load(file)

        if "first" not in Cfg.data:
            Cfg.data["first"] = True