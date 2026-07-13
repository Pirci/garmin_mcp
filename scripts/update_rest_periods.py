#!/usr/bin/env python3
"""Update all 9 workouts with corrected rest periods and reschedule."""
import json
import os
import sys
from datetime import date, timedelta

from garminconnect import Garmin

tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
garmin = Garmin()
garmin.login(tokenstore)
print("Logged in successfully.", file=sys.stderr)

OLD_WORKOUT_IDS = [
    1630789034, 1630789038, 1630789044,
    1630789049, 1630789054, 1630789058,
    1630789060, 1630789062, 1630789067,
]

# ============================================================
# STEP 1: Unschedule all existing entries
# ============================================================
print("=== STEP 1: Removing all scheduled entries ===", file=sys.stderr)

query = {
    "query": 'query{workoutScheduleSummariesScalar(startDate:"2026-07-14", endDate:"2026-10-05")}'
}
result = garmin.query_garmin_graphql(query)
scheduled = result.get("data", {}).get("workoutScheduleSummariesScalar", [])

old_set = set(OLD_WORKOUT_IDS)
removed = 0
for s in scheduled:
    if s.get("workoutId") in old_set:
        try:
            garmin.unschedule_workout(s["scheduledWorkoutId"])
            removed += 1
        except Exception as e:
            print(f"  Failed to unschedule {s['scheduledWorkoutId']}: {e}", file=sys.stderr)

print(f"  Removed {removed} scheduled entries.", file=sys.stderr)

# ============================================================
# STEP 2: Delete old workouts
# ============================================================
print("\n=== STEP 2: Deleting old workout templates ===", file=sys.stderr)

for wid in OLD_WORKOUT_IDS:
    try:
        garmin.delete_workout(wid)
        print(f"  Deleted workout {wid}", file=sys.stderr)
    except Exception as e:
        print(f"  Failed to delete {wid}: {e}", file=sys.stderr)

# ============================================================
# STEP 3: Create updated workouts with correct rest periods
# ============================================================
print("\n=== STEP 3: Uploading updated workouts ===", file=sys.stderr)

COMPOUND_REST = 120  # 2 minutes for compound movements
ISOLATION_REST = 90  # 90 seconds for isolation movements


def make_exercise_group(order, name, sets, reps, rest_sec, weight_desc=""):
    desc = f"{name}: {sets}x{reps}"
    if weight_desc:
        desc += f" @{weight_desc}"
    rep_val = float(reps) if isinstance(reps, int) else float(str(reps).split("-")[-1])
    return {
        "type": "RepeatGroupDTO",
        "stepOrder": order,
        "numberOfIterations": sets,
        "workoutSteps": [
            {
                "type": "ExecutableStepDTO",
                "stepOrder": 1,
                "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
                "description": desc,
                "endCondition": {"conditionTypeId": 10, "conditionTypeKey": "reps"},
                "endConditionValue": rep_val,
                "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
                "exerciseName": name,
            },
            {
                "type": "ExecutableStepDTO",
                "stepOrder": 2,
                "stepType": {"stepTypeId": 4, "stepTypeKey": "recovery"},
                "description": f"Rest {rest_sec}s",
                "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                "endConditionValue": float(rest_sec),
                "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
            },
        ],
    }


def make_timed_group(order, name, sets, duration_sec, rest_sec, weight_desc=""):
    desc = f"{name}: {sets}x{duration_sec}s"
    if weight_desc:
        desc += f" @{weight_desc}"
    return {
        "type": "RepeatGroupDTO",
        "stepOrder": order,
        "numberOfIterations": sets,
        "workoutSteps": [
            {
                "type": "ExecutableStepDTO",
                "stepOrder": 1,
                "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
                "description": desc,
                "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                "endConditionValue": float(duration_sec),
                "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
                "exerciseName": name,
            },
            {
                "type": "ExecutableStepDTO",
                "stepOrder": 2,
                "stepType": {"stepTypeId": 4, "stepTypeKey": "recovery"},
                "description": f"Rest {rest_sec}s",
                "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
                "endConditionValue": float(rest_sec),
                "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
            },
        ],
    }


def build(name, description, steps):
    return {
        "workoutName": name,
        "description": description,
        "sportType": {"sportTypeId": 5, "sportTypeKey": "strength_training"},
        "workoutSegments": [{
            "segmentOrder": 1,
            "sportType": {"sportTypeId": 5, "sportTypeKey": "strength_training"},
            "workoutSteps": steps,
        }],
    }


R = COMPOUND_REST
Ri = ISOLATION_REST

