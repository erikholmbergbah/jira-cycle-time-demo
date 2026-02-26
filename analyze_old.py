#!/usr/bin/env python3
"""
BIP AI Sprint Cycle Time Analysis
Computes metrics from collected Jira data and generates an HTML dashboard.
"""
import json, os, statistics
from datetime import datetime, timedelta
from collections import defaultdict, Counter

DATA_DIR = "/Users/erikholmberg/Documents/Code/jira-cycle-time-demo"
ISSUES_DIR = os.path.join(DATA_DIR, "sprint_issues")

# Sprint ordering
SPRINT_ORDER = [
    "BIP AI FY25Q4.1", "BIP AI FY25Q4.2", "BIP AI FY25Q4.3", "BIP AI FY25Q4.4",
    "BIP AI FY25Q4.5", "BIP AI FY25Q4.6", "BIP AI FY25Q4.7",
    "BIP AI FY26Q1.1", "BIP AI FY26Q1.2", "BIP AI FY26Q1.3", "BIP AI FY26Q1.4",
    "BIP AI FY26Q1.5", "BIP AI FY26Q1.6", "BIP AI FY26Q1.7",
    "BIP AI FY26Q2.1", "BIP AI FY26Q2.2", "BIP AI FY26Q2.3",
]

SPRINT_DATES = {
    "BIP AI FY25Q4.1": ("2025-07-07", "2025-07-18"),
    "BIP AI FY25Q4.2": ("2025-07-21", "2025-08-01"),
    "BIP AI FY25Q4.3": ("2025-08-04", "2025-08-15"),
    "BIP AI FY25Q4.4": ("2025-08-18", "2025-08-29"),
    "BIP AI FY25Q4.5": ("2025-09-01", "2025-09-12"),
    "BIP AI FY25Q4.6": ("2025-09-15", "2025-09-26"),
    "BIP AI FY25Q4.7": ("2025-09-29", "2025-10-03"),
    "BIP AI FY26Q1.1": ("2025-10-06", "2025-10-17"),
    "BIP AI FY26Q1.2": ("2025-10-20", "2025-10-31"),
    "BIP AI FY26Q1.3": ("2025-11-03", "2025-11-14"),
    "BIP AI FY26Q1.4": ("2025-11-17", "2025-11-28"),
    "BIP AI FY26Q1.5": ("2025-12-01", "2025-12-12"),
    "BIP AI FY26Q1.6": ("2025-12-15", "2025-12-26"),
    "BIP AI FY26Q1.7": ("2025-12-29", "2026-01-09"),
    "BIP AI FY26Q2.1": ("2026-01-12", "2026-01-23"),
    "BIP AI FY26Q2.2": ("2026-01-26", "2026-02-06"),
    "BIP AI FY26Q2.3": ("2026-02-09", "2026-02-20"),
}

def parse_date(date_str):
    """Parse Jira date string to datetime."""
    if not date_str:
        return None
    # Handle various formats
    for fmt in ["%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f"]:
        try:
            return datetime.fromisoformat(date_str.replace('+0000', '+00:00').replace('-0400', '-04:00').replace('-0500', '-05:00'))
        except:
            continue
    try:
        return datetime.fromisoformat(date_str)
    except:
        return None

def load_sprint_data():
    """Load all sprint issue data."""
    sprints = {}
    for sprint_name in SPRINT_ORDER:
        fname = sprint_name.replace(' ', '_') + '.json'
        filepath = os.path.join(ISSUES_DIR, fname)
        if os.path.exists(filepath):
            with open(filepath) as f:
                sprints[sprint_name] = json.load(f)
    return sprints

