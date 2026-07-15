#!/usr/bin/env python3
"""
Calisthenics-focused 90-day program.
- Bodyweight progression (variation + reps + sets) instead of DB weight ceiling
- KB for legs/rows/carry (safe weighted progression)
- Light DB for arm/delt isolation
- Deload every 4th week (W4, W8, W12)
Recalibrated to real strength from actual Tuesday W1 performance.
"""
import json
import os
import re
import sys
from datetime import date, timedelta

from garminconnect import Garmin

tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
garmin = Garmin()
garmin.login(tokenstore)
print("Logged in.\n", file=sys.stderr)

R = 120
Ri = 90


def rep_group(order, name, sets, reps, rest, label=""):
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
             "description": f"Rest {rest}s",
             "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
             "endConditionValue": float(rest),
             "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}},
        ],
    }


def timed_group(order, name, sets, dur, rest, label=""):
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
             "description": f"Rest {rest}s",
             "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
             "endConditionValue": float(rest),
             "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"}},
        ],
    }


def workout(name, desc, steps):
    return {
        "workoutName": name, "description": desc,
        "sportType": {"sportTypeId": 5, "sportTypeKey": "strength_training"},
        "workoutSegments": [{"segmentOrder": 1,
            "sportType": {"sportTypeId": 5, "sportTypeKey": "strength_training"},
            "workoutSteps": steps}],
    }


# =============================================================================
# 12-WEEK PROGRESSIONS  (sets, reps/sec, label)   deload weeks: 4, 8, 12
# =============================================================================

# --- Legs (KB Goblet Squat) ---
GOBLET = [(3,12,"16kg KB"),(3,15,"16kg KB"),(4,12,"16kg KB"),(2,12,"14kg KB"),
          (3,12,"18kg KB"),(3,15,"18kg KB"),(4,12,"18kg KB"),(2,12,"16kg KB"),
          (3,12,"20kg KB"),(3,15,"20kg KB"),(4,12,"20kg KB"),(2,12,"18kg KB")]

# --- Push-Up (chest) variation progression ---
PUSHUP = [(3,15,"Standard"),(3,20,"Standard"),(4,15,"Standard"),(2,15,"Standard"),
          (3,12,"Decline"),(3,15,"Decline"),(4,12,"Decline"),(2,12,"Decline"),
          (3,12,"Diamond"),(3,15,"Diamond"),(4,12,"Diamond"),(2,12,"Diamond")]

# --- Dips (chest/triceps) ---
DIPS = [(3,8,"Assisted"),(3,10,"Assisted"),(4,8,"Assisted"),(2,8,"Assisted"),
        (3,6,"BW"),(3,8,"BW"),(4,6,"BW"),(2,6,"BW"),
        (3,8,"BW"),(3,10,"BW"),(4,8,"BW"),(2,8,"BW")]

# --- Pike Push-Up (shoulders) ---
PIKE = [(3,8,"Floor"),(3,10,"Floor"),(4,8,"Floor"),(2,8,"Floor"),
        (3,8,"Feet Elevated"),(3,10,"Feet Elevated"),(4,8,"Feet Elevated"),(2,8,"Feet Elevated"),
        (3,8,"Deep Elevated"),(3,10,"Deep Elevated"),(4,8,"Deep Elevated"),(2,8,"Deep Elevated")]

# --- Chin-Up (back/biceps) ---
CHIN = [(3,6,"Assisted"),(3,8,"Assisted"),(3,10,"Assisted"),(2,6,"Assisted"),
        (3,6,"BW"),(3,8,"BW"),(4,6,"BW"),(2,6,"BW"),
        (3,8,"BW"),(3,10,"BW"),(4,8,"BW"),(2,6,"BW")]

# --- Pull-Up (back) ---
PULLUP = [(3,5,"Assisted"),(3,6,"Assisted"),(3,8,"Assisted"),(2,5,"Assisted"),
          (3,4,"BW"),(3,5,"BW"),(3,6,"BW"),(2,4,"BW"),
          (3,5,"BW"),(3,6,"BW"),(4,5,"BW"),(2,4,"BW")]

# --- Inverted Row (back) ---
ROW_BW = [(3,12,"Bar hip-height"),(3,15,"Bar hip-height"),(4,12,"Bar hip-height"),(2,12,"Bar hip-height"),
          (3,12,"Feet Elevated"),(3,15,"Feet Elevated"),(4,12,"Feet Elevated"),(2,12,"Feet Elevated"),
          (3,15,"Feet Elevated"),(4,12,"Feet Elevated"),(4,15,"Feet Elevated"),(2,12,"Feet Elevated")]