# --- PHASE 1 ---
workouts = []

workouts.append(build("F1 Heavy A (Sal/Cum)",
    "Faz 1 | Floor Press + Chin-Up | 3 set | Rest: 120s compound", [
    make_exercise_group(1, "Goblet Squat",    3, 10, R,  "14kg KB"),
    make_exercise_group(2, "Floor Press",     3, 12, R,  "10kg DB"),
    make_exercise_group(3, "Gorilla Row",     3, 10, R,  "14kg KB"),
    make_exercise_group(4, "Overhead Press",  3, 10, R,  "10kg DB"),
    make_exercise_group(5, "Chin Up",         3, 8,  R,  "Assisted"),
    make_exercise_group(6, "Knee Raise",      3, 12, Ri, "BW"),
]))

workouts.append(build("F1 Heavy B (Per)",
    "Faz 1 | Dips + Inverted Row | 3 set | Rest: 120s compound", [
    make_exercise_group(1, "Goblet Squat",    3, 10, R,  "14kg KB"),
    make_exercise_group(2, "Dips",            3, 10, R,  "Assisted"),
    make_exercise_group(3, "Inverted Row",    3, 10, R,  "BW"),
    make_exercise_group(4, "Overhead Press",  3, 10, R,  "10kg DB"),
    make_exercise_group(5, "Gorilla Row",     3, 10, R,  "14kg KB"),
    make_exercise_group(6, "Knee Raise",      3, 12, Ri, "BW"),
]))

workouts.append(build("F1 Izole (Car/Cum/Paz)",
    "Faz 1 | Kol + Omuz + Forearm | Rest: 90s izolasyon", [
    make_exercise_group(1, "Hammer Curl",        3, 12, Ri, "5kg DB"),
    make_exercise_group(2, "Triceps Extension",  3, 12, Ri, "5kg DB"),
    make_exercise_group(3, "Lateral Raise",      3, 15, Ri, "3kg DB"),
    make_timed_group(   4, "Farmers Walk",       3, 30, Ri, "14kg KB"),
]))

# --- PHASE 2 ---
workouts.append(build("F2 Heavy A (Sal/Cum)",
    "Faz 2 | Floor Press + Chin-Up | 4 set | Rest: 120s compound", [
    make_exercise_group(1, "Goblet Squat",    3, 12, R,  "16kg KB"),
    make_exercise_group(2, "Floor Press",     4, 12, R,  "10kg DB"),
    make_exercise_group(3, "Gorilla Row",     4, 10, R,  "16kg KB"),
    make_exercise_group(4, "Overhead Press",  4, 10, R,  "10kg DB"),
    make_exercise_group(5, "Chin Up",         3, 10, R,  "Assisted"),
    make_exercise_group(6, "Knee Raise",      3, 15, Ri, "BW"),
]))

workouts.append(build("F2 Heavy B (Per)",
    "Faz 2 | Dips + Inverted Row | 4 set | Rest: 120s compound", [
    make_exercise_group(1, "Goblet Squat",    3, 12, R,  "16kg KB"),
    make_exercise_group(2, "Dips",            4, 10, R,  "Assisted"),
    make_exercise_group(3, "Inverted Row",    4, 10, R,  "BW"),
    make_exercise_group(4, "Overhead Press",  4, 10, R,  "10kg DB"),
    make_exercise_group(5, "Gorilla Row",     4, 10, R,  "16kg KB"),
    make_exercise_group(6, "Knee Raise",      3, 15, Ri, "BW"),
]))

workouts.append(build("F2 Izole (Car/Cum/Paz)",
    "Faz 2 | Kol + Omuz + Forearm | 4 set | Rest: 90s izolasyon", [
    make_exercise_group(1, "Hammer Curl",        4, 12, Ri, "10kg DB"),
    make_exercise_group(2, "Triceps Extension",  4, 12, Ri, "10kg DB"),
    make_exercise_group(3, "Lateral Raise",      4, 15, Ri, "5kg DB"),
    make_timed_group(   4, "Farmers Walk",       3, 40, Ri, "16kg KB"),
]))

# --- PHASE 3 ---
workouts.append(build("F3 Heavy A (Sal/Cum)",
    "Faz 3 | Floor Press + Chin-Up | 4 set | Rest: 120s compound", [
    make_exercise_group(1, "Goblet Squat",    4, 10, R,  "18-20kg KB"),
    make_exercise_group(2, "Floor Press",     4, 10, R,  "12.5kg DB"),
    make_exercise_group(3, "Gorilla Row",     4, 10, R,  "18kg KB"),
    make_exercise_group(4, "Overhead Press",  4, 8,  R,  "12.5kg DB"),
    make_exercise_group(5, "Chin Up",         3, 8,  R,  "BW"),
    make_exercise_group(6, "Knee Raise",      4, 15, Ri, "BW"),
]))