def compute_metrics(sprints):
    """Compute all metrics for the dashboard."""
    metrics = {
        'sprint_labels': [],
        'sprint_short_labels': [],
        'total_issues': [],
        'done_count': [],
        'in_progress_count': [],
        'other_count': [],
        'completion_rate': [],
        'avg_cycle_time': [],
        'median_cycle_time': [],
        'p85_cycle_time': [],
        'cycle_times_all': [],
        'status_distribution': [],
        'team_breakdown': defaultdict(lambda: []),
        'assignee_data': defaultdict(lambda: defaultdict(int)),
        'quarter_totals': defaultdict(lambda: {'done': 0, 'total': 0, 'cycle_times': []}),
    }
    
    all_teams = set()
    all_statuses = set()
    
    for sprint_name in SPRINT_ORDER:
        if sprint_name not in sprints:
            continue
            
        issues = sprints[sprint_name]
        short_label = sprint_name.replace('BIP AI ', '')
        metrics['sprint_labels'].append(sprint_name)
        metrics['sprint_short_labels'].append(short_label)
        
        # Determine quarter
        if 'FY25Q4' in sprint_name:
            quarter = 'FY25 Q4'
        elif 'FY26Q1' in sprint_name:
            quarter = 'FY26 Q1'
        else:
            quarter = 'FY26 Q2'
        
        # Count statuses
        total = len(issues)
        done = sum(1 for i in issues if i.get('status', {}).get('category') == 'Done')
        in_progress = sum(1 for i in issues if i.get('status', {}).get('name') in ['In Progress', 'In Testing', 'Peer Review Needed'])
        other = total - done - in_progress
        
        metrics['total_issues'].append(total)
        metrics['done_count'].append(done)
        metrics['in_progress_count'].append(in_progress)
        metrics['other_count'].append(other)
        metrics['completion_rate'].append(round(done / total * 100, 1) if total > 0 else 0)
        
        # Status distribution
        status_counts = Counter()
        for issue in issues:
            status_name = issue.get('status', {}).get('name', 'Unknown')
            status_counts[status_name] += 1
            all_statuses.add(status_name)
        metrics['status_distribution'].append(dict(status_counts))
        
        # Cycle time (created -> updated for Done issues)
        cycle_times = []
        for issue in issues:
            if issue.get('status', {}).get('category') == 'Done':
                created = parse_date(issue.get('created'))
                updated = parse_date(issue.get('updated'))
                if created and updated:
                    delta = (updated - created).total_seconds() / 86400  # days
                    if delta >= 0:
                        cycle_times.append(delta)
        
        if cycle_times:
            metrics['avg_cycle_time'].append(round(statistics.mean(cycle_times), 1))
            metrics['median_cycle_time'].append(round(statistics.median(cycle_times), 1))
            sorted_ct = sorted(cycle_times)
            p85_idx = int(len(sorted_ct) * 0.85)
            metrics['p85_cycle_time'].append(round(sorted_ct[min(p85_idx, len(sorted_ct)-1)], 1))
        else:
            metrics['avg_cycle_time'].append(0)
            metrics['median_cycle_time'].append(0)
            metrics['p85_cycle_time'].append(0)
        
        metrics['cycle_times_all'].extend(cycle_times)
        
        # Quarter aggregation
        metrics['quarter_totals'][quarter]['done'] += done
        metrics['quarter_totals'][quarter]['total'] += total
        metrics['quarter_totals'][quarter]['cycle_times'].extend(cycle_times)
        
        # Team breakdown (from labels)
        team_counts = Counter()
        for issue in issues:
            labels = issue.get('labels', [])
            teams_found = []
            for label in labels:
                if label in ['MLOps_Eng', 'Infra_Cloud', 'BIPAI_Tenant', 'Solutions_Eng', 'Data_Science', 'it_ai']:
                    teams_found.append(label)
                    all_teams.add(label)
            if not teams_found:
                teams_found = ['Untagged']
                all_teams.add('Untagged')
            for team in teams_found:
                team_counts[team] += 1
        
        for team in all_teams:
            metrics['team_breakdown'][team].append(team_counts.get(team, 0))
        
        # Assignee data
        for issue in issues:
            if issue.get('status', {}).get('category') == 'Done':
                assignee = issue.get('assignee', {})
                if assignee:
                    name = assignee.get('display_name', 'Unassigned')
                else:
                    name = 'Unassigned'
                metrics['assignee_data'][name][sprint_name] += 1
    
    # Ensure all team arrays are same length
    n_sprints = len(metrics['sprint_labels'])
    for team in all_teams:
        while len(metrics['team_breakdown'][team]) < n_sprints:
            metrics['team_breakdown'][team].append(0)
    
    metrics['all_teams'] = sorted(all_teams)
    metrics['all_statuses'] = sorted(all_statuses)
    
    return metrics

