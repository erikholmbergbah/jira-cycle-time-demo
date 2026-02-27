#!/usr/bin/env python3
"""Check for cancelled issues in the dataset."""
import json
from datetime import datetime

data = json.load(open('issue_data_full.json'))
excluded = {'BIP-25393','BIP-25703','BIP-26294','BIP-26538','BIP-27314','BIP-28723'}
no_sp = {'BIP-30535','BIP-30530','BIP-30351','BIP-30306','BIP-29982','BIP-29937',
         'BIP-29936','BIP-29536','BIP-29529','BIP-29147','BIP-28949','BIP-28766',
         'BIP-25707','BIP-25706','BIP-25705','BIP-25704','BIP-25703','BIP-25393',
         'BIP-25392','BIP-25110','BIP-24894','BIP-23877'}

canceled = []
for k, v in data.items():
    if k in excluded or k in no_sp:
        continue
    cm = v.get('canceled_minutes', 0)
    if cm and cm > 0:
        canceled.append((k, cm, v))

print(f"Issues with canceled_minutes > 0: {len(canceled)}")
print()
for k, cm, v in sorted(canceled, key=lambda x: -x[1]):
    days_canceled = cm / 60 / 24
    ip = v.get('in_progress_minutes', 0) / 60 / 24
    wall = None
    if v.get('first_active') and v.get('done_at'):
        fa = datetime.fromisoformat(v['first_active'].replace('Z', '+00:00'))
        da = datetime.fromisoformat(v['done_at'].replace('Z', '+00:00'))
        wall = (da - fa).total_seconds() / 86400
    wall_str = f", wall={wall:.1f}d" if wall else ""
    print(f"  {k}: canceled={days_canceled:.1f}d, ip={ip:.1f}d{wall_str}")

# Also check: are there issues whose ONLY active time was in Canceled status?
print()
print("--- Issues where canceled time is majority of active time ---")
for k, cm, v in sorted(canceled, key=lambda x: -x[1]):
    ip = v.get('in_progress_minutes', 0)
    testing = v.get('in_testing_minutes', 0)
    review = v.get('peer_review_minutes', 0)
    blocked = v.get('blocked_minutes', 0)
    total_active = ip + testing + review + blocked + cm
    if total_active > 0:
        pct = cm / total_active * 100
        if pct > 50:
            print(f"  {k}: {pct:.0f}% canceled ({cm/60/24:.1f}d of {total_active/60/24:.1f}d active)")
