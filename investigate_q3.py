#!/usr/bin/env python3
"""Investigate FY25Q4.3 In Progress outliers."""
import json
from datetime import datetime

issues = json.load(open("issue_data_all.json"))
k2s = json.load(open("key_to_sprint.json"))

q3_issues = []
for key, d in issues.items():
    sprint = k2s.get(key, "")
    if "FY25Q4.3" in sprint:
        ip_days = d.get("in_progress_minutes", 0) / 1440
        test_days = d.get("in_testing_minutes", 0) / 1440
        pr_days = d.get("peer_review_minutes", 0) / 1440
        blk_days = d.get("blocked_minutes", 0) / 1440
        backlog_days = d.get("backlog_minutes", 0) / 1440
        first_active = d.get("first_active")
        done_at = d.get("done_at")
        created = d.get("created")
        if first_active and done_at:
            fa = datetime.fromisoformat(first_active)
            da = datetime.fromisoformat(done_at)
            cycle = (da - fa).total_seconds() / 86400
        else:
            cycle = None
        q3_issues.append({
            "key": key, "cycle": cycle,
            "ip_days": ip_days, "test_days": test_days,
            "pr_days": pr_days, "blk_days": blk_days,
            "backlog_days": backlog_days,
            "ip_min": d.get("in_progress_minutes", 0),
            "first_active": first_active,
            "done_at": done_at,
            "created": created,
        })

q3_issues.sort(key=lambda x: x["ip_days"], reverse=True)
print(f"FY25Q4.3: {len(q3_issues)} sampled issues\n")
for r in q3_issues:
    cyc_str = f"{r['cycle']:.1f}" if r["cycle"] else "N/A"
    print(f"{r['key']:12s}  cycle={cyc_str:>6s}d  "
          f"IP={r['ip_days']:>6.1f}d  Test={r['test_days']:>5.1f}d  "
          f"PR={r['pr_days']:>5.1f}d  Blk={r['blk_days']:>5.1f}d  "
          f"Backlog={r['backlog_days']:>5.1f}d")
    print(f"              created      = {r['created']}")
    print(f"              first_active = {r['first_active']}")
    print(f"              done_at      = {r['done_at']}")
    print(f"              IP minutes   = {r['ip_min']}")
    print()

# Compare to overall averages
all_ip = [d.get("in_progress_minutes", 0) / 1440 for d in issues.values()]
print(f"--- Overall avg IP: {sum(all_ip)/len(all_ip):.1f}d  "
      f"median IP: {sorted(all_ip)[len(all_ip)//2]:.1f}d")
q3_ip = [r["ip_days"] for r in q3_issues]
print(f"--- FY25Q4.3 avg IP: {sum(q3_ip)/len(q3_ip):.1f}d  "
      f"median IP: {sorted(q3_ip)[len(q3_ip)//2]:.1f}d")