# Status duration data from sampled issues
STATUS_DURATION_SAMPLES = [
    {"key": "BIP-23877", "status_summary": [
        {"status": "In Progress", "total_duration_minutes": 197279},
        {"status": "In Testing", "total_duration_minutes": 5760},
        {"status": "Backlog", "total_duration_minutes": 1236},
        {"status": "Peer Review Needed", "total_duration_minutes": 293},
    ]},
    {"key": "BIP-26054", "status_summary": [
        {"status": "In Progress", "total_duration_minutes": 13673},
        {"status": "Backlog", "total_duration_minutes": 5777},
        {"status": "In Testing", "total_duration_minutes": 829},
    ]},
    {"key": "BIP-26175", "status_summary": [
        {"status": "In Testing", "total_duration_minutes": 1530},
        {"status": "Backlog", "total_duration_minutes": 201},
        {"status": "In Progress", "total_duration_minutes": 0},
    ]},
    {"key": "BIP-26005", "status_summary": [
        {"status": "Backlog", "total_duration_minutes": 14424},
        {"status": "In Progress", "total_duration_minutes": 4306},
        {"status": "In Testing", "total_duration_minutes": 384},
    ]},
    {"key": "BIP-25392", "status_summary": [
        {"status": "In Progress", "total_duration_minutes": 68674},
        {"status": "In Testing", "total_duration_minutes": 397},
        {"status": "Backlog", "total_duration_minutes": 2},
    ]},
    {"key": "BIP-26295", "status_summary": [
        {"status": "Backlog", "total_duration_minutes": 45243},
        {"status": "In Progress", "total_duration_minutes": 14375},
        {"status": "Blocked", "total_duration_minutes": 2},
        {"status": "In Testing", "total_duration_minutes": 0},
    ]},
    {"key": "BIP-26769", "status_summary": [
        {"status": "Backlog", "total_duration_minutes": 18685},
        {"status": "Blocked", "total_duration_minutes": 18606},
        {"status": "In Progress", "total_duration_minutes": 3084},
        {"status": "Peer Review Needed", "total_duration_minutes": 1569},
    ]},
    {"key": "BIP-26985", "status_summary": [
        {"status": "Backlog", "total_duration_minutes": 10016},
        {"status": "In Progress", "total_duration_minutes": 8697},
        {"status": "Peer Review Needed", "total_duration_minutes": 7206},
        {"status": "In Testing", "total_duration_minutes": 7114},
        {"status": "Blocked", "total_duration_minutes": 4318},
    ]},
    {"key": "BIP-27277", "status_summary": [
        {"status": "Backlog", "total_duration_minutes": 38462},
        {"status": "In Progress", "total_duration_minutes": 22365},
        {"status": "In Testing", "total_duration_minutes": 1104},
    ]},
    {"key": "BIP-28437", "status_summary": [
        {"status": "Backlog", "total_duration_minutes": 51551},
        {"status": "Blocked", "total_duration_minutes": 4292},
        {"status": "In Testing", "total_duration_minutes": 3134},
        {"status": "In Progress", "total_duration_minutes": 2884},
        {"status": "Peer Review Needed", "total_duration_minutes": 67},
    ]},
    {"key": "BIP-28888", "status_summary": [
        {"status": "Backlog", "total_duration_minutes": 24530},
        {"status": "Peer Review Needed", "total_duration_minutes": 6868},
        {"status": "In Progress", "total_duration_minutes": 3035},
    ]},
    {"key": "BIP-29508", "status_summary": [
        {"status": "Backlog", "total_duration_minutes": 44720},
        {"status": "Peer Review Needed", "total_duration_minutes": 1326},
        {"status": "In Testing", "total_duration_minutes": 260},
        {"status": "In Progress", "total_duration_minutes": 0},
    ]},
    {"key": "BIP-30292", "status_summary": [
        {"status": "Backlog", "total_duration_minutes": 28346},
        {"status": "In Testing", "total_duration_minutes": 5807},
        {"status": "Peer Review Needed", "total_duration_minutes": 2805},
        {"status": "In Progress", "total_duration_minutes": 1820},
    ]},
    {"key": "BIP-30311", "status_summary": [
        {"status": "Backlog", "total_duration_minutes": 49459},
        {"status": "In Progress", "total_duration_minutes": 9953},
        {"status": "In Testing", "total_duration_minutes": 1227},
        {"status": "Peer Review Needed", "total_duration_minutes": 1},
    ]},
]

