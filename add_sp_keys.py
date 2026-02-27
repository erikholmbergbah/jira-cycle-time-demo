#!/usr/bin/env python3
"""Extract keys from MCP search result and append to sp_keys.json.
Usage: python3 add_sp_keys.py <content_json_path> <batch_num>
     or: python3 add_sp_keys.py --inline '{"result":"..."}' <batch_num>
"""
import json, sys, os

SP_FILE = 'sp_keys.json'

def extract_keys(data):
    if isinstance(data, str):
        data = json.loads(data)
    if 'result' in data:
        r = data['result']
        data = json.loads(r) if isinstance(r, str) else r
    return [i['key'] for i in data.get('issues', [])]

def merge_and_save(new_keys, batch_num):
    existing = json.load(open(SP_FILE)) if os.path.exists(SP_FILE) else []
    merged = sorted(set(existing + new_keys))
    json.dump(merged, open(SP_FILE, 'w'))
    print(f'Batch {batch_num}: +{len(new_keys)} keys with SP. Total: {len(merged)}')

if sys.argv[1] == '--inline':
    data = json.loads(sys.argv[2])
    batch_num = sys.argv[3]
else:
    data = json.load(open(sys.argv[1]))
    batch_num = sys.argv[2]

keys = extract_keys(data)
merge_and_save(keys, batch_num)
