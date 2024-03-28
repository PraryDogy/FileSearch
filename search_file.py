import json
from cfg import Cfg
from collections import defaultdict, OrderedDict

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
        data: dict = json.loads(json_file.read())

    try:
        beaty_res = [
            x
            for art, src_list in data.items()
            for x in src_list
            if article in x
            ]

        beaty_res = {
            f"{src.split('/')[-1]}": src
            for tmp in templates
            for src in beaty_res
            if tmp in src
            }

        return OrderedDict(sorted(beaty_res.items()))

    except KeyError:
        print("no file")

        return False
