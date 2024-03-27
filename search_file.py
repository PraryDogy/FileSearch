import json
from cfg import Cfg


raw = "Raw"
raw_premium = "Raw_Premium"

png = "Png"
png_premium = "Png_Premium"

ready = "Ready"
ready_premium = "Ready_Premium"

black_background = "Black Background"

templates = [
    "/" + i + "/"
    for i in (raw, raw_premium, png, png_premium, ready, ready_premium, black_background)
    ]


def search_file(article: str):

    with open(Cfg.catalog_json_dir, "r", encoding='utf-8') as json_file:
        data = json.loads(json_file.read())

    try:
        res = data[article]
        beaty_res = {}

        for temp in templates:
            for path in res:
                if temp in path:
                    beaty_res[temp.replace("/", "")] = path

        return beaty_res

    except KeyError:
        print("no file")

        return False