# --- Gorilla Row (KB, back) ---
GORILLA = [(3,12,"16kg KB"),(3,15,"16kg KB"),(4,12,"16kg KB"),(2,12,"14kg KB"),
           (3,12,"18kg KB"),(3,15,"18kg KB"),(4,12,"18kg KB"),(2,12,"16kg KB"),
           (3,12,"20kg KB"),(3,15,"20kg KB"),(4,12,"20kg KB"),(2,12,"18kg KB")]

# --- Hanging Knee/Leg Raise (core) ---
CORE = [(3,12,"Knee Raise"),(3,15,"Knee Raise"),(4,12,"Knee Raise"),(2,12,"Knee Raise"),
        (3,10,"Leg Raise"),(3,12,"Leg Raise"),(4,10,"Leg Raise"),(2,10,"Leg Raise"),
        (3,12,"Leg Raise"),(3,15,"Leg Raise"),(4,12,"Leg Raise"),(2,12,"Leg Raise")]

# --- Isolation: Hammer Curl (DB) ---
HAMMER = [(3,10,"10kg DB"),(3,12,"10kg DB"),(3,15,"10kg DB"),(2,10,"10kg DB"),
          (3,12,"10kg DB"),(3,15,"10kg DB"),(4,12,"10kg DB"),(2,12,"10kg DB"),
          (3,10,"12.5kg DB"),(3,12,"12.5kg DB"),(4,10,"12.5kg DB"),(2,10,"10kg DB")]

# --- Isolation: Diamond Push-Up (triceps) ---
DIAMOND = [(3,10,"BW"),(3,12,"BW"),(3,15,"BW"),(2,10,"BW"),
           (3,12,"BW"),(3,15,"BW"),(4,12,"BW"),(2,12,"BW"),
           (3,15,"BW"),(4,12,"BW"),(4,15,"BW"),(2,12,"BW")]

# --- Isolation: Lateral Raise (DB) ---
LATERAL = [(3,12,"5kg DB"),(3,15,"5kg DB"),(4,12,"5kg DB"),(2,12,"5kg DB"),
           (3,15,"5kg DB"),(4,12,"5kg DB"),(4,15,"5kg DB"),(2,12,"5kg DB"),
           (4,12,"5kg DB"),(4,15,"5kg DB"),(5,12,"5kg DB"),(2,12,"5kg DB")]

# --- Isolation: Farmer's Walk (KB, timed) ---
FARMER = [(3,30,"16kg KB"),(3,40,"16kg KB"),(3,45,"16kg KB"),(2,30,"14kg KB"),
          (3,30,"18kg KB"),(3,40,"18kg KB"),(3,45,"18kg KB"),(2,30,"16kg KB"),
          (3,40,"20kg KB"),(3,45,"20kg KB"),(3,50,"20kg KB"),(2,30,"18kg KB")]


def phase_of(w):
    return "F1" if w <= 4 else "F2" if w <= 8 else "F3"


def dl(w):
    return " [DELOAD]" if w in (4, 8, 12) else ""


def build_heavy_a(w):
    i = w - 1
    return workout(
        f"W{w} Heavy A{dl(w)}",
        f"{phase_of(w)} Hafta {w} | Push emphasis (calisthenics){dl(w)}",
        [
            rep_group(1, "Goblet Squat",  *GOBLET[i][:2],  R, GOBLET[i][2]),
            rep_group(2, "Dips",          *DIPS[i][:2],    R, DIPS[i][2]),
            rep_group(3, "Push Up",       *PUSHUP[i][:2],  R, PUSHUP[i][2]),
            rep_group(4, "Pike Push Up",  *PIKE[i][:2],    R, PIKE[i][2]),
            rep_group(5, "Chin Up",       *CHIN[i][:2],    R, CHIN[i][2]),
            rep_group(6, "Hanging Raise", *CORE[i][:2],    Ri, CORE[i][2]),
        ],
    )


def build_heavy_b(w):
    i = w - 1
    return workout(
        f"W{w} Heavy B{dl(w)}",
        f"{phase_of(w)} Hafta {w} | Pull emphasis (calisthenics){dl(w)}",
        [
            rep_group(1, "Goblet Squat",  *GOBLET[i][:2],  R, GOBLET[i][2]),
            rep_group(2, "Pull Up",       *PULLUP[i][:2],  R, PULLUP[i][2]),
            rep_group(3, "Gorilla Row",   *GORILLA[i][:2], R, GORILLA[i][2]),
            rep_group(4, "Inverted Row",  *ROW_BW[i][:2],  R, ROW_BW[i][2]),
            rep_group(5, "Pike Push Up",  *PIKE[i][:2],    R, PIKE[i][2]),
            rep_group(6, "Hanging Raise", *CORE[i][:2],    Ri, CORE[i][2]),
        ],
    )


