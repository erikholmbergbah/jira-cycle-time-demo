#!/usr/bin/env python3
"""Save issue dates result to the dates collection."""
import json, sys, os

DATES_FILE = "/Users/erikholmberg/Documents/Code/jira-cycle-time-demo/issue_dates.json"

def save_date_result(result_str, key=None):
    """Save a single issue dates result."""
    if os.path.exists(DATES_FILE):
        with open(DATES_FILE) as f:
            dates = json.load(f)
    else:
        dates = {}
    
    if isinstance(result_str, str):
        data = json.loads(result_str)
    else:
        data = result_str
    
    issue_key = data.get('issue_key', key)
    dates[issue_key] = data
    
    with open(DATES_FILE, 'w') as f:
        json.dump(dates, f, indent=2)
    
    return len(dates)

if __name__ == '__main__':
    # Read from file or stdin
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = json.load(f)
        if 'result' in data:
            n = save_date_result(data['result'])
        else:
            n = save_date_result(data)
        print(f"Saved. Total dates collected: {n}")
    else:
        print("Usage: save_dates.py <content_file>")
