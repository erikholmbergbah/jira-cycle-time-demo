#!/usr/bin/env python3
"""Helper to save search results to sprint files."""
import json, os, sys

DATA_DIR = "/Users/erikholmberg/Documents/Code/jira-cycle-time-demo"
ISSUES_DIR = os.path.join(DATA_DIR, "sprint_issues")
os.makedirs(ISSUES_DIR, exist_ok=True)

def save_result(content_file, sprint_name, append=False):
    filepath = os.path.join(ISSUES_DIR, f"{sprint_name.replace(' ', '_')}.json")
    with open(content_file) as f:
        data = json.load(f)
    result = json.loads(data['result'])
    new_issues = result['issues']
    
    if append and os.path.exists(filepath):
        with open(filepath) as f:
            existing = json.load(f)
        existing.extend(new_issues)
        issues = existing
    else:
        issues = new_issues
    
    with open(filepath, 'w') as f:
        json.dump(issues, f, indent=2)
    
    total = result['total']
    print(f"{sprint_name}: saved {len(issues)}/{total} issues" + 
          (" (NEEDS MORE)" if len(issues) < total else " (COMPLETE)"))
    return total, len(issues)

if __name__ == '__main__':
    if len(sys.argv) >= 3:
        save_result(sys.argv[1], sys.argv[2], append='--append' in sys.argv)
