#!/usr/bin/env python3
"""Collect keys with story points from search results.
Usage: python3 collect_sp_keys.py <content_json_path>
Appends found keys to sp_keys.json
"""
import json, sys, os

content_path = sys.argv[1]
c = json.load(open(content_path))
r = c.get('result', c)
d = json.loads(r) if isinstance(r, str) else r

found_keys = [issue['key'] for issue in d.get('issues', [])]

sp_file = 'sp_keys.json'
existing = json.load(open(sp_file)) if os.path.exists(sp_file) else []
existing.extend(found_keys)
json.dump(sorted(set(existing)), open(sp_file, 'w'))
print(f'+{len(found_keys)} keys with SP. Total: {len(set(existing))}')
