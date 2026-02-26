#!/usr/bin/env python3
"""Data collection helper for Jira sprint cycle time analysis."""
import json
import os

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
ISSUES_DIR = os.path.join(DATA_DIR, "sprint_issues")
CHANGELOGS_DIR = os.path.join(DATA_DIR, "changelogs")

os.makedirs(ISSUES_DIR, exist_ok=True)
os.makedirs(CHANGELOGS_DIR, exist_ok=True)

# Sprint name -> ID mapping
SPRINTS = {
    "BIP AI FY25Q4.1": 42618,
    "BIP AI FY25Q4.2": 43062,
    "BIP AI FY25Q4.3": 43063,
    "BIP AI FY25Q4.4": 43067,
    "BIP AI FY25Q4.5": 43068,
    "BIP AI FY25Q4.6": 43069,
    "BIP AI FY25Q4.7": 43070,
    "BIP AI FY26Q1.1": 45566,
    "BIP AI FY26Q1.2": 45885,
    "BIP AI FY26Q1.3": 45567,
    "BIP AI FY26Q1.4": 45568,
    "BIP AI FY26Q1.5": 45569,
    "BIP AI FY26Q1.6": 45570,
    "BIP AI FY26Q1.7": 45571,
    "BIP AI FY26Q2.1": 48227,
    "BIP AI FY26Q2.2": 48228,
    "BIP AI FY26Q2.3": 48229,
}

def save_sprint_issues(sprint_name, issues):
    """Save sprint issues to file."""
    filepath = os.path.join(ISSUES_DIR, f"{sprint_name.replace(' ', '_')}.json")
    with open(filepath, 'w') as f:
        json.dump(issues, f, indent=2)
    print(f"Saved {len(issues)} issues for {sprint_name}")

def save_changelogs(issue_key, changelog):
    """Save issue changelog to file."""
    filepath = os.path.join(CHANGELOGS_DIR, f"{issue_key}.json")
    with open(filepath, 'w') as f:
        json.dump(changelog, f, indent=2)

def get_all_unique_keys():
    """Get all unique issue keys across all sprints."""
    all_keys = set()
    for fname in os.listdir(ISSUES_DIR):
        if fname.endswith('.json'):
            with open(os.path.join(ISSUES_DIR, fname)) as f:
                issues = json.load(f)
                for issue in issues:
                    all_keys.add(issue['key'])
    return sorted(all_keys)

if __name__ == '__main__':
    keys = get_all_unique_keys()
    print(f"Total unique issues: {len(keys)}")
    
    # Check which changelogs we still need
    existing = {f.replace('.json', '') for f in os.listdir(CHANGELOGS_DIR) if f.endswith('.json')}
    missing = [k for k in keys if k not in existing]
    print(f"Changelogs collected: {len(existing)}")
    print(f"Changelogs missing: {len(missing)}")
    if missing:
        print("Missing keys:", missing[:20], "..." if len(missing) > 20 else "")
