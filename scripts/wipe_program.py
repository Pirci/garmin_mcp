#!/usr/bin/env python3
"""Remove ALL program workouts from Garmin Connect: unschedule + delete."""
import os
import re
import sys

from garminconnect import Garmin

tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
garmin = Garmin()
garmin.login(tokenstore)
print("Logged in.\n", file=sys.stderr)

# Match our program workouts: "W<n> Heavy A/B" or "W<n> Izole"
pattern = re.compile(r"^W\d+ (Heavy [AB]|Izole)")

all_workouts = garmin.get_workouts(0, 200)
ours = [wk for wk in all_workouts if pattern.match(wk.get("workoutName", ""))]
our_ids = {wk["workoutId"] for wk in ours}
print(f"Found {len(our_ids)} program workouts.", file=sys.stderr)

# Unschedule every calendar entry referencing them (wide date range)
query = {"query": 'query{workoutScheduleSummariesScalar(startDate:"2026-07-01", endDate:"2026-12-31")}'}
result = garmin.query_garmin_graphql(query)
scheduled = result.get("data", {}).get("workoutScheduleSummariesScalar", [])

unsched = 0
for s in scheduled:
    if s.get("workoutId") in our_ids:
        try:
            garmin.unschedule_workout(s["scheduledWorkoutId"])
            unsched += 1
        except Exception as e:
            print(f"  unschedule fail {s.get('scheduledWorkoutId')}: {e}", file=sys.stderr)
print(f"Unscheduled {unsched} calendar entries.", file=sys.stderr)

# Delete the workout templates
deleted = 0
for wid in our_ids:
    try:
        garmin.delete_workout(wid)
        deleted += 1
    except Exception as e:
        print(f"  delete fail {wid}: {e}", file=sys.stderr)
print(f"Deleted {deleted} workouts.", file=sys.stderr)

# Verify nothing remains
remaining = [wk for wk in garmin.get_workouts(0, 200) if pattern.match(wk.get("workoutName", ""))]
print(f"\nRemaining program workouts: {len(remaining)}", file=sys.stderr)
print("Done — Garmin Connect wiped clean." if not remaining else "WARNING: some remain", file=sys.stderr)
