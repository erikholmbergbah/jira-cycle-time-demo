#!/usr/bin/env python3
"""
Collect all SP keys from a content.json file (MCP search result).
Usage: python3 collect_all_sp.py <content_json_path>
Extracts issue keys and appends them to sp_keys.json
"""
import json, sys

content_path = sys.argv[1]
with open(content_path) as f:
    data = json.load(f)

# Extract keys from the search result
new_keys = []
if isinstance(data, list):
    for item in data:
        if isinstance(item, dict) and 'key' in item:
            new_keys.append(item['key'])
elif isinstance(data, dict):
    if 'issues' in data:
        for item in data['issues']:
            new_keys.append(item['key'])
    elif 'key' in data:
        new_keys.append(data['key'])

# Load existing and merge
try:
    with open('sp_keys.json') as f:
        existing = json.load(f)
except:
    existing = []

merged = sorted(set(existing + new_keys))
with open('sp_keys.json', 'w') as f:
    json.dump(merged, f)

print(f"New: {len(new_keys)}, Total: {len(merged)}")
