#!/usr/bin/env python3
"""
Process search results with expand=changelog into issue_data_full.json format.
Reads raw_search_batch_<N>.json files, extracts status transitions, computes durations.
Usage: python3 process_search_batch.py <batch_number>
"""
import json, sys, os
from datetime import datetime

def parse_dt(s):
    """Parse Jira datetime string"""
    if not s:
        return None
    # Handle both formats
    s = s.replace("T", "T")
    try:
        # Try with microseconds
        if "." in s:
            base, rest = s.rsplit(".", 1)
            # Split fraction from timezone
            if "+" in rest:
                frac, tz = rest.split("+", 1)
                s = f"{base}.{frac[:6]}+{tz}"
            elif "-" in rest:
                frac, tz = rest.rsplit("-", 1)
                if len(tz) == 4:
                    s = f"{base}.{frac[:6]}-{tz}"
        # Normalize timezone: -0400 -> -04:00
        if len(s) > 5 and s[-5] in "+-" and s[-4:].isdigit():
            s = s[:-2] + ":" + s[-2:]
        return datetime.fromisoformat(s)
    except:
        return None

STATUS_MAP = {
    "In Progress": "in_progress",
    "In Testing": "in_testing",
    "Peer Review Needed": "peer_review",
    "Peer Review": "peer_review",         # alias just in case
    "Blocked": "blocked",
    "Canceled": "canceled",
    "Backlog": "backlog",
    "Selected for Development": "backlog",
    "Ready for Dev": "backlog",
    "Done": "done",
}

def process_issue(issue):
    """Process a single issue from search results into our format."""
    key = issue["key"]
    created = issue.get("created", "")
    resolution_date = issue.get("resolutiondate", "")
    status_name = issue.get("status", {}).get("name", "")
    
    if status_name != "Done":
        return None  # Skip non-Done issues
    
    changelogs = issue.get("changelogs", [])
    
    # Extract status transitions in chronological order
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
    
    # Sort by timestamp
    status_changes.sort(key=lambda x: x["timestamp"])
    
    # Find first_active (first transition TO "In Progress")
    first_active = None
    for sc in status_changes:
        if sc["to"] == "In Progress":
            first_active = sc["timestamp"]
            break
    
    # Find done_at (last transition TO "Done")
    done_at = None
    for sc in reversed(status_changes):
        if sc["to"] == "Done":
            done_at = sc["timestamp"]
            break
    
    if not first_active or not done_at:
        return None  # Skip if no IP->Done transition found
    
    # Compute status durations from transitions
    durations = {
        "backlog_minutes": 0,
        "in_progress_minutes": 0,
        "in_testing_minutes": 0,
        "peer_review_minutes": 0,
        "blocked_minutes": 0,
        "canceled_minutes": 0,
    }
    
    # Build timeline: start from created in Backlog, then apply transitions
    current_status = "backlog"
    current_ts = parse_dt(created)
    
    for sc in status_changes:
        sc_ts = parse_dt(sc["timestamp"])
        if current_ts and sc_ts and sc_ts > current_ts:
            minutes = (sc_ts - current_ts).total_seconds() / 60.0
            status_key = current_status + "_minutes"
            if status_key in durations:
                durations[status_key] += int(minutes)
        # Map the new status
        to_status = STATUS_MAP.get(sc["to"], "")
        if to_status and to_status != "done":
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
    import glob as _glob
    out_file = "issue_data_full.json"

    # If a batch number is provided, process that single file (legacy mode).
    # Otherwise reprocess ALL raw_search_*.json + raw_search_sample_*.json files from scratch.
    if len(sys.argv) > 1:
        raw_files = [f"raw_search_batch_{sys.argv[1]}.json"]
    else:
        raw_files = sorted(_glob.glob("raw_search_*.json")) + sorted(_glob.glob("raw_search_sample_*.json"))
        if not raw_files:
            print("No raw_search_*.json files found"); sys.exit(1)

    data = {}   # rebuild from scratch
    added = 0
    skipped = 0
    for raw_file in raw_files:
        raw = json.load(open(raw_file))
        issues = raw.get("issues", [])
        for issue in issues:
            key = issue["key"]
            if key in data:
                skipped += 1
                continue
            result = process_issue(issue)
            if result:
                data[key] = result
                added += 1
            else:
                skipped += 1

    json.dump(data, open(out_file, "w"))
    print(f"Processed {len(raw_files)} files: {added} issues added, {skipped} skipped. Total: {len(data)}")


if __name__ == "__main__":
    main()
