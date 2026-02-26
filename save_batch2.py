#!/usr/bin/env python3
"""Save batch 2 results (issues from batch 1 of sample)."""
import json, os

RESULTS_FILE = 'issue_dates_all.json'
data = {}
if os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE) as f:
        data = json.load(f)

def find_first_active(changes):
    """Find first transition to a non-Backlog active status."""
    for c in changes:
        if c['status'] in ('In Progress', 'In Testing', 'Peer Review Needed', 'Ready for Dev'):
            return c['entered_at']
    return None

def find_done(changes):
    """Find Done entry."""
    for c in changes:
        if c['status'] == 'Done':
            return c['entered_at']
    return None

def get_summary_minutes(summary, status):
    for s in summary:
        if s['status'] == status:
            return s['total_duration_minutes']
    return 0

def add(issue_data):
    parsed = json.loads(issue_data) if isinstance(issue_data, str) else issue_data
    key = parsed['issue_key']
    changes = parsed.get('status_changes', [])
    summary = parsed.get('status_summary', [])
    
    data[key] = {
        'created': parsed.get('created'),
        'resolution_date': parsed.get('resolution_date'),
        'first_in_progress': find_first_active(changes),
        'done_at': find_done(changes),
        'backlog_minutes': get_summary_minutes(summary, 'Backlog'),
        'in_progress_minutes': get_summary_minutes(summary, 'In Progress'),
        'in_testing_minutes': get_summary_minutes(summary, 'In Testing'),
        'peer_review_minutes': get_summary_minutes(summary, 'Peer Review Needed'),
        'blocked_minutes': get_summary_minutes(summary, 'Blocked'),
        'canceled_minutes': get_summary_minutes(summary, 'Canceled'),
    }

