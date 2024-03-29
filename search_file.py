import json
from cfg import Cfg
from collections import defaultdict, OrderedDict
import os


# ready = "Ready"
# ready_premium = "Ready_Premium"

# black_background = "Black Background"

# templates = [
#     "/" + i + "/"
#     for i in (raw, raw_premium, png, png_premium, ready, ready_premium, black_background)
#     ]


templates = {
    "/RAW/": "Исходник",
    "/Raw_Premium/": "Исходник",
    "/Png/": "PNG",
    "/Png_Premium/": "PNG",
    "/Ready/": "Послойник",
    "/Ready_Premium/": "Послойник",
    }


def search_file(article: str):

    with open(Cfg.catalog_json_file, "r", encoding='utf-8') as json_file:
        data: dict = json.loads(json_file.read())

    try:
        beaty_res = [
            x
            for art, src_list in data.items()
            for x in src_list
            if article in x
            ]

        beaty_res = [
            [
                f"{templates[tmp]}: {src.split(os.sep)[-1]}",
                src
                ]
            for tmp in templates
            for src in beaty_res
            if tmp in src
            ]

        return beaty_res

    except KeyError:
        print("no file")

        return False
