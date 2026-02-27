#!/usr/bin/env python3
"""
Process a raw search result JSON string directly.
Usage: echo '<json>' | python3 process_inline.py
Or: python3 process_inline.py < raw_file.json
"""
import json, sys, os
from datetime import datetime

def parse_dt(s):
    if not s: return None
    try:
        if len(s) > 5 and s[-5] in "+-" and s[-4:].isdigit():
            s = s[:-2] + ":" + s[-2:]
        return datetime.fromisoformat(s)
    except:
        return None

STATUS_MAP = {
    "In Progress": "in_progress",
    "In Testing": "in_testing",
    "Peer Review": "peer_review",
    "Blocked": "blocked",
    "Canceled": "canceled",
    "Backlog": "backlog",
    "Selected for Development": "backlog",
}

def process_issue(issue):
    key = issue["key"]
    created = issue.get("created", "")
    resolution_date = issue.get("resolutiondate", "")
    status_name = issue.get("status", {}).get("name", "")
    
    if status_name != "Done":
        return None
    
    changelogs = issue.get("changelogs", [])
    status_changes = []
    for cl in changelogs:
        ts = cl.get("created", "")
        for item in cl.get("items", []):
            if item.get("field") == "status":
                status_changes.append({
                    "timestamp": ts,
                    "from": item.get("from_string", ""),
                    "to": item.get("to_string", ""),
                })
    status_changes.sort(key=lambda x: x["timestamp"])
    
    first_active = None
    for sc in status_changes:
        if sc["to"] == "In Progress":
            first_active = sc["timestamp"]
            break
    
    done_at = None
    for sc in reversed(status_changes):
        if sc["to"] == "Done":
            done_at = sc["timestamp"]
            break
    
    if not first_active or not done_at:
        return None
    
    durations = {
        "backlog_minutes": 0,
        "in_progress_minutes": 0,
        "in_testing_minutes": 0,
        "peer_review_minutes": 0,
        "blocked_minutes": 0,
        "canceled_minutes": 0,
    }
    
    current_status = "backlog"
    current_ts = parse_dt(created)
    
    for sc in status_changes:
        sc_ts = parse_dt(sc["timestamp"])
        if current_ts and sc_ts and sc_ts > current_ts:
            minutes = (sc_ts - current_ts).total_seconds() / 60.0
            status_key = current_status + "_minutes"
            if status_key in durations:
                durations[status_key] += int(minutes)
        to_status = STATUS_MAP.get(sc["to"], "")
        if to_status:
            current_status = to_status
        elif sc["to"] == "Done":
            current_status = "done"
        current_ts = sc_ts
    
    return {
        "created": created,
        "resolution_date": resolution_date,
        "first_active": first_active,
        "done_at": done_at,
        **durations,
    }

def main():
    out_file = "issue_data_full.json"
    data = json.load(open(out_file)) if os.path.exists(out_file) else {}
    
    raw_text = sys.stdin.read()
    raw = json.loads(raw_text)
    issues = raw.get("issues", [])
    
    added = 0
    skipped_not_done = 0
    skipped_exists = 0
    skipped_no_transitions = 0
    
    for issue in issues:
        key = issue["key"]
        if key in data:
            skipped_exists += 1
            continue
        result = process_issue(issue)
        if result:
            data[key] = result
            added += 1
        else:
            status = issue.get("status", {}).get("name", "?")
            if status != "Done":
                skipped_not_done += 1
            else:
                skipped_no_transitions += 1
    
    json.dump(data, open(out_file, "w"))
    print(f"+{added} issues (skip: {skipped_exists} exist, {skipped_not_done} not-done, {skipped_no_transitions} no-transitions). Total: {len(data)}")

if __name__ == "__main__":
    main()