# Batch 1 sample results
batch = [
    {"issue_key":"BIP-26056","created":"2025-06-27T10:52:00.769000-04:00","resolution_date":"2025-07-08T17:42:06.669000-04:00","status_changes":[{"status":"Backlog","entered_at":"2025-06-27T10:52:00.769000-04:00","exited_at":"2025-07-01T11:09:04.533000-04:00","duration_minutes":5777},{"status":"In Progress","entered_at":"2025-07-01T11:09:04.533000-04:00","exited_at":"2025-07-07T11:04:44.605000-04:00","duration_minutes":8635},{"status":"In Testing","entered_at":"2025-07-07T11:04:44.605000-04:00","exited_at":"2025-07-08T17:42:06.673000-04:00","duration_minutes":1837},{"status":"Done","entered_at":"2025-07-08T17:42:06.673000-04:00"}],"status_summary":[{"status":"In Progress","total_duration_minutes":8635},{"status":"Backlog","total_duration_minutes":5777},{"status":"In Testing","total_duration_minutes":1837},{"status":"Done","total_duration_minutes":0}]},
    {"issue_key":"BIP-26081","created":"2025-06-27T15:14:01.502000-04:00","resolution_date":"2025-07-08T09:03:09.971000-04:00","status_changes":[{"status":"Backlog","entered_at":"2025-06-27T15:14:01.502000-04:00","exited_at":"2025-06-30T06:34:25.665000-04:00","duration_minutes":3800},{"status":"In Progress","entered_at":"2025-06-30T06:34:25.665000-04:00","exited_at":"2025-07-01T12:32:12.246000-04:00","duration_minutes":1797},{"status":"In Testing","entered_at":"2025-07-01T12:32:12.246000-04:00","exited_at":"2025-07-08T09:03:09.978000-04:00","duration_minutes":9870},{"status":"Done","entered_at":"2025-07-08T09:03:09.978000-04:00"}],"status_summary":[{"status":"In Testing","total_duration_minutes":9870},{"status":"Backlog","total_duration_minutes":3800},{"status":"In Progress","total_duration_minutes":1797},{"status":"Done","total_duration_minutes":0}]},
    {"issue_key":"BIP-26028","created":"2025-06-27T10:51:37.140000-04:00","resolution_date":"2025-07-10T23:12:00.705000-04:00","status_changes":[{"status":"Backlog","entered_at":"2025-06-27T10:51:37.140000-04:00","exited_at":"2025-07-08T10:45:47.341000-04:00","duration_minutes":15834},{"status":"In Progress","entered_at":"2025-07-08T10:45:47.341000-04:00","exited_at":"2025-07-10T09:57:35.501000-04:00","duration_minutes":2831},{"status":"In Testing","entered_at":"2025-07-10T09:57:35.501000-04:00","exited_at":"2025-07-10T23:12:00.707000-04:00","duration_minutes":794},{"status":"Done","entered_at":"2025-07-10T23:12:00.707000-04:00"}],"status_summary":[{"status":"Backlog","total_duration_minutes":15834},{"status":"In Progress","total_duration_minutes":2831},{"status":"In Testing","total_duration_minutes":794},{"status":"Done","total_duration_minutes":0}]},
    {"issue_key":"BIP-26025","created":"2025-06-27T10:51:34.709000-04:00","resolution_date":"2025-07-10T12:34:52.032000-04:00","status_changes":[{"status":"Backlog","entered_at":"2025-06-27T10:51:34.709000-04:00","exited_at":"2025-07-08T09:05:19.753000-04:00","duration_minutes":15733},{"status":"In Progress","entered_at":"2025-07-08T09:05:19.753000-04:00","exited_at":"2025-07-08T10:59:40.669000-04:00","duration_minutes":114},{"status":"In Testing","entered_at":"2025-07-08T10:59:40.669000-04:00","exited_at":"2025-07-10T12:34:52.038000-04:00","duration_minutes":2975},{"status":"Done","entered_at":"2025-07-10T12:34:52.038000-04:00"}],"status_summary":[{"status":"Backlog","total_duration_minutes":15733},{"status":"In Testing","total_duration_minutes":2975},{"status":"In Progress","total_duration_minutes":114},{"status":"Done","total_duration_minutes":0}]},
    {"issue_key":"BIP-26275","created":"2025-07-10T23:35:07.377000-04:00","resolution_date":"2025-07-25T08:55:38.972000-04:00","status_changes":[{"status":"Backlog","entered_at":"2025-07-10T23:35:07.377000-04:00","exited_at":"2025-07-14T10:05:01.674000-04:00","duration_minutes":4949},{"status":"In Progress","entered_at":"2025-07-14T10:05:01.674000-04:00","exited_at":"2025-07-22T09:57:41.127000-04:00","duration_minutes":11512},{"status":"In Testing","entered_at":"2025-07-22T09:57:41.127000-04:00","exited_at":"2025-07-22T09:57:44.364000-04:00","duration_minutes":0},{"status":"Blocked","entered_at":"2025-07-22T09:57:44.364000-04:00","exited_at":"2025-07-25T08:55:38.974000-04:00","duration_minutes":4257},{"status":"Done","entered_at":"2025-07-25T08:55:38.974000-04:00"}],"status_summary":[{"status":"In Progress","total_duration_minutes":11512},{"status":"Backlog","total_duration_minutes":4949},{"status":"Blocked","total_duration_minutes":4257},{"status":"In Testing","total_duration_minutes":0},{"status":"Done","total_duration_minutes":0}]},
    {"issue_key":"BIP-26267","created":"2025-07-10T23:35:03.399000-04:00","resolution_date":"2025-07-17T23:08:14.536000-04:00","status_changes":[{"status":"Backlog","entered_at":"2025-07-10T23:35:03.399000-04:00","exited_at":"2025-07-14T11:14:34.808000-04:00","duration_minutes":5019},{"status":"In Progress","entered_at":"2025-07-14T11:14:34.808000-04:00","exited_at":"2025-07-16T16:09:39.949000-04:00","duration_minutes":3175},{"status":"In Testing","entered_at":"2025-07-16T16:09:39.949000-04:00","exited_at":"2025-07-17T23:08:14.541000-04:00","duration_minutes":1858},{"status":"Done","entered_at":"2025-07-17T23:08:14.541000-04:00"}],"status_summary":[{"status":"Backlog","total_duration_minutes":5019},{"status":"In Progress","total_duration_minutes":3175},{"status":"In Testing","total_duration_minutes":1858},{"status":"Done","total_duration_minutes":0}]},
    {"issue_key":"BIP-26319","created":"2025-07-11T13:12:40.450000-04:00","resolution_date":"2025-07-25T14:43:47.345000-04:00","status_changes":[{"status":"Backlog","entered_at":"2025-07-11T13:12:40.450000-04:00","exited_at":"2025-07-21T10:53:14.367000-04:00","duration_minutes":14260},{"status":"Blocked","entered_at":"2025-07-21T10:53:14.367000-04:00","exited_at":"2025-07-22T10:13:04.681000-04:00","duration_minutes":1399},{"status":"In Progress","entered_at":"2025-07-22T10:13:04.681000-04:00","exited_at":"2025-07-25T09:55:04.693000-04:00","duration_minutes":4301},{"status":"In Testing","entered_at":"2025-07-25T09:55:04.693000-04:00","exited_at":"2025-07-25T14:43:47.351000-04:00","duration_minutes":288},{"status":"Done","entered_at":"2025-07-25T14:43:47.351000-04:00"}],"status_summary":[{"status":"Backlog","total_duration_minutes":14260},{"status":"In Progress","total_duration_minutes":4301},{"status":"Blocked","total_duration_minutes":1399},{"status":"In Testing","total_duration_minutes":288},{"status":"Done","total_duration_minutes":0}]},
    {"issue_key":"BIP-26265","created":"2025-07-10T23:35:02.400000-04:00","resolution_date":"2025-07-25T10:24:33.270000-04:00","status_changes":[{"status":"Backlog","entered_at":"2025-07-10T23:35:02.400000-04:00","exited_at":"2025-07-21T10:04:33.878000-04:00","duration_minutes":15029},{"status":"Blocked","entered_at":"2025-07-21T10:04:33.878000-04:00","exited_at":"2025-07-22T09:59:23.853000-04:00","duration_minutes":1434},{"status":"In Progress","entered_at":"2025-07-22T09:59:23.853000-04:00","exited_at":"2025-07-22T09:59:34.880000-04:00","duration_minutes":0},{"status":"In Testing","entered_at":"2025-07-22T09:59:34.880000-04:00","exited_at":"2025-07-25T10:24:33.275000-04:00","duration_minutes":4344},{"status":"Done","entered_at":"2025-07-25T10:24:33.275000-04:00"}],"status_summary":[{"status":"Backlog","total_duration_minutes":15029},{"status":"In Testing","total_duration_minutes":4344},{"status":"Blocked","total_duration_minutes":1434},{"status":"In Progress","total_duration_minutes":0},{"status":"Done","total_duration_minutes":0}]},
    {"issue_key":"BIP-26311","created":"2025-07-10T23:35:24.416000-04:00","resolution_date":"2025-07-25T13:42:16.048000-04:00","status_changes":[{"status":"Backlog","entered_at":"2025-07-10T23:35:24.416000-04:00","exited_at":"2025-07-15T11:10:34.882000-04:00","duration_minutes":6455},{"status":"In Progress","entered_at":"2025-07-15T11:10:34.882000-04:00","exited_at":"2025-07-25T13:04:58.398000-04:00","duration_minutes":14514},{"status":"In Testing","entered_at":"2025-07-25T13:04:58.398000-04:00","exited_at":"2025-07-25T13:42:16.049000-04:00","duration_minutes":37},{"status":"Done","entered_at":"2025-07-25T13:42:16.049000-04:00"}],"status_summary":[{"status":"In Progress","total_duration_minutes":14514},{"status":"Backlog","total_duration_minutes":6455},{"status":"In Testing","total_duration_minutes":37},{"status":"Done","total_duration_minutes":0}]},
    {"issue_key":"BIP-26471","created":"2025-07-23T13:18:29.307000-04:00","resolution_date":"2025-07-28T14:04:36.275000-04:00","status_changes":[{"status":"Backlog","entered_at":"2025-07-23T13:18:29.307000-04:00","exited_at":"2025-07-24T11:15:54.357000-04:00","duration_minutes":1317},{"status":"In Progress","entered_at":"2025-07-24T11:15:54.357000-04:00","exited_at":"2025-07-25T10:22:13.175000-04:00","duration_minutes":1386},{"status":"Canceled","entered_at":"2025-07-25T10:22:13.175000-04:00","exited_at":"2025-07-28T14:04:36.280000-04:00","duration_minutes":4542},{"status":"Done","entered_at":"2025-07-28T14:04:36.280000-04:00"}],"status_summary":[{"status":"Canceled","total_duration_minutes":4542},{"status":"In Progress","total_duration_minutes":1386},{"status":"Backlog","total_duration_minutes":1317},{"status":"Done","total_duration_minutes":0}]}
]

for item in batch:
    add(item)

with open(RESULTS_FILE, 'w') as f:
    json.dump(data, f)

print(f"Saved {len(batch)} issues. Total: {len(data)}")
