import json
from cfg import Cfg
import os


templates = {
    "/RAW/": "Исходник",
    "/Raw_Premium/": "Исходник",
    "/Png/": "PNG",
    "/Png_Premium/": "PNG",
    "/Ready/": "Послойник",
    "/Ready_Premium/": "Послойник",
    }


def catalog_search_file(article: str):

    data = Cfg.read_catalog_json_file()

    try:
        result = [
            x
            for art, src_list in data.items()
            for x in src_list
            if article in x
            ]

        result = [
            [
                f"{templates[tmp]}: {src.split(os.sep)[-1]}",
                src
                ]
            for tmp in templates
            for src in result
            if tmp in src
            ]

        return result

    except KeyError:
        print("no file")

        return False
