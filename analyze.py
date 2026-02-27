#!/usr/bin/env python3
"""
Cycle Time Analysis for BIP AI Sprints
=======================================
Reads issue_data_full.json (all Done issues with real status-transition
data) and key_to_sprint.json, computes true cycle time and status-duration
metrics, then generates an interactive HTML dashboard.
"""

import json, os, math, statistics
from datetime import datetime, date, timedelta, timezone
from collections import defaultdict

# ── Paths ────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
ISSUE_DATA   = os.path.join(BASE, "issue_data_full.json")
KEY_SPRINT   = os.path.join(BASE, "key_to_sprint.json")
SPRINT_DIR   = os.path.join(BASE, "sprint_issues")
RAW_DIR      = BASE  # raw_search_*.json lives here
OUTPUT_HTML  = os.path.join(BASE, "dashboard.html")
METRICS_JSON = os.path.join(BASE, "computed_metrics.json")

# ── Sprint ordering & dates ──────────────────────────────────────────────────
SPRINT_ORDER = [
    "BIP AI FY25Q4.1", "BIP AI FY25Q4.2", "BIP AI FY25Q4.3",
    "BIP AI FY25Q4.4", "BIP AI FY25Q4.5", "BIP AI FY25Q4.6",
    "BIP AI FY25Q4.7",
    "BIP AI FY26Q1.1", "BIP AI FY26Q1.2", "BIP AI FY26Q1.3",
    "BIP AI FY26Q1.4", "BIP AI FY26Q1.5", "BIP AI FY26Q1.6",
    "BIP AI FY26Q1.7",
    "BIP AI FY26Q2.1", "BIP AI FY26Q2.2", "BIP AI FY26Q2.3",
]

SPRINT_THROUGHPUT = {}  # populated from sprint_issues/*.json
SPRINT_SP = {}          # populated from sp_values.json + key_to_sprint.json
SP_VALUES_JSON = os.path.join(BASE, "sp_values.json")

# ── US Federal Holidays (observed dates) ─────────────────────────────────────
# Covers the data range Jun 2025 – Feb 2026.  When a holiday falls on Saturday
# the observed date is the preceding Friday; Sunday → following Monday.
US_HOLIDAYS = {
    # 2025
    date(2025, 1,  1),   # New Year's Day
    date(2025, 1, 20),   # MLK Day
    date(2025, 2, 17),   # Presidents' Day
    date(2025, 5, 26),   # Memorial Day
    date(2025, 6, 19),   # Juneteenth
    date(2025, 7,  4),   # Independence Day (Friday)
    date(2025, 9,  1),   # Labor Day
    date(2025, 10, 13),  # Columbus Day
    date(2025, 11, 11),  # Veterans Day
    date(2025, 11, 27),  # Thanksgiving
    date(2025, 12, 25),  # Christmas
    # 2026
    date(2026, 1,  1),   # New Year's Day
    date(2026, 1, 19),   # MLK Day
    date(2026, 2, 16),   # Presidents' Day
}

# ── Helpers ──────────────────────────────────────────────────────────────────
def parse_dt(s):
    """Parse ISO datetime string -> datetime (timezone-aware)."""
    if not s:
        return None
    return datetime.fromisoformat(s)

def business_days_between(dt_start, dt_end):
    """Return the number of business days (float) between two datetimes,
    excluding weekends (Sat/Sun) and US federal holidays.

    Fractional days are calculated based on an 8-hour workday (480 min).
    If start and end fall on the same business day the result is the
    intra-day fraction.  Non-business-day portions are skipped."""
    if dt_start is None or dt_end is None:
        return None
    if dt_end <= dt_start:
        return 0.0

    d_start = dt_start.date()
    d_end   = dt_end.date()

    def is_business(d):
        return d.weekday() < 5 and d not in US_HOLIDAYS

    # Same calendar day
    if d_start == d_end:
        if is_business(d_start):
            return (dt_end - dt_start).total_seconds() / 86400.0
        return 0.0

    total = 0.0

    # Partial first day (fraction remaining)
    if is_business(d_start):
        end_of_day = datetime.combine(d_start + timedelta(days=1),
                                      datetime.min.time(),
                                      tzinfo=dt_start.tzinfo)
        total += (end_of_day - dt_start).total_seconds() / 86400.0

    # Full days in between
    cur = d_start + timedelta(days=1)
    while cur < d_end:
        if is_business(cur):
            total += 1.0
        cur += timedelta(days=1)

    # Partial last day
    if is_business(d_end):
        start_of_day = datetime.combine(d_end, datetime.min.time(),
                                        tzinfo=dt_end.tzinfo)
        total += (dt_end - start_of_day).total_seconds() / 86400.0

    return total

def mins_to_days(m):
    """Convert minutes to calendar days (float)."""
    if m is None:
        return None
    return m / 1440.0

def percentile(data, p):
    """Return p-th percentile (0-100) of sorted data list."""
    if not data:
        return None
    n = len(data)
    k = (p / 100) * (n - 1)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return data[int(k)]
    return data[f] * (c - k) + data[c] * (k - f)

def safe_median(data):
    return statistics.median(data) if data else None

