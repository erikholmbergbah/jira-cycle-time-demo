#!/usr/bin/env python3
"""
Append a batch of raw MCP issue JSON results to the growing dataset.
Usage: python3 append_batch.py <batch_number>
Raw data is read from raw_batch_<N>.json, processed, and appended to issue_data_full.json
"""
import json, sys, os

BATCH_NUM = int(sys.argv[1]) if len(sys.argv) > 1 else 0
RAW_FILE = f"raw_batch_{BATCH_NUM}.json"
OUT_FILE = "issue_data_full.json"

# Load raw batch
with open(RAW_FILE) as f:
    raw_issues = json.load(f)

# Load existing data or start fresh
if os.path.exists(OUT_FILE):
    with open(OUT_FILE) as f:
        all_data = json.load(f)
else:
    all_data = {}

for issue in raw_issues:
    key = issue["issue_key"]
    created = issue.get("created")
    resolution_date = issue.get("resolution_date")
    current_status = issue.get("current_status", "")

    # Skip non-Done issues
    if current_status != "Done":
        continue

    # Extract first_active (first In Progress entry) and done_at from status_changes
    first_active = None
    done_at = None
    for sc in issue.get("status_changes", []):
        if sc["status"] == "In Progress" and first_active is None:
            first_active = sc["entered_at"]
        if sc["status"] == "Done":
            done_at = sc["entered_at"]

    # Extract status durations from summary
    summary = {}
    for s in issue.get("status_summary", []):
        summary[s["status"]] = s["total_duration_minutes"]

    all_data[key] = {
        "created": created,
        "resolution_date": resolution_date,
        "first_active": first_active,
        "done_at": done_at,
        "backlog_minutes": summary.get("Backlog", 0),
        "in_progress_minutes": summary.get("In Progress", 0),
        "in_testing_minutes": summary.get("In Testing", 0),
        "peer_review_minutes": summary.get("Peer Review Needed", 0),
        "blocked_minutes": summary.get("Blocked", 0),
        "canceled_minutes": summary.get("Canceled", 0),
    }

with open(OUT_FILE, "w") as f:
    json.dump(all_data, f)

print(f"Batch {BATCH_NUM}: processed {len(raw_issues)} issues, "
      f"{len(raw_issues) - sum(1 for i in raw_issues if i.get('current_status') != 'Done')} Done. "
      f"Total in {OUT_FILE}: {len(all_data)}")
