#!/usr/bin/env python3
"""Append raw JSON result data to sprint issue file."""
import json, sys, os

ISSUES_DIR = "/Users/erikholmberg/Documents/Code/jira-cycle-time-demo/sprint_issues"
os.makedirs(ISSUES_DIR, exist_ok=True)

content_file = sys.argv[1]
sprint_name = sys.argv[2]
append = len(sys.argv) > 3 and sys.argv[3] == '--append'

filepath = os.path.join(ISSUES_DIR, f"{sprint_name.replace(' ', '_')}.json")

with open(content_file) as f:
    data = json.load(f)
result = json.loads(data['result'])
new_issues = result['issues']
total = result['total']

if append and os.path.exists(filepath):
    with open(filepath) as f:
        existing = json.load(f)
    existing.extend(new_issues)
    issues = existing
else:
    issues = new_issues

with open(filepath, 'w') as f:
    json.dump(issues, f, indent=2)

print(f"{sprint_name}: saved {len(issues)}/{total} issues" + 
      (" (NEEDS MORE)" if len(issues) < total else " (COMPLETE)"))
