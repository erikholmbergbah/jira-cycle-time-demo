#!/usr/bin/env python3
"""Collect issue dates (with status history) for all unique issues across sprints."""
import json, os, sys, time

DATA_DIR = "/Users/erikholmberg/Documents/Code/jira-cycle-time-demo"
ISSUES_DIR = os.path.join(DATA_DIR, "sprint_issues")
DATES_FILE = os.path.join(DATA_DIR, "issue_dates.json")

def get_all_unique_keys():
    """Get all unique issue keys across all sprints."""
    all_keys = set()
    for fname in sorted(os.listdir(ISSUES_DIR)):
        if fname.endswith('.json'):
            with open(os.path.join(ISSUES_DIR, fname)) as f:
                issues = json.load(f)
                for issue in issues:
                    all_keys.add(issue['key'])
    return sorted(all_keys)

def get_existing_dates():
    """Load already-collected dates."""
    if os.path.exists(DATES_FILE):
        with open(DATES_FILE) as f:
            return json.load(f)
    return {}

def get_missing_keys():
    """Get keys that still need dates collected."""
    all_keys = get_all_unique_keys()
    existing = get_existing_dates()
    return [k for k in all_keys if k not in existing]

if __name__ == '__main__':
    all_keys = get_all_unique_keys()
    existing = get_existing_dates()
    missing = [k for k in all_keys if k not in existing]
    print(f"Total unique: {len(all_keys)}")
    print(f"Already collected: {len(existing)}")
    print(f"Still missing: {len(missing)}")
    
    if missing:
        # Print next batch of 50 keys separated by commas for easy copy
        batch = missing[:50]
        print(f"\nNext batch ({len(batch)} keys):")
        print(",".join(batch))