def safe_mean(data):
    return statistics.mean(data) if data else None


# ── Exclusions ───────────────────────────────────────────────────────────────
# BIP-25393 (49d IP) and BIP-25703 (37d IP): parked in "In Progress" for weeks
#   without active work, then batch-moved to Done together on the same day by
#   the same person.  Not representative of normal work items.
# BIP-26294 (21d IP across 2 stints with backlog re-entry): similar pattern.
# BIP-26538, BIP-27314, BIP-28723: manually excluded by user.
EXCLUDED_KEYS = {"BIP-25393", "BIP-25703", "BIP-26294",
                 "BIP-26538", "BIP-27314", "BIP-28723",
                 # Additional manual outliers
                 "BIP-26043", "BIP-28160", "BIP-28942", "BIP-27706",
                 "BIP-29078", "BIP-28906", "BIP-26543", "BIP-26721",
                 "BIP-26503", "BIP-26502", "BIP-26027",
                 "BIP-26790", "BIP-26789", "BIP-26788", "BIP-26572",
                 "BIP-26778", "BIP-26787", "BIP-26793"}

# Issues without Story Points assigned (queried from Jira).
NO_STORY_POINTS = {
    "BIP-30535", "BIP-30530", "BIP-30351", "BIP-30306", "BIP-29982",
    "BIP-29937", "BIP-29936", "BIP-29536", "BIP-29529", "BIP-29147",
    "BIP-28949", "BIP-28766", "BIP-25707", "BIP-25706", "BIP-25705",
    "BIP-25704", "BIP-25703", "BIP-25393", "BIP-25392", "BIP-25110",
    "BIP-24894", "BIP-23877",
}

# Issues that spent time in "Canceled" status before eventually reaching Done.
# Their cycle time is inflated by idle canceled time, not representative of work.
CANCELED_KEYS = {
    "BIP-26007", "BIP-26049", "BIP-26059", "BIP-26061", "BIP-26085",
    "BIP-26281", "BIP-26305", "BIP-26321", "BIP-26323", "BIP-26471",
    "BIP-26509", "BIP-27270", "BIP-27271", "BIP-27304", "BIP-27305",
    "BIP-27693", "BIP-28217", "BIP-28694", "BIP-28898", "BIP-28941",
    "BIP-29072", "BIP-29102", "BIP-29172", "BIP-29179", "BIP-30550",
    "BIP-30901", "BIP-30902",
}

# Issues reopened (Done → In Progress → Done) where the reopen spanned multiple days.
# Same-day reopens are kept as they represent minor corrections.
REOPENED_KEYS = {
    "BIP-26995", "BIP-27975", "BIP-28231", "BIP-28721", "BIP-30515",
}

# ── Load data ────────────────────────────────────────────────────────────────
with open(ISSUE_DATA) as f:
    all_issues = json.load(f)

# Exclude non-development work by summary keywords
SUMMARY_EXCLUDE_KEYS = set()
for sp in SPRINT_ORDER:
    fname = sp.replace(" ", "_") + ".json"
    fpath = os.path.join(SPRINT_DIR, fname)
    if os.path.exists(fpath):
        with open(fpath) as f:
            for iss in json.load(f):
                s = (iss.get("summary") or "").lower()
                if "adhoc support" in s or "on call" in s or "shadow" in s:
                    SUMMARY_EXCLUDE_KEYS.add(iss["key"])

issues = {k: v for k, v in all_issues.items()
          if k not in EXCLUDED_KEYS and k not in NO_STORY_POINTS
          and k not in CANCELED_KEYS and k not in REOPENED_KEYS
          and k not in SUMMARY_EXCLUDE_KEYS}

with open(KEY_SPRINT) as f:
    key_to_sprint = json.load(f)

# Load throughput from sprint_issues directory
for sp in SPRINT_ORDER:
    fname = sp.replace(" ", "_") + ".json"
    fpath = os.path.join(SPRINT_DIR, fname)
    if os.path.exists(fpath):
        with open(fpath) as f:
            SPRINT_THROUGHPUT[sp] = len(json.load(f))
    else:
        SPRINT_THROUGHPUT[sp] = 0

# Load story-point totals per sprint from sp_values.json
if os.path.exists(SP_VALUES_JSON):
    with open(SP_VALUES_JSON) as f:
        _sp_vals = json.load(f)   # key -> SP value
    for k, v in _sp_vals.items():
        sprint = key_to_sprint.get(k)
        if sprint and sprint in SPRINT_THROUGHPUT:
            SPRINT_SP[sprint] = SPRINT_SP.get(sprint, 0) + v
for sp in SPRINT_ORDER:
    SPRINT_SP.setdefault(sp, 0)
    SPRINT_SP[sp] = int(SPRINT_SP[sp])

