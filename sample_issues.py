#!/usr/bin/env python3
"""Sample Done issues from each sprint for status history fetching."""
import json, os, random

random.seed(42)  # reproducible

SPRINT_ORDER = [
    'BIP AI FY25Q4.1','BIP AI FY25Q4.2','BIP AI FY25Q4.3','BIP AI FY25Q4.4',
    'BIP AI FY25Q4.5','BIP AI FY25Q4.6','BIP AI FY25Q4.7',
    'BIP AI FY26Q1.1','BIP AI FY26Q1.2','BIP AI FY26Q1.3','BIP AI FY26Q1.4',
    'BIP AI FY26Q1.5','BIP AI FY26Q1.6','BIP AI FY26Q1.7',
    'BIP AI FY26Q2.1','BIP AI FY26Q2.2','BIP AI FY26Q2.3',
]

# Load already fetched keys
if os.path.exists('issue_dates_all.json'):
    with open('issue_dates_all.json') as f:
        already_fetched = set(json.load(f).keys())
else:
    already_fetched = set()

# Global seen set to avoid dups across sprints  
global_seen = set()
sample_by_sprint = {}
all_sample_keys = []

for sprint_name in SPRINT_ORDER:
    fname = sprint_name.replace(' ', '_') + '.json'
    filepath = os.path.join('sprint_issues', fname)
    with open(filepath) as f:
        issues = json.load(f)
    
    done_issues = [i for i in issues if i.get('status', {}).get('category') == 'Done' and i['key'] not in global_seen]
    
    # Sample 6 (or all if fewer)
    sample_size = min(6, len(done_issues))
    sampled = random.sample(done_issues, sample_size)
    
    sprint_keys = []
    for issue in sampled:
        key = issue['key']
        global_seen.add(key)
        if key not in already_fetched:
            sprint_keys.append(key)
            all_sample_keys.append(key)
    
    sample_by_sprint[sprint_name] = sprint_keys

print(f"Already fetched: {len(already_fetched)}")
print(f"Need to fetch: {len(all_sample_keys)}")
print(f"\nSample per sprint:")
for sprint, keys in sample_by_sprint.items():
    short = sprint.replace('BIP AI ', '')
    print(f"  {short}: {keys}")

# Save the sample keys for batch fetching
with open('sample_keys.json', 'w') as f:
    json.dump(all_sample_keys, f)

# Print in batches of 10 for easy copy
print(f"\n=== Batches of 10 ===")
for i in range(0, len(all_sample_keys), 10):
    batch = all_sample_keys[i:i+10]
    print(f"Batch {i//10 + 1}: {batch}")
