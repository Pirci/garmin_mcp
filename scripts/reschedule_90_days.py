#!/usr/bin/env python3
"""Fix scheduling: unschedule all wrongly placed workouts, reschedule correctly."""
import json
import os
import sys
from datetime import date, timedelta

from garminconnect import Garmin

tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
garmin = Garmin()
garmin.login(tokenstore)
print("Logged in successfully.", file=sys.stderr)

# ============================================================
# STEP 1: Unschedule all wrongly placed workouts (Jul 15 - Oct 5)
# ============================================================
print("\n=== STEP 1: Removing wrongly scheduled workouts ===", file=sys.stderr)

query = {
    "query": 'query{workoutScheduleSummariesScalar(startDate:"2026-07-15", endDate:"2026-10-06")}'
}
result = garmin.query_garmin_graphql(query)
scheduled = result.get("data", {}).get("workoutScheduleSummariesScalar", [])

# Only unschedule our strength workouts (not Garmin Coach running workouts)
our_workout_ids = {
    1630789034, 1630789038, 1630789044,
    1630789049, 1630789054, 1630789058,
    1630789060, 1630789062, 1630789067,
}

to_unschedule = []
for s in scheduled:
    wid = s.get("workoutId")
    if wid in our_workout_ids:
        to_unschedule.append(s.get("scheduledWorkoutId"))

print(f"Found {len(to_unschedule)} strength workouts to remove.", file=sys.stderr)

for sid in to_unschedule:
    try:
        garmin.unschedule_workout(sid)
        print(f"  Removed scheduled_workout_id {sid}", file=sys.stderr)
    except Exception as e:
        print(f"  Failed to remove {sid}: {e}", file=sys.stderr)

# ============================================================
# STEP 2: Reschedule with correct dates
# ============================================================
print("\n=== STEP 2: Scheduling with correct dates ===", file=sys.stderr)

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

# July 13, 2026 = Monday (confirmed from Garmin calendar screenshot)
# Program starts Week 1 Monday = July 13
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

    # Tuesday (Monday + 1) - Heavy A
    tue = monday + timedelta(days=1)
    schedule.append({"date": str(tue), "workout_id": WORKOUTS[f"{phase}_HEAVY_A"], "label": f"W{week+1} Sal Heavy A"})

    # Wednesday (Monday + 2) - Isolation
    wed = monday + timedelta(days=2)
    schedule.append({"date": str(wed), "workout_id": WORKOUTS[f"{phase}_ISOLATION"], "label": f"W{week+1} Car Izole"})

    # Thursday (Monday + 3) - Heavy B
    thu = monday + timedelta(days=3)
    schedule.append({"date": str(thu), "workout_id": WORKOUTS[f"{phase}_HEAVY_B"], "label": f"W{week+1} Per Heavy B"})

    # Friday (Monday + 4) - Isolation
    fri = monday + timedelta(days=4)
    schedule.append({"date": str(fri), "workout_id": WORKOUTS[f"{phase}_ISOLATION"], "label": f"W{week+1} Cum Izole"})

    # Saturday (Monday + 5) - Heavy A
    sat = monday + timedelta(days=5)
    schedule.append({"date": str(sat), "workout_id": WORKOUTS[f"{phase}_HEAVY_A"], "label": f"W{week+1} Cum Heavy A"})

    # Sunday (Monday + 6) - Isolation
    sun = monday + timedelta(days=6)
    schedule.append({"date": str(sun), "workout_id": WORKOUTS[f"{phase}_ISOLATION"], "label": f"W{week+1} Paz Izole"})

print(f"Total sessions to schedule: {len(schedule)}", file=sys.stderr)
print(f"Date range: {schedule[0]['date']} to {schedule[-1]['date']}", file=sys.stderr)

# Verify day-of-week correctness
first = date.fromisoformat(schedule[0]["date"])
print(f"First workout: {schedule[0]['date']} = {first.strftime('%A')} (should be Tuesday)", file=sys.stderr)

success = 0
failed = 0
for i, item in enumerate(schedule):
    label = item["label"]
    workout_id = item["workout_id"]
    cal_date = item["date"]
    day_name = date.fromisoformat(cal_date).strftime("%A")
    print(f"  [{i+1}/{len(schedule)}] {label} -> {cal_date} ({day_name})...", file=sys.stderr, end=" ")

    try:
        url = f"workout-service/schedule/{workout_id}"
        response = garmin.client.post("connectapi", url, json={"date": cal_date})
        if response.status_code == 200:
            print("OK", file=sys.stderr)
            success += 1
        else:
            print(f"HTTP {response.status_code}", file=sys.stderr)
            failed += 1
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        failed += 1

print(f"\nDone: {success} scheduled, {failed} failed.", file=sys.stderr)