# ── Build "last In Progress" lookup from raw changelogs ──────────────────────
# For cycle time we use the LAST transition into an active status (In Progress,
# In Testing, Peer Review Needed, Blocked) so that backlog bounces don't inflate
# the measurement.  We look for the last transition into In Progress that was
# preceded only by inactive statuses (Backlog / Ready for Dev) since the
# previous Done (or start).
import glob as _glob
LAST_ACTIVE = {}           # key -> ISO timestamp of last "real" start
ACTIVE_STATUSES = {"In Progress", "In Testing", "Peer Review Needed", "Blocked"}
for raw_path in sorted(_glob.glob(os.path.join(RAW_DIR, "raw_search_*.json"))) + \
                sorted(_glob.glob(os.path.join(RAW_DIR, "raw_search_sample_*.json"))):
    with open(raw_path) as f:
        raw = json.load(f)
    for iss in raw.get("issues", []):
        key = iss["key"]
        changelogs = iss.get("changelogs", [])
        # Walk transitions and find the last time the issue entered an active
        # status after being in Backlog/Ready for Dev (i.e. last restart).
        last_start = None
        for cl in changelogs:
            for item in cl.get("items", []):
                if item.get("field") != "status":
                    continue
                to_s = item.get("to_string", "")
                from_s = item.get("from_string", "")
                if to_s in ACTIVE_STATUSES:
                    if from_s in ("Backlog", "Ready for Dev", ""):
                        last_start = cl["created"]
                    elif last_start is None:
                        last_start = cl["created"]
        if last_start:
            LAST_ACTIVE[key] = last_start


# ── Compute per-issue metrics ────────────────────────────────────────────────
records = []
for key, d in issues.items():
    sprint = key_to_sprint.get(key, "Unknown")
    first_active = parse_dt(d.get("first_active"))
    done_at      = parse_dt(d.get("done_at"))
    created      = parse_dt(d.get("created"))
    resolved     = parse_dt(d.get("resolution_date"))

    # Use "last active start" when available (handles backlog bounces);
    # fall back to first_active from the data file.
    last_active = parse_dt(LAST_ACTIVE.get(key))
    cycle_start = last_active or first_active

    # Cycle time: last_active -> done_at  (business days)
    cycle_days = business_days_between(cycle_start, done_at)
    if cycle_days == 0.0 and cycle_start is None:
        cycle_days = None   # Backlog->Done skip

    # Lead time: created -> done_at (business days)
    lead_days = business_days_between(created, done_at)

    # Status durations in days
    ip_days      = mins_to_days(d.get("in_progress_minutes", 0))
    test_days    = mins_to_days(d.get("in_testing_minutes", 0))
    pr_days      = mins_to_days(d.get("peer_review_minutes", 0))
    blocked_days = mins_to_days(d.get("blocked_minutes", 0))
    cancel_days  = mins_to_days(d.get("canceled_minutes", 0))
    backlog_days = mins_to_days(d.get("backlog_minutes", 0))

    # "Active work" = IP + Testing + PR (excludes Blocked/Canceled/Backlog)
    active_days = ip_days + test_days + pr_days

    records.append({
        "key": key,
        "sprint": sprint,
        "cycle_days": cycle_days,
        "lead_days": lead_days,
        "backlog_days": backlog_days,
        "ip_days": ip_days,
        "test_days": test_days,
        "pr_days": pr_days,
        "blocked_days": blocked_days,
        "cancel_days": cancel_days,
        "active_days": active_days,
        "has_cycle": cycle_days is not None,
    })


# ── Aggregate overall ────────────────────────────────────────────────────────
cycle_times = sorted([r["cycle_days"] for r in records if r["has_cycle"]])
lead_times  = sorted([r["lead_days"]  for r in records if r["lead_days"] is not None])
active_times = sorted([r["active_days"] for r in records if r["has_cycle"]])

overall = {
    "sample_size": len(records),
    "with_cycle": len(cycle_times),
    "skipped": len(records) - len(cycle_times),
    "cycle_median": round(safe_median(cycle_times), 2) if cycle_times else None,
    "cycle_mean":   round(safe_mean(cycle_times), 2)   if cycle_times else None,
    "cycle_p85":    round(percentile(cycle_times, 85), 2) if cycle_times else None,
    "cycle_p95":    round(percentile(cycle_times, 95), 2) if cycle_times else None,
    "cycle_min":    round(min(cycle_times), 2)          if cycle_times else None,
    "cycle_max":    round(max(cycle_times), 2)          if cycle_times else None,
    "lead_median":  round(safe_median(lead_times), 2)   if lead_times else None,
    "lead_mean":    round(safe_mean(lead_times), 2)     if lead_times else None,
    "active_median": round(safe_median(active_times), 2) if active_times else None,
    "active_mean":   round(safe_mean(active_times), 2)  if active_times else None,
}

