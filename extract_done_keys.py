#!/usr/bin/env python3
"""Extract all unique Done issue keys across all sprints."""
import json, os

SPRINT_ORDER = [
    'BIP AI FY25Q4.1','BIP AI FY25Q4.2','BIP AI FY25Q4.3','BIP AI FY25Q4.4',
    'BIP AI FY25Q4.5','BIP AI FY25Q4.6','BIP AI FY25Q4.7',
    'BIP AI FY26Q1.1','BIP AI FY26Q1.2','BIP AI FY26Q1.3','BIP AI FY26Q1.4',
    'BIP AI FY26Q1.5','BIP AI FY26Q1.6','BIP AI FY26Q1.7',
    'BIP AI FY26Q2.1','BIP AI FY26Q2.2','BIP AI FY26Q2.3',
]

seen = set()
done_keys = []
key_to_sprint = {}

for sprint_name in SPRINT_ORDER:
    fname = sprint_name.replace(' ', '_') + '.json'
    filepath = os.path.join('sprint_issues', fname)
    with open(filepath) as f:
        issues = json.load(f)
    for issue in issues:
        key = issue['key']
        if issue.get('status', {}).get('category') == 'Done' and key not in seen:
            seen.add(key)
            done_keys.append(key)
            key_to_sprint[key] = sprint_name

print(f'Total unique Done issues: {len(done_keys)}')
with open('done_keys.json', 'w') as f:
    json.dump(done_keys, f)
with open('key_to_sprint.json', 'w') as f:
    json.dump(key_to_sprint, f)
print('First 10:', done_keys[:10])
print('Last 10:', done_keys[-10:])