workouts.append(build("F3 Heavy B (Per)",
    "Faz 3 | Dips + Inverted Row | 4 set | Rest: 120s compound", [
    make_exercise_group(1, "Goblet Squat",    4, 10, R,  "18-20kg KB"),
    make_exercise_group(2, "Dips",            4, 10, R,  "BW"),
    make_exercise_group(3, "Inverted Row",    4, 10, R,  "BW"),
    make_exercise_group(4, "Overhead Press",  4, 8,  R,  "12.5kg DB"),
    make_exercise_group(5, "Gorilla Row",     4, 10, R,  "18kg KB"),
    make_exercise_group(6, "Knee Raise",      4, 15, Ri, "BW"),
]))

workouts.append(build("F3 Izole (Car/Cum/Paz)",
    "Faz 3 | Kol + Omuz + Forearm | Rest: 90s izolasyon", [
    make_exercise_group(1, "Hammer Curl",        4, 10, Ri, "12.5kg DB"),
    make_exercise_group(2, "Triceps Extension",  4, 10, Ri, "12.5kg DB"),
    make_exercise_group(3, "Lateral Raise",      4, 12, Ri, "5kg DB"),
    make_timed_group(   4, "Farmers Walk",       3, 45, Ri, "18-20kg KB"),
]))

# ============================================================
# Upload and collect new IDs
# ============================================================
new_ids = {}
workout_names = [
    "F1_HEAVY_A", "F1_HEAVY_B", "F1_ISOLATION",
    "F2_HEAVY_A", "F2_HEAVY_B", "F2_ISOLATION",
    "F3_HEAVY_A", "F3_HEAVY_B", "F3_ISOLATION",
]

for w, key in zip(workouts, workout_names):
    name = w["workoutName"]
    print(f"  Uploading: {name}...", file=sys.stderr, end=" ")
    try:
        result = garmin.upload_workout(w)
        wid = result.get("workoutId") if isinstance(result, dict) else None
        new_ids[key] = wid
        print(f"OK (id: {wid})", file=sys.stderr)
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)

print(f"\n  New workout IDs: {json.dumps(new_ids, indent=2)}", file=sys.stderr)

# ============================================================
# STEP 4: Schedule 12 weeks with correct dates
# ============================================================
print("\n=== STEP 4: Scheduling 12 weeks ===", file=sys.stderr)

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

    schedule.append({"date": str(monday + timedelta(days=1)), "workout_id": new_ids[f"{phase}_HEAVY_A"],   "label": f"W{week+1} Sal Heavy A"})
    schedule.append({"date": str(monday + timedelta(days=2)), "workout_id": new_ids[f"{phase}_ISOLATION"], "label": f"W{week+1} Car Izole"})
    schedule.append({"date": str(monday + timedelta(days=3)), "workout_id": new_ids[f"{phase}_HEAVY_B"],   "label": f"W{week+1} Per Heavy B"})
    schedule.append({"date": str(monday + timedelta(days=4)), "workout_id": new_ids[f"{phase}_ISOLATION"], "label": f"W{week+1} Cum Izole"})
    schedule.append({"date": str(monday + timedelta(days=5)), "workout_id": new_ids[f"{phase}_HEAVY_A"],   "label": f"W{week+1} Cum Heavy A"})
    schedule.append({"date": str(monday + timedelta(days=6)), "workout_id": new_ids[f"{phase}_ISOLATION"], "label": f"W{week+1} Paz Izole"})

print(f"  Scheduling {len(schedule)} sessions ({schedule[0]['date']} to {schedule[-1]['date']})...", file=sys.stderr)

success = 0
for item in schedule:
    try:
        url = f"workout-service/schedule/{item['workout_id']}"
        response = garmin.client.post("connectapi", url, json={"date": item["date"]})
        if response.status_code == 200:
            success += 1
        else:
            print(f"  WARN: {item['label']} -> HTTP {response.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"  FAIL: {item['label']} -> {e}", file=sys.stderr)

print(f"\nDone: {success}/{len(schedule)} scheduled successfully.", file=sys.stderr)
print(json.dumps({"new_workout_ids": new_ids, "scheduled": success, "total": len(schedule)}, indent=2))
