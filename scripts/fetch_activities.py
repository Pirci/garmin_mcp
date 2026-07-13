#!/usr/bin/env python3
"""Fetch walking and running activities from Garmin Connect and save as fixtures."""
import json
import os
import sys
from datetime import date, timedelta

from garminconnect import Garmin

tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"

garmin = Garmin()
garmin.login(tokenstore)
print("Logged in successfully.", file=sys.stderr)

end_date = date.today()
start_date = end_date - timedelta(days=180)

fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "garmin")
os.makedirs(fixtures_dir, exist_ok=True)

for activity_type in ("walking", "running"):
    print(f"Fetching {activity_type} activities ({start_date} to {end_date})...", file=sys.stderr)

    all_activities = []
    page = 0
    page_size = 100

    while True:
        activities = garmin.connectapi(
            garmin.garmin_connect_activities,
            params={
                "startDate": str(start_date),
                "endDate": str(end_date),
                "activityType": activity_type,
                "start": str(page * page_size),
                "limit": str(page_size),
            },
        )
        if not activities:
            break
        all_activities.extend(activities)
        if len(activities) < page_size:
            break
        page += 1

    print(f"  Found {len(all_activities)} {activity_type} activities.", file=sys.stderr)

    out_path = os.path.join(fixtures_dir, f"{activity_type}_activities.json")
    with open(out_path, "w") as f:
        json.dump(all_activities, f, indent=2, default=str)
    print(f"  Saved to {out_path}", file=sys.stderr)

print("Done!", file=sys.stderr)
