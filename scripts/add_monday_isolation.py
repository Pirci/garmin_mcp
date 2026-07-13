#!/usr/bin/env python3
"""Add Monday isolation workouts to the 12-week schedule."""
import json
import os
import sys
from datetime import date, timedelta

from garminconnect import Garmin

tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
garmin = Garmin()
garmin.login(tokenstore)
print("Logged in successfully.", file=sys.stderr)

# Current isolation workout IDs
ISOLATION_IDS = {
    "F1": 1630805008,
    "F2": 1630805026,
    "F3": 1630805040,
}

# Also update workout names to include Pzrts
# We need to fetch, update name, and re-upload... or just rename via API
# Actually, let's just schedule Mondays - the workout content is the same

start_monday = date(2026, 7, 13)

schedule = []
for week in range(12):
    if week < 4:
        phase = "F1"
    elif week < 8:
        phase = "F2"
    else:
        phase = "F3"

    monday = start_monday + timedelta(weeks=week)
    schedule.append({
        "date": str(monday),
        "workout_id": ISOLATION_IDS[phase],
        "label": f"W{week+1} Pzt Izole",
    })

print(f"Scheduling {len(schedule)} Monday sessions...", file=sys.stderr)

success = 0
for item in schedule:
    day = date.fromisoformat(item["date"]).strftime("%A")
    print(f"  {item['label']} -> {item['date']} ({day})...", file=sys.stderr, end=" ")
    try:
        url = f"workout-service/schedule/{item['workout_id']}"
        response = garmin.client.post("connectapi", url, json={"date": item["date"]})
        if response.status_code == 200:
            print("OK", file=sys.stderr)
            success += 1
        else:
            print(f"HTTP {response.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)

print(f"\nDone: {success}/{len(schedule)} scheduled.", file=sys.stderr)