def build_iso(w):
    i = w - 1
    return workout(
        f"W{w} Izole{dl(w)}",
        f"{phase_of(w)} Hafta {w} | Kol + Omuz + Forearm{dl(w)}",
        [
            rep_group(  1, "Hammer Curl",       *HAMMER[i][:2],  Ri, HAMMER[i][2]),
            rep_group(  2, "Diamond Push Up",   *DIAMOND[i][:2], Ri, DIAMOND[i][2]),
            rep_group(  3, "Lateral Raise",     *LATERAL[i][:2], Ri, LATERAL[i][2]),
            timed_group(4, "Farmers Walk",  FARMER[i][0], FARMER[i][1], Ri, FARMER[i][2]),
        ],
    )


# =============================================================================
# STEP 1: Clean up existing program workouts + schedule
# =============================================================================
print("=== STEP 1: Cleaning existing program ===", file=sys.stderr)

# Find our workouts by name pattern: "W<n> Heavy A/B" or "W<n> Izole"
all_workouts = garmin.get_workouts(0, 200)
pattern = re.compile(r"^W\d+ (Heavy [AB]|Izole)")
ours = [wk for wk in all_workouts if pattern.match(wk.get("workoutName", ""))]
our_ids = {wk["workoutId"] for wk in ours}
print(f"  Found {len(our_ids)} existing program workouts.", file=sys.stderr)

# Unschedule any calendar entries referencing them
query = {"query": 'query{workoutScheduleSummariesScalar(startDate:"2026-07-13", endDate:"2026-10-05")}'}
result = garmin.query_garmin_graphql(query)
scheduled = result.get("data", {}).get("workoutScheduleSummariesScalar", [])
unsched = 0
for s in scheduled:
    if s.get("workoutId") in our_ids:
        try:
            garmin.unschedule_workout(s["scheduledWorkoutId"])
            unsched += 1
        except:
            pass
print(f"  Unscheduled {unsched} calendar entries.", file=sys.stderr)

for wid in our_ids:
    try:
        garmin.delete_workout(wid)
    except:
        pass
print(f"  Deleted {len(our_ids)} workouts.", file=sys.stderr)


# =============================================================================
# STEP 2: Create 36 new calisthenics workouts
# =============================================================================
print("\n=== STEP 2: Creating 36 calisthenics workouts ===", file=sys.stderr)

ids = {}
for w in range(1, 13):
    for typ, builder in (("HA", build_heavy_a), ("HB", build_heavy_b), ("ISO", build_iso)):
        wk = builder(w)
        res = garmin.upload_workout(wk)
        ids[(w, typ)] = res.get("workoutId")
    print(f"  W{w:2d} done (HA/HB/ISO)", file=sys.stderr)


# =============================================================================
# STEP 3: Schedule 84 sessions
# =============================================================================
print("\n=== STEP 3: Scheduling 84 sessions ===", file=sys.stderr)

start_monday = date(2026, 7, 13)
sched = []
for week in range(12):
    w = week + 1
    mon = start_monday + timedelta(weeks=week)
    sched.append((str(mon),                     ids[(w, "ISO")]))  # Mon
    sched.append((str(mon + timedelta(days=1)), ids[(w, "HA")]))   # Tue
    sched.append((str(mon + timedelta(days=2)), ids[(w, "ISO")]))  # Wed
    sched.append((str(mon + timedelta(days=3)), ids[(w, "HB")]))   # Thu
    sched.append((str(mon + timedelta(days=4)), ids[(w, "ISO")]))  # Fri
    sched.append((str(mon + timedelta(days=5)), ids[(w, "HA")]))   # Sat
    sched.append((str(mon + timedelta(days=6)), ids[(w, "ISO")]))  # Sun

ok = 0
for d, wid in sched:
    try:
        resp = garmin.client.post("connectapi", f"workout-service/schedule/{wid}", json={"date": d})
        if resp.status_code == 200:
            ok += 1
        else:
            print(f"  WARN {d} HTTP {resp.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"  FAIL {d}: {e}", file=sys.stderr)

print(f"\nDone: {ok}/{len(sched)} scheduled.", file=sys.stderr)
print(json.dumps({"workouts": len(ids), "scheduled": ok}, indent=2))
