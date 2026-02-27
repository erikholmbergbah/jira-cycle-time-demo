#!/usr/bin/env python3
"""Append keys from stdin JSON to sp_keys.json"""
import json, sys

data = json.load(sys.stdin)
issues = data.get('issues', []) if isinstance(data, dict) else data
new_keys = [i['key'] for i in issues if isinstance(i, dict) and 'key' in i]

with open('sp_keys.json') as f:
    existing = json.load(f)

merged = sorted(set(existing + new_keys))
with open('sp_keys.json', 'w') as f:
    json.dump(merged, f)

print(f"+{len(new_keys)} keys, total: {len(merged)}")
