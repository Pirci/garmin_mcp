#!/usr/bin/env python3
"""Update the 12 isolation workouts in-place: swap Hammer Curl -> KB Hammer Curl.
In-place PUT preserves workoutId, so the existing schedule stays intact.
"""
import os
import re
import sys

from garminconnect import Garmin

tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
garmin = Garmin()
garmin.login(tokenstore)
print("Logged in.\n", file=sys.stderr)

Ri = 90


def rep_group(order, name, sets, reps, label=""):
    desc = f"{name}: {sets}x{reps}"
    if label:
        desc += f" @{label}"
    return {
        "type": "RepeatGroupDTO", "stepOrder": order, "numberOfIterations": sets,
        "workoutSteps": [
            {"type": "ExecutableStepDTO", "stepOrder": 1,
             "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
             "description": desc,
             "endCondition": {"conditionTypeId": 10, "conditionTypeKey": "reps"},
             "endConditionValue": float(reps),
             "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
             "exerciseName": name},
            {"type": "ExecutableStepDTO", "stepOrder": 2,
             "stepType": {"stepTypeId": 4, "stepTypeKey": "recovery"},
             "description": f"Rest {Ri}s",
             "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
             "endConditionValue": float(Ri),
             "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}},
        ],
    }


def timed_group(order, name, sets, dur, label=""):
    desc = f"{name}: {sets}x{dur}s"
    if label:
        desc += f" @{label}"
    return {
        "type": "RepeatGroupDTO", "stepOrder": order, "numberOfIterations": sets,
        "workoutSteps": [
            {"type": "ExecutableStepDTO", "stepOrder": 1,
             "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
             "description": desc,
             "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
             "endConditionValue": float(dur),
             "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
             "exerciseName": name},
            {"type": "ExecutableStepDTO", "stepOrder": 2,
             "stepType": {"stepTypeId": 4, "stepTypeKey": "recovery"},
             "description": f"Rest {Ri}s",
             "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
             "endConditionValue": float(Ri),
             "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}},
        ],
    }


# 12-week isolation progression (deload W4/W8/W12)
# KB Hammer Curl: F1 14kg, F2 16kg, F3 18kg
KB_HAMMER = [(3,12,"14kg KB"),(3,15,"14kg KB"),(4,12,"14kg KB"),(2,12,"12kg KB"),
             (3,12,"16kg KB"),(3,15,"16kg KB"),(4,12,"16kg KB"),(2,12,"14kg KB"),
             (3,10,"18kg KB"),(3,12,"18kg KB"),(4,10,"18kg KB"),(2,10,"16kg KB")]

DIAMOND = [(3,10,"BW"),(3,12,"BW"),(3,15,"BW"),(2,10,"BW"),
           (3,12,"BW"),(3,15,"BW"),(4,12,"BW"),(2,12,"BW"),
           (3,15,"BW"),(4,12,"BW"),(4,15,"BW"),(2,12,"BW")]

LATERAL = [(3,12,"5kg DB"),(3,15,"5kg DB"),(4,12,"5kg DB"),(2,12,"5kg DB"),
           (3,15,"5kg DB"),(4,12,"5kg DB"),(4,15,"5kg DB"),(2,12,"5kg DB"),
           (4,12,"5kg DB"),(4,15,"5kg DB"),(5,12,"5kg DB"),(2,12,"5kg DB")]

FARMER = [(3,30,"16kg KB"),(3,40,"16kg KB"),(3,45,"16kg KB"),(2,30,"14kg KB"),
          (3,30,"18kg KB"),(3,40,"18kg KB"),(3,45,"18kg KB"),(2,30,"16kg KB"),
          (3,40,"20kg KB"),(3,45,"20kg KB"),(3,50,"20kg KB"),(2,30,"18kg KB")]


def build_steps(w):
    i = w - 1
    return [
        rep_group(  1, "KB Hammer Curl",  *KB_HAMMER[i][:2], KB_HAMMER[i][2]),
        rep_group(  2, "Diamond Push Up", *DIAMOND[i][:2],   DIAMOND[i][2]),
        rep_group(  3, "Lateral Raise",   *LATERAL[i][:2],   LATERAL[i][2]),
        timed_group(4, "Farmers Walk",  FARMER[i][0], FARMER[i][1], FARMER[i][2]),
    ]


# Find the 12 isolation workouts by name
all_workouts = garmin.get_workouts(0, 200)
iso_pattern = re.compile(r"^W(\d+) Izole")

by_week = {}
for wk in all_workouts:
    m = iso_pattern.match(wk.get("workoutName", ""))
    if m:
        by_week[int(m.group(1))] = wk["workoutId"]

print(f"Found {len(by_week)} isolation workouts.\n", file=sys.stderr)

for w in range(1, 13):
    wid = by_week.get(w)
    if not wid:
        print(f"  W{w}: NOT FOUND, skipping", file=sys.stderr)
        continue

    workout = garmin.get_workout_by_id(wid)
    workout["workoutSegments"][0]["workoutSteps"] = build_steps(w)

    url = f"workout-service/workout/{wid}"
    resp = garmin.client.put("connectapi", url, json=workout)
    name = workout.get("workoutName")
    print(f"  {name} ({wid}): HTTP {resp.status_code}", file=sys.stderr)

print("\nDone! All isolation workouts updated with KB Hammer Curl.", file=sys.stderr)
