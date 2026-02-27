#!/usr/bin/env python3
"""Identify reopened issues where the reopen spanned multiple days."""
import json, glob

all_issues = {}
for f in sorted(glob.glob('raw_search_*.json')):
    data = json.load(open(f))
    for iss in data.get('issues', []):
        all_issues[iss['key']] = iss

full_data = json.load(open('issue_data_full.json'))

same_day = []
multi_day = []

for key, iss in sorted(all_issues.items()):
    if key not in full_data:
        continue
    changelogs = iss.get('changelogs', [])
    status_seq = []
    for cl in changelogs:
        for item in cl.get('items', []):
            if item.get('field') == 'status':
                status_seq.append({
                    'from': item.get('from_string', ''),
                    'to': item.get('to_string', ''),
                    'date': cl.get('created', '')[:10]
                })

    # Find all Done -> * -> Done spans
    done_count = 0
    is_reopened = False
    max_reopen_days = 0
    for i, t in enumerate(status_seq):
        if t['to'] == 'Done':
            done_count += 1
        if done_count > 0 and t['to'] == 'In Progress' and t['from'] in ('Done', 'Canceled', 'Ready for Dev'):
            # Found a reopen - find when it next reaches Done
            reopen_date = t['date']
            for j in range(i+1, len(status_seq)):
                if status_seq[j]['to'] == 'Done':
                    redone_date = status_seq[j]['date']
                    is_reopened = True
                    if reopen_date != redone_date:
                        from datetime import datetime
                        d1 = datetime.strptime(reopen_date, '%Y-%m-%d')
                        d2 = datetime.strptime(redone_date, '%Y-%m-%d')
                        gap = (d2 - d1).days
                        max_reopen_days = max(max_reopen_days, gap)
                    break

    if not is_reopened:
        continue

    if max_reopen_days == 0:
        same_day.append(key)
    else:
        multi_day.append((key, max_reopen_days))

print(f"Same-day reopen (KEEP): {len(same_day)}")
for k in same_day:
    print(f"  {k}")

print(f"\nMulti-day reopen (EXCLUDE): {len(multi_day)}")
for k, days in sorted(multi_day, key=lambda x: -x[1]):
    print(f"  {k}: {days}d between reopen and re-done")

# Output the exclude list
exclude_keys = sorted([k for k, _ in multi_day])
print(f"\nExclude keys ({len(exclude_keys)}):")
print(exclude_keys)