# ── Aggregate per-sprint ─────────────────────────────────────────────────────
sprint_data = {}
for sp in SPRINT_ORDER:
    sp_recs = [r for r in records if r["sprint"] == sp]
    sp_cycles = sorted([r["cycle_days"] for r in sp_recs if r["has_cycle"]])

    # Status averages for stacked chart (in days)
    ip_vals   = [r["ip_days"] for r in sp_recs if r["has_cycle"]]
    test_vals = [r["test_days"] for r in sp_recs if r["has_cycle"]]
    pr_vals   = [r["pr_days"] for r in sp_recs if r["has_cycle"]]
    blk_vals  = [r["blocked_days"] for r in sp_recs if r["has_cycle"]]

    sprint_data[sp] = {
        "sample_count": len(sp_recs),
        "with_cycle": len(sp_cycles),
        "throughput": SPRINT_THROUGHPUT.get(sp, 0),
        "story_points": SPRINT_SP.get(sp, 0),
        "cycle_median": round(safe_median(sp_cycles), 2) if sp_cycles else None,
        "cycle_mean":   round(safe_mean(sp_cycles), 2)   if sp_cycles else None,
        "cycle_p85":    round(percentile(sp_cycles, 85), 2) if sp_cycles else None,
        "avg_ip_days":      round(safe_mean(ip_vals), 2)   if ip_vals else 0,
        "avg_test_days":    round(safe_mean(test_vals), 2)  if test_vals else 0,
        "avg_pr_days":      round(safe_mean(pr_vals), 2)    if pr_vals else 0,
        "avg_blocked_days": round(safe_mean(blk_vals), 2)   if blk_vals else 0,
    }

# ── Build histogram buckets ─────────────────────────────────────────────────
# Buckets: 0-1, 1-2, 2-5, 5-10, 10-20, 20-30, 30+
HIST_BUCKETS = [
    ("0-1d",  0, 1),
    ("1-2d",  1, 2),
    ("2-5d",  2, 5),
    ("5-10d", 5, 10),
    ("10-20d", 10, 20),
    ("20-30d", 20, 30),
    ("30d+",  30, 999),
]
histogram = []
for label, lo, hi in HIST_BUCKETS:
    count = len([c for c in cycle_times if lo <= c < hi])
    histogram.append({"label": label, "count": count})

# ── Status distribution (overall) ───────────────────────────────────────────
status_totals = {
    "In Progress":        sum(r["ip_days"] for r in records if r["has_cycle"]),
    "In Testing":         sum(r["test_days"] for r in records if r["has_cycle"]),
    "Peer Review Needed": sum(r["pr_days"] for r in records if r["has_cycle"]),
    "Blocked":            sum(r["blocked_days"] for r in records if r["has_cycle"]),
}
# Also compute percentage of total tracked time
total_status_days = sum(status_totals.values())
status_pct = {k: round(v / total_status_days * 100, 1) if total_status_days else 0
              for k, v in status_totals.items()}

# ── Top outliers ─────────────────────────────────────────────────────────────
sorted_by_cycle = sorted([r for r in records if r["has_cycle"]],
                         key=lambda r: r["cycle_days"], reverse=True)
top_longest = sorted_by_cycle[:10]

sorted_by_blocked = sorted([r for r in records if r["blocked_days"] > 0],
                           key=lambda r: r["blocked_days"], reverse=True)
top_blocked = sorted_by_blocked[:10]

# ── Compute insights ────────────────────────────────────────────────────────
insights = []

# 1. Overall summary
insights.append(
    f"Across all {overall['with_cycle']} Done issues, the median cycle time "
    f"(In Progress &rarr; Done) is <strong>{overall['cycle_median']} days</strong>, "
    f"with a mean of {overall['cycle_mean']} days. The 85th percentile is "
    f"{overall['cycle_p85']} days and 95th percentile is {overall['cycle_p95']} days."
)

# 2. Spread
if overall["cycle_max"] and overall["cycle_min"]:
    spread = overall["cycle_max"] - overall["cycle_min"]
    insights.append(
        f"Cycle times range from {overall['cycle_min']} to {overall['cycle_max']} days "
        f"(spread of {round(spread, 1)} days), indicating significant variability. "
        f"High variability reduces predictability of delivery commitments."
    )

# 3. Blocked time
blocked_issues = [r for r in records if r["blocked_days"] > 0.5]
if blocked_issues:
    avg_blk = safe_mean([r["blocked_days"] for r in blocked_issues])
    insights.append(
        f"<strong>{len(blocked_issues)} issues</strong> spent more than half a day blocked. "
        f"Among those, the average blocked time was <strong>{round(avg_blk, 1)} days</strong>. "
        f"Reducing blocked time is one of the highest-leverage improvements."
    )

# 4. Testing bottleneck
if status_pct.get("In Testing", 0) > 30:
    insights.append(
        f"Testing accounts for <strong>{status_pct['In Testing']}%</strong> of tracked active time, "
        f"suggesting a potential bottleneck. Consider parallel testing, earlier test involvement, "
        f"or automated test coverage to reduce this."
    )

# 5. Backlog->Done skips
skip_keys = [r["key"] for r in records if not r["has_cycle"]]
if skip_keys:
    insights.append(
        f"{len(skip_keys)} issue(s) went directly from Backlog to Done without entering "
        f"In Progress ({', '.join(skip_keys)}). These were excluded from cycle time calculations."
    )

# 6. Sprint trend
early_sprints = SPRINT_ORDER[:4]
late_sprints  = SPRINT_ORDER[-4:]
early_medians = [sprint_data[s]["cycle_median"] for s in early_sprints
                 if sprint_data[s]["cycle_median"] is not None]
late_medians  = [sprint_data[s]["cycle_median"] for s in late_sprints
                 if sprint_data[s]["cycle_median"] is not None]
