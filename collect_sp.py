#!/usr/bin/env python3
"""
Collect all Done issue keys WITH Story Points from all 17 sprints.
Run after fetching results from Jira MCP search.
This is meant to be called from add_sp_keys.py with content.json paths.
"""
import json, sys, os

SP_FILE = 'sp_keys.json'

def process_content_file(path, label="?"):
    c = json.load(open(path))
    r = c.get('result', c)
    d = json.loads(r) if isinstance(r, str) else r
    keys = [i['key'] for i in d.get('issues', [])]
    
    existing = json.load(open(SP_FILE)) if os.path.exists(SP_FILE) else []
    merged = sorted(set(existing + keys))
    json.dump(merged, open(SP_FILE, 'w'))
    print(f'{label}: +{len(keys)} keys. Total: {len(merged)}')
    return d.get('total', len(keys)), len(keys)

if __name__ == '__main__':
    path = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else "?"
    total, received = process_content_file(path, label)
    if total > received:
        print(f'  NOTE: {total} total, only got {received}. Need start_at={received} for more.')
