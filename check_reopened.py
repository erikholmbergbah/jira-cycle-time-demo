#!/usr/bin/env python3
"""Find issues that went IP -> Done -> IP -> Done (reopened pattern)."""
import json, glob

# Load all raw search data
all_issues = {}
for f in sorted(glob.glob('raw_search_*.json')):
    data = json.load(open(f))
    for iss in data.get('issues', []):
        all_issues[iss['key']] = iss

# Load current active keys (after all exclusions)
full_data = json.load(open('issue_data_full.json'))

# Check for IP -> Done -> IP -> Done pattern
reopened = []
for key, iss in all_issues.items():
    changelogs = iss.get('changelogs', [])
    # Build ordered list of status transitions
    status_seq = []
    for cl in changelogs:
        items = cl.get('items', [])
        for item in items:
            if item.get('field') == 'status':
                status_seq.append({
                    'from': item.get('from_string', ''),
                    'to': item.get('to_string', ''),
                    'date': cl.get('created', '')
                })
    
    # Look for pattern: any transition TO Done, then later TO In Progress, then TO Done again
    done_count = 0
    saw_ip_after_done = False
    for t in status_seq:
        if t['to'] == 'Done':
            done_count += 1
            if saw_ip_after_done:
                # This is the second Done after going back to IP
                reopened.append((key, status_seq))
                break
        elif t['to'] == 'In Progress' and done_count > 0:
            saw_ip_after_done = True

print(f"Issues with IP->Done->IP->Done pattern: {len(reopened)}")
print()

in_dataset = 0
for key, seq in sorted(reopened):
    marker = " *" if key in full_data else ""
    in_data = key in full_data
    if in_data:
        in_dataset += 1
    print(f"  {key}{'  (in dataset)' if in_data else '  (excluded)'}")
    for t in seq:
        print(f"    {t['date'][:10]}  {t['from']:20s} -> {t['to']}")
    print()

print(f"Total: {len(reopened)}, in active dataset: {in_dataset}")
