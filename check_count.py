#!/usr/bin/env python3
"""Check why issue count changed after reprocessing."""
import json, glob

total = 0
keys = set()
not_done = 0
no_transition = 0
for f in sorted(glob.glob("raw_search_*.json")):
    data = json.load(open(f))
    for iss in data.get("issues", []):
        k = iss["key"]
        if k in keys:
            continue
        keys.add(k)
        total += 1
        status = iss.get("status", {}).get("name", "")
        if status != "Done":
            not_done += 1
            continue
        has_ip = False
        has_done = False
        for cl in iss.get("changelogs", []):
            for item in cl.get("items", []):
                if item.get("field") == "status":
                    if item.get("to_string") == "In Progress":
                        has_ip = True
                    if item.get("to_string") == "Done":
                        has_done = True
        if not has_ip or not has_done:
            no_transition += 1

print(f"Total unique issues in raw_search: {total}")
print(f"Not Done status: {not_done}")
print(f"Missing IP or Done transition: {no_transition}")
print(f"Valid (expected): {total - not_done - no_transition}")

# Check the old data
old = json.load(open("issue_data_full.json"))
print(f"\nCurrent issue_data_full.json: {len(old)} issues")

# Check which keys are in old but not new
old_keys = set(old.keys())
raw_done_keys = set()
for f in sorted(glob.glob("raw_search_*.json")):
    data = json.load(open(f))
    for iss in data.get("issues", []):
        if iss.get("status", {}).get("name") == "Done":
            raw_done_keys.add(iss["key"])

missing = old_keys - raw_done_keys
if missing:
    print(f"\nKeys in old data but not in raw_search Done issues: {len(missing)}")
    for k in sorted(missing)[:10]:
        print(f"  {k}")
