#!/usr/bin/env python3
"""Build sp_values.json from sp_page_*.json files."""
import json, glob, os

BASE = os.path.dirname(os.path.abspath(__file__))
sp_map = {}

for f in sorted(glob.glob(os.path.join(BASE, "sp_page_*.json"))):
    data = json.load(open(f))
    for issue in data:
        sp_map[issue["key"]] = issue["sp"]

out = os.path.join(BASE, "sp_values.json")
with open(out, "w") as fh:
    json.dump(sp_map, fh, indent=2)
print(f"Saved {len(sp_map)} key->SP mappings to {out}")
