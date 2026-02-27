#!/usr/bin/env python3
"""
Fetch all issue keys with Story Points for all 17 BIP AI sprints.
Saves results to sp_keys_by_sprint.json and sp_keys.json.
Requires manual MCP calls - this just generates the JQLs needed.
"""

SPRINTS = [
    "BIP AI FY25Q4.1", "BIP AI FY25Q4.2", "BIP AI FY25Q4.3",
    "BIP AI FY26Q1.1", "BIP AI FY26Q1.2", "BIP AI FY26Q1.3",
    "BIP AI FY26Q2.1", "BIP AI FY26Q2.2", "BIP AI FY26Q2.3",
    # These are the early ones
    "BIP AI Sprint 1", "BIP AI Sprint 2", "BIP AI Sprint 3",
    "BIP AI Sprint 4", "BIP AI Sprint 5", "BIP AI Sprint 6",
    "BIP AI Sprint 7", "BIP AI Sprint 8",
]

for sp in SPRINTS:
    jql = f'project = BIP AND sprint = "{sp}" AND "Story Points" is not EMPTY AND status = Done'
    print(f'{sp}: {jql}')
