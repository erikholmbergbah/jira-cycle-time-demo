#!/usr/bin/env python3
"""Save a batch of issue_dates results to the master file."""
import json, sys, os

RESULTS_FILE = 'issue_dates_all.json'

def load():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return {}

def save(data):
    with open(RESULTS_FILE, 'w') as f:
        json.dump(data, f)

# Read batch from stdin - expects JSON array of result objects
if len(sys.argv) > 1:
    # Read from file
    with open(sys.argv[1]) as f:
        batch = json.load(f)
else:
    batch = json.load(sys.stdin)

data = load()
for item in batch:
    key = item['issue_key']
    data[key] = item

save(data)
with open('done_keys.json') as f:
    total = len(json.load(f))
print(f"Saved {len(batch)} issues. Total: {len(data)}/{total}")
