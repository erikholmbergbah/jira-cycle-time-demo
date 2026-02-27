#!/usr/bin/env python3
"""Collect story point values from sp_raw_*.json files and build key->SP mapping."""
import json, glob, os

BASE = os.path.dirname(os.path.abspath(__file__))
sp_map = {}

for f in sorted(glob.glob(os.path.join(BASE, "sp_raw_*.json"))):
    data = json.load(open(f))
    for issue in data["issues"]:
        key = issue["key"]
        sp = issue.get("customfield_10100", {})
        if sp and "value" in sp:
            sp_map[key] = sp["value"]

out = os.path.join(BASE, "sp_values.json")
with open(out, "w") as fh:
    json.dump(sp_map, fh, indent=2)
print(f"Saved {len(sp_map)} key->SP mappings to {out}")
