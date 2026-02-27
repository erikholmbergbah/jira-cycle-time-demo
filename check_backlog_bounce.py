#!/usr/bin/env python3
"""Find issues with IP -> Backlog -> IP pattern and compare first vs last IP->Done."""
import json, glob
from datetime import datetime

all_issues = {}
for f in sorted(glob.glob('raw_search_*.json')):
    data = json.load(open(f))
    for iss in data.get('issues', []):
        all_issues[iss['key']] = iss

full_data = json.load(open('issue_data_full.json'))

bounced = []
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
                    'date': cl.get('created', '')
                })

    # Check for IP -> Backlog -> IP pattern
    has_bounce = False
    been_ip = False
    for t in status_seq:
        if t['to'] == 'In Progress':
            if has_bounce:
                break  # confirmed: IP -> Backlog -> IP
            been_ip = True
        elif been_ip and t['to'] == 'Backlog':
            has_bounce = True
    else:
        if has_bounce:
            has_bounce = False  # never got back to IP

    if not has_bounce:
        # Also check IP -> Ready for Dev -> IP (similar pattern)
        been_ip = False
        has_bounce = False
        for t in status_seq:
            if t['to'] == 'In Progress':
                if has_bounce:
                    break
                been_ip = True
            elif been_ip and t['to'] in ('Backlog', 'Ready for Dev'):
                has_bounce = True
        else:
            has_bounce = False

    if has_bounce:
        # Find first and last IP timestamps
        ip_dates = [t['date'] for t in status_seq if t['to'] == 'In Progress']
        first_ip = ip_dates[0][:10] if ip_dates else '?'
        last_ip = ip_dates[-1][:10] if ip_dates else '?'
        done_date = full_data[key].get('done_at', '?')[:10]
        first_active = full_data[key].get('first_active', '?')[:10]
        bounced.append((key, first_ip, last_ip, done_date, first_active))

print(f"Issues with IP -> Backlog/ReadyForDev -> IP pattern: {len(bounced)}")
print()
print(f"{'Key':<14} {'First IP':<12} {'Last IP':<12} {'Done':<12} {'Current first_active'}")
print("-" * 70)
for key, fip, lip, done, fa in bounced:
    marker = " ***" if fip != lip else ""
    print(f"{key:<14} {fip:<12} {lip:<12} {done:<12} {fa}{marker}")

# Count how many have different first vs last IP
diff = sum(1 for _, fip, lip, _, _ in bounced if fip != lip)
print(f"\nWith different first/last IP date: {diff}")
print(f"Same first/last IP date: {len(bounced) - diff}")
