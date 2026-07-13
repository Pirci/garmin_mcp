#!/usr/bin/env python3
"""Schedule the 90-day strength program on Garmin Connect calendar."""
import json
import os
import sys
from datetime import date, timedelta

from garminconnect import Garmin

tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
garmin = Garmin()
garmin.login(tokenstore)
print("Logged in successfully.", file=sys.stderr)

# Workout IDs from upload
WORKOUTS = {
    "F1_HEAVY_A": 1630789034,
    "F1_HEAVY_B": 1630789038,
    "F1_ISOLATION": 1630789044,
    "F2_HEAVY_A": 1630789049,
    "F2_HEAVY_B": 1630789054,
    "F2_ISOLATION": 1630789058,
    "F3_HEAVY_A": 1630789060,
    "F3_HEAVY_B": 1630789062,
    "F3_ISOLATION": 1630789067,
}

# Program starts tomorrow (Monday July 14, 2026)
# Week starts on Monday
start_date = date(2026, 7, 14)

# Build 12-week schedule
# Mon=0 rest, Tue=1 Heavy A, Wed=2 Isolation, Thu=3 Heavy B, Fri=4 Isolation, Sat=5 Heavy A, Sun=6 Isolation
schedule = []

for week in range(12):
    if week < 4:
        phase = "F1"
    elif week < 8:
        phase = "F2"
    else:
        phase = "F3"

    monday = start_date + timedelta(weeks=week)

    # Tuesday - Heavy A
    tue = monday + timedelta(days=1)
    schedule.append({"date": str(tue), "workout_id": WORKOUTS[f"{phase}_HEAVY_A"], "label": f"W{week+1} Sal Heavy A"})

    # Wednesday - Isolation
    wed = monday + timedelta(days=2)
    schedule.append({"date": str(wed), "workout_id": WORKOUTS[f"{phase}_ISOLATION"], "label": f"W{week+1} Car Izole"})

    # Thursday - Heavy B
    thu = monday + timedelta(days=3)
    schedule.append({"date": str(thu), "workout_id": WORKOUTS[f"{phase}_HEAVY_B"], "label": f"W{week+1} Per Heavy B"})

    # Friday - Isolation
    fri = monday + timedelta(days=4)
    schedule.append({"date": str(fri), "workout_id": WORKOUTS[f"{phase}_ISOLATION"], "label": f"W{week+1} Cum Izole"})

    # Saturday - Heavy A
    sat = monday + timedelta(days=5)
    schedule.append({"date": str(sat), "workout_id": WORKOUTS[f"{phase}_HEAVY_A"], "label": f"W{week+1} Cum Heavy A"})

    # Sunday - Isolation
    sun = monday + timedelta(days=6)
    schedule.append({"date": str(sun), "workout_id": WORKOUTS[f"{phase}_ISOLATION"], "label": f"W{week+1} Paz Izole"})

print(f"Total sessions to schedule: {len(schedule)}", file=sys.stderr)
print(f"Date range: {schedule[0]['date']} to {schedule[-1]['date']}", file=sys.stderr)
print(f"  Phase 1: W1-W4 ({start_date + timedelta(days=1)} to {start_date + timedelta(weeks=3, days=6)})", file=sys.stderr)
print(f"  Phase 2: W5-W8 ({start_date + timedelta(weeks=4, days=1)} to {start_date + timedelta(weeks=7, days=6)})", file=sys.stderr)
print(f"  Phase 3: W9-W12 ({start_date + timedelta(weeks=8, days=1)} to {start_date + timedelta(weeks=11, days=6)})", file=sys.stderr)

# Schedule all workouts
results = []
for i, item in enumerate(schedule):
    label = item["label"]
    workout_id = item["workout_id"]
    cal_date = item["date"]
    print(f"  [{i+1}/{len(schedule)}] {label} -> {cal_date}...", file=sys.stderr, end=" ")

    try:
        url = f"workout-service/schedule/{workout_id}"
        response = garmin.client.post("connectapi", url, json={"date": cal_date})
        if response.status_code == 200:
            print("OK", file=sys.stderr)
            results.append({"date": cal_date, "label": label, "status": "success"})
        else:
            print(f"HTTP {response.status_code}", file=sys.stderr)
            results.append({"date": cal_date, "label": label, "status": "error", "http": response.status_code})
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        results.append({"date": cal_date, "label": label, "status": "error", "error": str(e)})

success = sum(1 for r in results if r["status"] == "success")
failed = sum(1 for r in results if r["status"] != "success")
print(f"\nDone: {success} scheduled, {failed} failed.", file=sys.stderr)

print(json.dumps(results, indent=2))