if early_medians and late_medians:
    e_avg = safe_mean(early_medians)
    l_avg = safe_mean(late_medians)
    if l_avg < e_avg:
        pct_imp = round((e_avg - l_avg) / e_avg * 100, 0)
        insights.append(
            f"Cycle times improved over time: the first 4 sprints averaged "
            f"{round(e_avg, 1)}-day median vs {round(l_avg, 1)} days in the last 4 "
            f"(~{int(pct_imp)}% improvement)."
        )
    elif l_avg > e_avg:
        pct_deg = round((l_avg - e_avg) / e_avg * 100, 0)
        insights.append(
            f"Cycle times increased over time: the first 4 sprints averaged "
            f"{round(e_avg, 1)}-day median vs {round(l_avg, 1)} days in the last 4 "
            f"(~{int(pct_deg)}% increase). Investigate growing complexity or WIP limits."
        )

# 7. Throughput trend
early_thru = [SPRINT_THROUGHPUT.get(s, 0) for s in early_sprints]
late_thru  = [SPRINT_THROUGHPUT.get(s, 0) for s in late_sprints]
if early_thru and late_thru:
    e_thru = safe_mean(early_thru)
    l_thru = safe_mean(late_thru)
    insights.append(
        f"Average throughput: first 4 sprints = {round(e_thru, 0)} issues/sprint, "
        f"last 4 sprints = {round(l_thru, 0)} issues/sprint."
    )

# 8. Efficiency ratio: active work vs lead time (created->done)
# This captures how much of total lead time is spent in active statuses
eff_ratios = []
for r in records:
    if r["has_cycle"] and r["lead_days"] and r["lead_days"] > 0:
        eff_ratios.append(r["active_days"] / r["lead_days"] * 100)
if eff_ratios:
    med_eff = round(safe_median(eff_ratios), 0)
    insights.append(
        f"Flow efficiency (active work / lead time): median <strong>{int(med_eff)}%</strong>. "
        f"Lead time includes backlog wait before work starts. "
        f"Higher efficiency means less waiting. World-class teams target &gt;40%."
    )

# 9. Median lead vs cycle gap
if overall["lead_median"] and overall["cycle_median"]:
    gap = round(overall["lead_median"] - overall["cycle_median"], 1)
    if gap > 1:
        insights.append(
            f"Median lead time ({overall['lead_median']}d) exceeds median cycle time "
            f"({overall['cycle_median']}d) by <strong>{gap} days</strong>, meaning issues "
            f"sit in Backlog for a median of ~{gap} days before work begins."
        )

# ── Assemble metrics object ─────────────────────────────────────────────────
metrics = {
    "overall": overall,
    "sprint_order": SPRINT_ORDER,
    "sprint_data": sprint_data,
    "histogram": histogram,
    "status_totals": {k: round(v, 1) for k, v in status_totals.items()},
    "status_pct": status_pct,
    "top_longest": [{"key": r["key"], "sprint": r["sprint"],
                     "cycle_days": round(r["cycle_days"], 2),
                     "ip": round(r["ip_days"], 2),
                     "test": round(r["test_days"], 2),
                     "blocked": round(r["blocked_days"], 2)}
                    for r in top_longest],
    "top_blocked": [{"key": r["key"], "sprint": r["sprint"],
                     "blocked_days": round(r["blocked_days"], 2),
                     "cycle_days": round(r["cycle_days"], 2)}
                    for r in top_blocked],
    "insights": insights,
    "all_issues": [{"key": r["key"], "sprint": r["sprint"],
                    "cycle": round(r["cycle_days"], 2) if r["cycle_days"] else None,
                    "ip": round(r["ip_days"], 2),
                    "test": round(r["test_days"], 2),
                    "pr": round(r["pr_days"], 2),
                    "blocked": round(r["blocked_days"], 2),
                    "backlog": round(r["backlog_days"], 2)}
                   for r in sorted(records, key=lambda r: r["sprint"])],
}

with open(METRICS_JSON, "w") as f:
    json.dump(metrics, f, indent=2)
print(f"Wrote {METRICS_JSON}")

# ── Generate HTML Dashboard ──────────────────────────────────────────────────
sprint_labels_js   = json.dumps([s.replace("BIP AI ", "") for s in SPRINT_ORDER])
cycle_medians_js   = json.dumps([sprint_data[s]["cycle_median"] for s in SPRINT_ORDER])
cycle_means_js     = json.dumps([sprint_data[s]["cycle_mean"] for s in SPRINT_ORDER])
cycle_p85s_js      = json.dumps([sprint_data[s]["cycle_p85"] for s in SPRINT_ORDER])
throughputs_js     = json.dumps([sprint_data[s]["throughput"] for s in SPRINT_ORDER])
story_points_js    = json.dumps([sprint_data[s]["story_points"] for s in SPRINT_ORDER])
avg_ip_js          = json.dumps([sprint_data[s]["avg_ip_days"] for s in SPRINT_ORDER])
avg_test_js        = json.dumps([sprint_data[s]["avg_test_days"] for s in SPRINT_ORDER])
avg_pr_js          = json.dumps([sprint_data[s]["avg_pr_days"] for s in SPRINT_ORDER])
avg_blk_js         = json.dumps([sprint_data[s]["avg_blocked_days"] for s in SPRINT_ORDER])
hist_labels_js     = json.dumps([h["label"] for h in histogram])
hist_counts_js     = json.dumps([h["count"] for h in histogram])
status_labels_js   = json.dumps(list(status_pct.keys()))
status_values_js   = json.dumps(list(status_pct.values()))

