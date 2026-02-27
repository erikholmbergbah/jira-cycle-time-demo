#!/usr/bin/env python3
"""Quick save+process from MCP content.json path.
Usage: python3 save_and_process.py <batch_num> <content_json_path>
"""
import json, sys, subprocess

batch_num = sys.argv[1]
content_path = sys.argv[2]

c = json.load(open(content_path))
r = c.get('result', c)
d = json.loads(r) if isinstance(r, str) else r
raw_file = f'raw_search_{batch_num}.json'
json.dump(d, open(raw_file, 'w'))
print(f'Batch {batch_num}: {len(d["issues"])} issues returned')

# Process
result = subprocess.run(['python3', 'process_inline.py'], input=json.dumps(d), capture_output=True, text=True)
print(result.stdout.strip())
if result.stderr:
    print(f'ERRORS: {result.stderr[:200]}')
