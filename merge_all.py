#!/usr/bin/env python3
"""Save indices 90-99 (batch 10) and merge ALL batch files into issue_data_all.json."""
import json, os

DIR = os.path.dirname(__file__)

# Batch 10 data (indices 90-99)
BATCH10 = [
    ("BIP-30531", "2026-01-23T07:58:59.388000-05:00", "2026-02-06T13:01:17.836000-05:00", "2026-01-27T17:20:05.867000-05:00", "2026-02-06T13:01:17.844000-05:00", 6321, 12548, 460, 1132, 0, 0),
    ("BIP-30555", "2026-01-23T07:59:10.756000-05:00", "2026-01-30T09:27:42.440000-05:00", "2026-01-26T09:33:51.830000-05:00", "2026-01-30T09:27:42.444000-05:00", 4414, 1476, 4276, 0, 0, 0),
    ("BIP-30584", "2026-01-23T07:59:28.621000-05:00", "2026-01-30T10:34:29.797000-05:00", "2026-01-27T10:51:52.461000-05:00", "2026-01-30T10:34:29.803000-05:00", 5932, 4302, 0, 0, 0, 0),
    ("BIP-30523", "2026-01-23T07:58:55.613000-05:00", "2026-02-06T10:41:51.093000-05:00", "2026-01-30T10:18:12.866000-05:00", "2026-02-06T10:41:51.097000-05:00", 10219, 2, 0, 10100, 0, 0),
    ("BIP-30939", "2026-02-06T07:20:51.507000-05:00", "2026-02-13T10:28:33.055000-05:00", "2026-02-09T10:36:45.062000-05:00", "2026-02-13T10:28:33.059000-05:00", 4515, 3263, 2487, 0, 0, 0),
    ("BIP-30951", "2026-02-06T07:20:56.789000-05:00", "2026-02-20T14:40:21.336000-05:00", "2026-02-09T10:37:07.851000-05:00", "2026-02-20T14:40:21.342000-05:00", 4516, 1440, 14642, 0, 0, 0),
    ("BIP-30911", "2026-02-06T07:20:37.342000-05:00", "2026-02-20T14:14:19.267000-05:00", "2026-02-09T10:33:46.798000-05:00", "2026-02-20T14:14:19.271000-05:00", 4513, 15719, 341, 0, 0, 0),
    ("BIP-30897", "2026-02-06T07:20:30.189000-05:00", "2026-02-20T10:01:46.394000-05:00", "2026-02-17T10:30:34.077000-05:00", "2026-02-20T10:01:46.401000-05:00", 16030, 301, 3989, 0, 0, 0),
    ("BIP-30907", "2026-02-06T07:20:35.252000-05:00", "2026-02-20T16:01:12.468000-05:00", "2026-02-09T10:36:05.220000-05:00", "2026-02-20T16:01:12.470000-05:00", 4515, 15844, 320, 0, 0, 0),
    ("BIP-30978", "2026-02-06T12:04:01.826000-05:00", "2026-02-18T09:56:48.192000-05:00", "2026-02-09T17:46:36.065000-05:00", "2026-02-18T09:56:48.197000-05:00", 4662, 3889, 332, 8267, 0, 0),
]

# Save batch 10
b10 = {}
for row in BATCH10:
    key, created, res, first_active, done_at, bl, ip, tt, pr, bk, cn = row
    b10[key] = {
        "created": created, "resolution_date": res, "first_active": first_active,
        "done_at": done_at, "backlog_minutes": bl, "in_progress_minutes": ip,
        "in_testing_minutes": tt, "peer_review_minutes": pr,
        "blocked_minutes": bk, "canceled_minutes": cn,
    }
with open(os.path.join(DIR, "issue_data_batch_10.json"), "w") as f:
    json.dump(b10, f, indent=2)
print(f"Saved batch 10: {len(b10)} issues")

# Merge all batch files
all_data = {}
batch_files = [
    "issue_data_batch_0_1.json",   # 20 issues (indices 0-19)
    "issue_data_batch_2_3.json",   # 10 issues (indices 20-29)
    "issue_data_batch_4.json",     # 10 issues (indices 30-39)
    "issue_data_batches_5_9.json", # 50 issues (indices 40-89)
    "issue_data_batch_10.json",    # 10 issues (indices 90-99)
]
for bf in batch_files:
    path = os.path.join(DIR, bf)
    with open(path) as f:
        data = json.load(f)
    print(f"  {bf}: {len(data)} issues")
    all_data.update(data)

outpath = os.path.join(DIR, "issue_data_all.json")
with open(outpath, "w") as f:
    json.dump(all_data, f, indent=2)
print(f"\nMerged total: {len(all_data)} issues -> {outpath}")