# Scatter data: all issues with cycle time
scatter_js = json.dumps([
    {"x": i+1, "y": round(r["cycle_days"], 2), "key": r["key"], "sprint": r["sprint"]}
    for i, r in enumerate(sorted(
        [r for r in records if r["has_cycle"]],
        key=lambda r: (SPRINT_ORDER.index(r["sprint"]) if r["sprint"] in SPRINT_ORDER else 99,
                       r["cycle_days"])
    ))
])

# Top longest table rows
longest_rows = ""
for r in top_longest:
    longest_rows += f"""<tr>
        <td>{r['key']}</td><td>{r['sprint'].replace('BIP AI ', '')}</td>
        <td>{round(r['cycle_days'], 1)}</td><td>{round(r['ip_days'], 1)}</td>
        <td>{round(r['test_days'], 1)}</td><td>{round(r['blocked_days'], 1)}</td>
    </tr>\n"""

top_blocked_rows = ""
for r in top_blocked:
    top_blocked_rows += f"""<tr>
        <td>{r['key']}</td><td>{r['sprint'].replace('BIP AI ', '')}</td>
        <td>{round(r['blocked_days'], 1)}</td><td>{round(r['cycle_days'], 1)}</td>
    </tr>\n"""

insights_html = "\n".join(f'<li class="insight">{ins}</li>' for ins in insights)

# Sprint detail table
sprint_detail_rows = ""
for sp in SPRINT_ORDER:
    sd = sprint_data[sp]
    label = sp.replace("BIP AI ", "")
    sprint_detail_rows += f"""<tr>
        <td>{label}</td>
        <td>{sd['throughput']}</td>
        <td>{sd['story_points']}</td>
        <td>{sd['sample_count']}</td>
        <td>{sd['cycle_median'] if sd['cycle_median'] is not None else '&#8212;'}</td>
        <td>{sd['cycle_mean'] if sd['cycle_mean'] is not None else '&#8212;'}</td>
        <td>{sd['cycle_p85'] if sd['cycle_p85'] is not None else '&#8212;'}</td>
        <td>{sd['avg_ip_days']}</td>
        <td>{sd['avg_test_days']}</td>
        <td>{sd['avg_pr_days']}</td>
        <td>{sd['avg_blocked_days']}</td>
    </tr>\n"""


html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BIP AI &mdash; Cycle Time Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0d1117; --card: #161b22; --border: #30363d;
    --text: #e6edf3; --muted: #8b949e; --accent: #58a6ff;
    --green: #3fb950; --orange: #d29922; --red: #f85149;
    --purple: #bc8cff; --teal: #39d353;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text); padding: 24px;
    line-height: 1.5;
  }
  h1 { font-size: 1.8rem; margin-bottom: 4px; }
  .subtitle { color: var(--muted); margin-bottom: 24px; font-size: 0.95rem; }
  .kpi-row { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }
  .kpi {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 8px; padding: 16px 20px; min-width: 160px; flex: 1;
  }
  .kpi .label { color: var(--muted); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; }
  .kpi .value { font-size: 1.8rem; font-weight: 700; color: var(--accent); margin-top: 4px; }
  .kpi .unit { font-size: 0.85rem; color: var(--muted); }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
  .card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 8px; padding: 20px;
  }
  .card h3 { font-size: 1rem; margin-bottom: 12px; color: var(--text); }
  .card.full { grid-column: 1 / -1; }
  canvas { max-height: 340px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; }
  td { color: var(--text); }
  tr:hover td { background: rgba(88,166,255,0.05); }
  .insights { list-style: none; padding: 0; }
  .insight {
    background: var(--card); border-left: 3px solid var(--accent);
    padding: 12px 16px; margin-bottom: 10px; border-radius: 0 6px 6px 0;
    font-size: 0.9rem; line-height: 1.6;
  }
  .insight:nth-child(2) { border-left-color: var(--orange); }
  .insight:nth-child(3) { border-left-color: var(--red); }
  .insight:nth-child(4) { border-left-color: var(--orange); }
  .insight:nth-child(5) { border-left-color: var(--purple); }
  .insight:nth-child(6) { border-left-color: var(--green); }
  .insight:nth-child(7) { border-left-color: var(--teal); }
  .insight:nth-child(8) { border-left-color: var(--accent); }
  @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>

<h1>BIP AI &mdash; Cycle Time Dashboard</h1>
<p class="subtitle">
  True cycle time (In Progress &rarr; Done) in business days (excl. weekends &amp; US holidays) &middot;
  """ + str(overall['with_cycle']) + """ issues with Story Points across 17 sprints (FY25Q4.1 &ndash; FY26Q2.3)
