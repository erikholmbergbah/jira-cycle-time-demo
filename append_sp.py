#!/usr/bin/env python3
"""Append SP keys from inline JSON result.
Usage: echo '<json>' | python3 append_sp.py
"""
import json, sys, os

raw = json.loads(sys.stdin.read())
if isinstance(raw, str):
    raw = json.loads(raw)

# Handle MCP wrapper
if 'result' in raw:
    r = raw['result']
    raw = json.loads(r) if isinstance(r, str) else r

found = [i['key'] for i in raw.get('issues', [])]

sp_file = 'sp_keys.json'
existing = json.load(open(sp_file)) if os.path.exists(sp_file) else []
merged = sorted(set(existing + found))
json.dump(merged, open(sp_file, 'w'))
print(f'+{len(found)} keys. Total unique: {len(merged)}')
