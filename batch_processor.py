#!/usr/bin/env python3
"""Process issue_dates results saved by batch fetching, compute true cycle times."""
import json, os

RESULTS_FILE = 'issue_dates_all.json'

def load_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return {}

def save_results(data):
    with open(RESULTS_FILE, 'w') as f:
        json.dump(data, f)

def add_result(key, result):
    data = load_results()
    data[key] = result
    save_results(data)
    return len(data)

def check_progress():
    with open('done_keys.json') as f:
        done_keys = json.load(f)
    data = load_results()
    fetched = set(data.keys())
    remaining = [k for k in done_keys if k not in fetched]
    print(f"Fetched: {len(fetched)}/{len(done_keys)}")
    print(f"Remaining: {len(remaining)}")
    if remaining:
        print(f"Next batch: {remaining[:10]}")
    return remaining

if __name__ == '__main__':
    remaining = check_progress()