</p>

<!-- KPIs -->
<div class="kpi-row">
  <div class="kpi">
    <div class="label">Median Cycle Time</div>
    <div class="value">""" + str(overall['cycle_median']) + """<span class="unit"> days</span></div>
  </div>
  <div class="kpi">
    <div class="label">Mean Cycle Time</div>
    <div class="value">""" + str(overall['cycle_mean']) + """<span class="unit"> days</span></div>
  </div>
  <div class="kpi">
    <div class="label">85th Percentile</div>
    <div class="value">""" + str(overall['cycle_p85']) + """<span class="unit"> days</span></div>
  </div>
  <div class="kpi">
    <div class="label">95th Percentile</div>
    <div class="value">""" + str(overall['cycle_p95']) + """<span class="unit"> days</span></div>
  </div>
  <div class="kpi">
    <div class="label">Active Work (median)</div>
    <div class="value">""" + str(overall['active_median']) + """<span class="unit"> days</span></div>
  </div>
</div>

<!-- Charts Row 1: Cycle Time Trend + Throughput -->
<div class="grid">
  <div class="card">
    <h3>Cycle Time Trend by Sprint (days)</h3>
    <canvas id="chartTrend"></canvas>
  </div>
  <div class="card">
    <h3>Sprint Throughput (Done issues &amp; Story Points)</h3>
    <canvas id="chartThru"></canvas>
  </div>
</div>

<!-- Charts Row 2: Histogram + Status Pie -->
<div class="grid">
  <div class="card">
    <h3>Cycle Time Distribution</h3>
    <canvas id="chartHist"></canvas>
  </div>
  <div class="card">
    <h3>Time in Status (overall %)</h3>
    <canvas id="chartStatus"></canvas>
  </div>
</div>

<!-- Charts Row 3: Stacked Status by Sprint + Scatter -->
<div class="grid">
  <div class="card">
    <h3>Avg Status Duration by Sprint (days)</h3>
    <canvas id="chartStacked"></canvas>
  </div>
  <div class="card">
    <h3>Cycle Time Scatter (all issues)</h3>
    <canvas id="chartScatter"></canvas>
  </div>
</div>

<!-- Insights -->
<div class="card full" style="margin-bottom:24px">
  <h3>Key Insights</h3>
  <ul class="insights">
    """ + insights_html + """
  </ul>
</div>

<!-- Sprint Detail Table -->
<div class="card full" style="margin-bottom:24px">
  <h3>Sprint Detail</h3>
  <div style="overflow-x:auto">
  <table>
    <thead><tr>
      <th>Sprint</th><th>Throughput</th><th>Story Pts</th><th>Analyzed</th>
      <th>Median CT</th><th>Mean CT</th><th>P85 CT</th>
      <th>Avg IP</th><th>Avg Test</th><th>Avg PR</th><th>Avg Blocked</th>
    </tr></thead>
    <tbody>
      """ + sprint_detail_rows + """
    </tbody>
  </table>
  </div>
</div>

<!-- Longest Cycle Times -->
<div class="grid">
  <div class="card">
    <h3>Top 10 Longest Cycle Times</h3>
    <table>
      <thead><tr><th>Key</th><th>Sprint</th><th>Cycle (d)</th><th>IP (d)</th><th>Test (d)</th><th>Blocked (d)</th></tr></thead>
      <tbody>""" + longest_rows + """</tbody>
    </table>
  </div>
  <div class="card">
    <h3>Top 10 Most Blocked Issues</h3>
    <table>
      <thead><tr><th>Key</th><th>Sprint</th><th>Blocked (d)</th><th>Cycle (d)</th></tr></thead>
      <tbody>""" + top_blocked_rows + """</tbody>
    </table>
  </div>
</div>

<script>
const sprintLabels = """ + sprint_labels_js + """;
const cycleMedians = """ + cycle_medians_js + """;
const cycleMeans   = """ + cycle_means_js + """;
const cycleP85s    = """ + cycle_p85s_js + """;
const throughputs  = """ + throughputs_js + """;
const storyPoints  = """ + story_points_js + """;
const avgIP        = """ + avg_ip_js + """;
const avgTest      = """ + avg_test_js + """;
const avgPR        = """ + avg_pr_js + """;
const avgBlocked   = """ + avg_blk_js + """;
const histLabels   = """ + hist_labels_js + """;
const histCounts   = """ + hist_counts_js + """;
const statusLabels = """ + status_labels_js + """;
const statusValues = """ + status_values_js + """;
const scatterData  = """ + scatter_js + """;

Chart.defaults.color = '#8b949e';
Chart.defaults.borderColor = '#30363d';
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial";

