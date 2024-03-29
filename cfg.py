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

    catalog_json_file = os.path.join(
        app_dir,
        "catalog.json"
        )

    cfg_json_file = os.path.join(
        app_dir,
        "cfg.json"
        )
    
    images_dir = None

    @staticmethod
    def check():
        os.makedirs(Cfg.app_dir, exist_ok=True)

        if not os.path.exists(Cfg.catalog_json_file):
            shutil.copy2("catalog.json", Cfg.catalog_json_file)

        if not os.path.exists(Cfg.cfg_json_file):
            shutil.copy2("cfg.json", Cfg.cfg_json_file)

        data = Cfg.read_cfg_json_file()

        try:
            data["images_dir"] = Cfg.images_dir
        except Exception as e:
            ...




        #     data["images_dir"] = Cfg.images_dir

        # if type(Cfg.data) != dict:
        #     shutil.copy2("cfg.json", Cfg.cfg_json_dir)
        #     with open(Cfg.cfg_json_dir, "r", encoding="utf=8") as file:
        #         Cfg.data = json.load(file)

        # if "first" not in Cfg.data:
        #     Cfg.data["first"] = True



    @staticmethod
    def read_cfg_json_file() -> dict:
        with open(Cfg.cfg_json_file, "r", encoding="utf=8") as file:
            return json.load(file)
        
    @staticmethod
    def write_cfg_json_file():
        with open(Cfg.cfg_json_file, "w", encoding="utf=8") as file:
            json.dump(Cfg.data, file, ensure_ascii=False, indent=2)

    @staticmethod
    def read_catalog_json_file(self) -> dict:
        with open(Cfg.catalog_json_file, "r", encoding='utf-8') as json_file:
            return json.loads(json_file.read())
        
    @staticmethod
    def write_catalog_json_file(new_data: dict):
        with open(Cfg.catalog_json_file, "w", encoding="utf=8") as file:
            json.dump(new_data, file, ensure_ascii=False, indent=2)
