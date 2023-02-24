#!/bin/python3

from pprint import pprint
import json

final = {}

with open("raw.txt", "r") as txt:
    for line in txt.readlines():
        line = line.strip()
        key = line.replace('.', '_').replace('-', '_dash_')
        if key[0] in "0123456789":
            key = '_' + key
        final[key] = line

with open("export.json", "w") as exporter:
    json.dump(final, exporter, indent=4)

# pprint(final)