// === Cycle Time Trend ===
new Chart(document.getElementById('chartTrend'), {
  type: 'line',
  data: {
    labels: sprintLabels,
    datasets: [
      { label: 'Median', data: cycleMedians, borderColor: '#58a6ff', backgroundColor: 'rgba(88,166,255,0.1)',
        fill: true, tension: 0.3, pointRadius: 4, borderWidth: 2, spanGaps: true },
      { label: 'Mean', data: cycleMeans, borderColor: '#d29922', borderDash: [5,3],
        tension: 0.3, pointRadius: 3, borderWidth: 2, fill: false, spanGaps: true },
      { label: 'P85', data: cycleP85s, borderColor: '#f85149', borderDash: [2,4],
        tension: 0.3, pointRadius: 3, borderWidth: 1.5, fill: false, spanGaps: true },
    ]
  },
  options: {
    responsive: true,
    plugins: { legend: { position: 'top', labels: { boxWidth: 14, padding: 12 } } },
    scales: {
      x: { ticks: { maxRotation: 45, font: { size: 10 } } },
      y: { title: { display: true, text: 'Days' }, beginAtZero: true }
    }
  }
});

// === Throughput ===
new Chart(document.getElementById('chartThru'), {
  type: 'bar',
  data: {
    labels: sprintLabels,
    datasets: [
      { label: 'Done Issues', data: throughputs, yAxisID: 'y',
        backgroundColor: 'rgba(57,211,83,0.6)', borderColor: '#3fb950', borderWidth: 1 },
      { label: 'Story Points', data: storyPoints, yAxisID: 'y1',
        backgroundColor: 'rgba(88,166,255,0.45)', borderColor: '#58a6ff', borderWidth: 1 }
    ]
  },
  options: {
    responsive: true,
    plugins: { legend: { position: 'top', labels: { boxWidth: 14, padding: 12 } } },
    scales: {
      x: { ticks: { maxRotation: 45, font: { size: 10 } } },
      y:  { position: 'left',  title: { display: true, text: 'Issues' }, beginAtZero: true },
      y1: { position: 'right', title: { display: true, text: 'Story Points' }, beginAtZero: true,
            grid: { drawOnChartArea: false } }
    }
  }
});

// === Histogram ===
new Chart(document.getElementById('chartHist'), {
  type: 'bar',
  data: {
    labels: histLabels,
    datasets: [{ label: 'Issues', data: histCounts,
                 backgroundColor: 'rgba(88,166,255,0.6)', borderColor: '#58a6ff', borderWidth: 1 }]
  },
  options: {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { title: { display: true, text: 'Count' }, beginAtZero: true } }
  }
});

// === Status Pie ===
new Chart(document.getElementById('chartStatus'), {
  type: 'doughnut',
  data: {
    labels: statusLabels,
    datasets: [{
      data: statusValues,
      backgroundColor: ['#58a6ff', '#d29922', '#bc8cff', '#f85149'],
      borderWidth: 0
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { position: 'right', labels: { padding: 16 } },
      tooltip: { callbacks: { label: ctx => ctx.label + ': ' + ctx.parsed + '%' } }
    }
  }
});

// === Stacked Status by Sprint ===
new Chart(document.getElementById('chartStacked'), {
  type: 'bar',
  data: {
    labels: sprintLabels,
    datasets: [
      { label: 'In Progress', data: avgIP, backgroundColor: 'rgba(88,166,255,0.7)' },
      { label: 'In Testing', data: avgTest, backgroundColor: 'rgba(210,153,34,0.7)' },
      { label: 'Peer Review Needed', data: avgPR, backgroundColor: 'rgba(188,140,255,0.7)' },
      { label: 'Blocked', data: avgBlocked, backgroundColor: 'rgba(248,81,73,0.7)' },
    ]
  },
  options: {
    responsive: true,
    plugins: { legend: { position: 'top', labels: { boxWidth: 14, padding: 12 } } },
    scales: {
      x: { stacked: true, ticks: { maxRotation: 45, font: { size: 10 } } },
      y: { stacked: true, title: { display: true, text: 'Days' }, beginAtZero: true }
    }
  }
});

// === Scatter Plot ===
new Chart(document.getElementById('chartScatter'), {
  type: 'scatter',
  data: {
    datasets: [{
      label: 'Cycle Time',
      data: scatterData.map(d => ({ x: d.x, y: d.y })),
      backgroundColor: 'rgba(88,166,255,0.5)',
      pointRadius: 4,
      pointHoverRadius: 7,
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: function(ctx) {
            const d = scatterData[ctx.dataIndex];
            return d.key + ' (' + d.sprint.replace('BIP AI ','') + '): ' + d.y + ' days';
          }
        }
      }
    },
    scales: {
      x: { title: { display: true, text: 'Issue #' }, ticks: { display: false } },
      y: { title: { display: true, text: 'Cycle Time (days)' }, beginAtZero: true }
    }
  }
});
</script>

<p style="color:var(--muted);text-align:center;margin-top:32px;font-size:0.8rem">
  Generated from all sprint issues &middot;
  Cycle time = first In Progress &rarr; final Done (business days, excl. weekends &amp; US holidays) &middot;
  Status durations from Jira transition histories
</p>
</body>
</html>
"""

with open(OUTPUT_HTML, "w") as f:
    f.write(html)
print(f"Wrote {OUTPUT_HTML}")
print(f"\nOverall: median={overall['cycle_median']}d  mean={overall['cycle_mean']}d  p85={overall['cycle_p85']}d  p95={overall['cycle_p95']}d")
print(f"Status split: {status_pct}")
