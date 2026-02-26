#!/usr/bin/env python3
"""Save issue dates from MCP result string."""
import json, sys, os

DATES_FILE = "/Users/erikholmberg/Documents/Code/jira-cycle-time-demo/issue_dates.json"

result_str = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()

# Load existing
if os.path.exists(DATES_FILE):
    with open(DATES_FILE) as f:
        dates = json.load(f)
else:
    dates = {}

# Parse the result
if os.path.isfile(result_str):
    with open(result_str) as f:
        wrapper = json.load(f)
    data = json.loads(wrapper['result'])
else:
    data = json.loads(result_str)

issue_key = data['issue_key']
dates[issue_key] = data

with open(DATES_FILE, 'w') as f:
    json.dump(dates, f, indent=2)

print(f"Saved {issue_key}. Total: {len(dates)}")