def compute_status_duration_metrics():
    """Compute average time spent in each status from sampled issues."""
    status_totals = defaultdict(list)
    
    for sample in STATUS_DURATION_SAMPLES:
        total_minutes = sum(s['total_duration_minutes'] for s in sample['status_summary'])
        if total_minutes == 0:
            continue
        for status_entry in sample['status_summary']:
            status = status_entry['status']
            mins = status_entry['total_duration_minutes']
            days = mins / 1440  # convert to days
            pct = (mins / total_minutes) * 100
            status_totals[status].append({'days': days, 'pct': pct, 'minutes': mins})
    
    result = {}
    for status, entries in status_totals.items():
        if status == 'Done':
            continue
        result[status] = {
            'avg_days': round(statistics.mean([e['days'] for e in entries]), 1),
            'median_days': round(statistics.median([e['days'] for e in entries]), 1),
            'avg_pct': round(statistics.mean([e['pct'] for e in entries]), 1),
            'count': len(entries),
        }
    
    return result

if __name__ == '__main__':
    sprints = load_sprint_data()
    metrics = compute_metrics(sprints)
    status_metrics = compute_status_duration_metrics()
    
    print("=== Sprint Summary ===")
    for i, sprint in enumerate(metrics['sprint_labels']):
        print(f"{metrics['sprint_short_labels'][i]:>12} | Total: {metrics['total_issues'][i]:>3} | Done: {metrics['done_count'][i]:>3} | Rate: {metrics['completion_rate'][i]:>5.1f}% | Avg CT: {metrics['avg_cycle_time'][i]:>5.1f}d | Med CT: {metrics['median_cycle_time'][i]:>5.1f}d")
    
    print("\n=== Quarter Summary ===")
    for q, data in sorted(metrics['quarter_totals'].items()):
        rate = data['done'] / data['total'] * 100 if data['total'] > 0 else 0
        avg_ct = statistics.mean(data['cycle_times']) if data['cycle_times'] else 0
        print(f"{q}: {data['done']}/{data['total']} done ({rate:.1f}%), Avg CT: {avg_ct:.1f}d")
    
    print("\n=== Status Duration (from sampled issues) ===")
    for status, data in sorted(status_metrics.items(), key=lambda x: -x[1]['avg_days']):
        print(f"{status:>25}: Avg {data['avg_days']:>5.1f}d, Median {data['median_days']:>5.1f}d, Avg {data['avg_pct']:>5.1f}% of total time (n={data['count']})")
    
    # Save metrics for HTML generation
    output = {
        'metrics': {k: v for k, v in metrics.items() if k != 'quarter_totals' and k != 'team_breakdown' and k != 'assignee_data'},
        'quarter_totals': {k: {'done': v['done'], 'total': v['total'], 'avg_ct': round(statistics.mean(v['cycle_times']), 1) if v['cycle_times'] else 0} for k, v in metrics['quarter_totals'].items()},
        'team_breakdown': dict(metrics['team_breakdown']),
        'top_contributors': dict(sorted(
            [(name, sum(sprints.values())) for name, sprints in metrics['assignee_data'].items()],
            key=lambda x: -x[1]
        )[:20]),
        'status_durations': status_metrics,
    }
    
    with open(os.path.join(DATA_DIR, 'computed_metrics.json'), 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print("\nMetrics saved to computed_metrics.json")
