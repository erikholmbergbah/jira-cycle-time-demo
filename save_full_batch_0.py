#!/usr/bin/env python3
"""Save batch 0 data and append to issue_data_full.json"""
import json, os

batch = {
    "BIP-23877": {"created":"2025-03-19T14:30:02.116000-04:00","resolution_date":"2025-08-08T16:00:57.802000-04:00","first_active":"2025-03-20T11:06:35.630000-04:00","done_at":"2025-08-08T16:00:57.807000-04:00","backlog_minutes":1236,"in_progress_minutes":197279,"in_testing_minutes":5760,"peer_review_minutes":293,"blocked_minutes":0,"canceled_minutes":0},
    "BIP-24894": {"created":"2025-05-08T14:43:44.642000-04:00","resolution_date":"2025-07-30T17:56:49.938000-04:00","first_active":"2025-05-08T14:44:00.522000-04:00","done_at":"2025-07-30T17:56:49.941000-04:00","backlog_minutes":0,"in_progress_minutes":110959,"in_testing_minutes":8753,"peer_review_minutes":0,"blocked_minutes":0,"canceled_minutes":0},
    "BIP-25110": {"created":"2025-05-22T10:59:03.601000-04:00","resolution_date":"2025-07-30T17:56:34.170000-04:00","first_active":"2025-05-22T10:59:52.237000-04:00","done_at":"2025-07-30T17:56:34.175000-04:00","backlog_minutes":0,"in_progress_minutes":91023,"in_testing_minutes":8753,"peer_review_minutes":0,"blocked_minutes":0,"canceled_minutes":0},
    "BIP-25392": {"created":"2025-06-05T16:55:50.279000-04:00","resolution_date":"2025-07-23T16:09:24.733000-04:00","first_active":"2025-06-05T16:57:57.114000-04:00","done_at":"2025-07-23T16:09:24.737000-04:00","backlog_minutes":2,"in_progress_minutes":68674,"in_testing_minutes":397,"peer_review_minutes":0,"blocked_minutes":0,"canceled_minutes":0},
    "BIP-25704": {"created":"2025-06-16T12:30:49.749000-04:00","resolution_date":"2025-08-08T16:26:37.537000-04:00","first_active":"2025-06-17T11:15:08.933000-04:00","done_at":"2025-08-08T16:26:37.539000-04:00","backlog_minutes":1364,"in_progress_minutes":61796,"in_testing_minutes":13074,"peer_review_minutes":319,"blocked_minutes":0,"canceled_minutes":0},
    "BIP-25705": {"created":"2025-06-16T12:35:30.546000-04:00","resolution_date":"2025-08-08T16:26:33.802000-04:00","first_active":"2025-06-17T11:14:26.764000-04:00","done_at":"2025-08-08T16:26:33.807000-04:00","backlog_minutes":1358,"in_progress_minutes":75127,"in_testing_minutes":0,"peer_review_minutes":64,"blocked_minutes":0,"canceled_minutes":0},
    "BIP-25706": {"created":"2025-06-16T12:35:56.581000-04:00","resolution_date":"2025-07-30T17:56:28.064000-04:00","first_active":"2025-06-25T11:12:28.116000-04:00","done_at":"2025-07-30T17:56:28.068000-04:00","backlog_minutes":12876,"in_progress_minutes":42050,"in_testing_minutes":8753,"peer_review_minutes":0,"blocked_minutes":0,"canceled_minutes":0},
    "BIP-25707": {"created":"2025-06-16T12:37:40.820000-04:00","resolution_date":"2025-08-08T16:26:40.728000-04:00","first_active":"2025-06-17T11:14:32.259000-04:00","done_at":"2025-08-08T16:26:40.732000-04:00","backlog_minutes":1356,"in_progress_minutes":70550,"in_testing_minutes":4321,"peer_review_minutes":319,"blocked_minutes":0,"canceled_minutes":0},
    # BIP-25880 skipped: current_status=Backlog (not Done)
    "BIP-26005": {"created":"2025-06-27T10:51:14.945000-04:00","resolution_date":"2025-07-10T17:26:50.183000-04:00","first_active":"2025-07-07T11:15:47.422000-04:00","done_at":"2025-07-10T17:26:50.190000-04:00","backlog_minutes":14424,"in_progress_minutes":4306,"in_testing_minutes":384,"peer_review_minutes":0,"blocked_minutes":0,"canceled_minutes":0},
}

OUT = "issue_data_full.json"
data = json.load(open(OUT)) if os.path.exists(OUT) else {}
data.update(batch)
json.dump(data, open(OUT, "w"))
print(f"Batch 0: added {len(batch)} issues. Total: {len(data)}")
