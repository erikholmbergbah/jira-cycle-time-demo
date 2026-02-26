#!/usr/bin/env python3
"""Save issue dates results extracted from MCP calls. 
Usage: python3 save_issue.py KEY FIRST_IP_DATE DONE_DATE BACKLOG_MIN IP_MIN TEST_MIN REVIEW_MIN BLOCKED_MIN"""
import json, sys, os

RESULTS_FILE = 'issue_dates_all.json'

def load():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return {}

def save(data):
    with open(RESULTS_FILE, 'w') as f:
        json.dump(data, f)

key = sys.argv[1]
first_ip = sys.argv[2]  # first In Progress date
done_at = sys.argv[3]   # Done date
backlog = int(sys.argv[4])
ip = int(sys.argv[5])
testing = int(sys.argv[6])
review = int(sys.argv[7])
blocked = int(sys.argv[8])

data = load()
data[key] = {
    "first_in_progress": first_ip,
    "done_at": done_at,
    "backlog_minutes": backlog,
    "in_progress_minutes": ip,
    "in_testing_minutes": testing,
    "peer_review_minutes": review,
    "blocked_minutes": blocked,
}
save(data)

total_needed = 0
if os.path.exists('sample_keys.json'):
    with open('sample_keys.json') as f:
        total_needed = len(json.load(f)) + 10  # +10 for initial batch
print(f"Saved {key}. Total: {len(data)}/{total_needed}")
