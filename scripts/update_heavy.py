#!/usr/bin/env python3
"""Update the 12 Heavy A + 12 Heavy B workouts in-place (calisthenics-first).
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


# =============================================================================
# 12-WEEK CALISTHENICS-FIRST PROGRESSIONS  (deload W4/W8/W12)
# =============================================================================

# Legs (KB — safest heavy leg loading, zero knee/back risk)
GOBLET = [(3,12,"16kg KB"),(3,15,"16kg KB"),(4,12,"16kg KB"),(2,12,"14kg KB"),
          (3,12,"18kg KB"),(3,15,"18kg KB"),(4,12,"18kg KB"),(2,12,"16kg KB"),
          (3,12,"20kg KB"),(3,15,"20kg KB"),(4,12,"20kg KB"),(2,12,"18kg KB")]

# Chest — PRIMARY calisthenics push, variation progression
PUSHUP = [(3,15,"Standard"),(3,20,"Standard"),(4,15,"Standard"),(2,15,"Standard"),
          (3,12,"Decline"),(3,15,"Decline"),(4,12,"Decline"),(2,12,"Decline"),
          (3,10,"Archer"),(3,12,"Archer"),(4,10,"Archer"),(2,10,"Archer")]

# Chest/Triceps — Dips (assisted -> BW -> BW high rep)
DIPS = [(3,8,"Assisted"),(3,10,"Assisted"),(4,8,"Assisted"),(2,8,"Assisted"),
        (3,6,"BW"),(3,8,"BW"),(4,6,"BW"),(2,6,"BW"),
        (3,8,"BW"),(3,10,"BW"),(4,8,"BW"),(2,8,"BW")]

# Shoulders — Pike -> Elevated -> Deep (toward handstand)
PIKE = [(3,8,"Floor"),(3,10,"Floor"),(4,8,"Floor"),(2,8,"Floor"),
        (3,8,"Feet Elevated"),(3,10,"Feet Elevated"),(4,8,"Feet Elevated"),(2,8,"Feet Elevated"),
        (3,8,"Deep Elevated"),(3,10,"Deep Elevated"),(4,8,"Deep Elevated"),(2,8,"Deep Elevated")]

# Back/Biceps — Chin-Up (assisted -> BW)
CHIN = [(3,6,"Assisted"),(3,8,"Assisted"),(3,10,"Assisted"),(2,6,"Assisted"),
        (3,5,"BW"),(3,6,"BW"),(3,8,"BW"),(2,5,"BW"),
        (3,6,"BW"),(3,8,"BW"),(4,6,"BW"),(2,5,"BW")]

# Back — Pull-Up (assisted -> BW), harder than chin
PULLUP = [(3,5,"Assisted"),(3,6,"Assisted"),(3,8,"Assisted"),(2,5,"Assisted"),
          (3,4,"BW"),(3,5,"BW"),(3,6,"BW"),(2,4,"BW"),
          (3,5,"BW"),(3,6,"BW"),(4,5,"BW"),(2,4,"BW")]

# Back thickness — Gorilla Row (KB loading)
GORILLA = [(3,12,"16kg KB"),(3,15,"16kg KB"),(4,12,"16kg KB"),(2,12,"14kg KB"),
           (3,12,"18kg KB"),(3,15,"18kg KB"),(4,12,"18kg KB"),(2,12,"16kg KB"),
           (3,12,"20kg KB"),(3,15,"20kg KB"),(4,12,"20kg KB"),(2,12,"18kg KB")]

# Back — Inverted Row (angle progression)
ROW_BW = [(3,12,"Bar hip-height"),(3,15,"Bar hip-height"),(4,12,"Bar hip-height"),(2,12,"Bar hip-height"),
          (3,12,"Feet Elevated"),(3,15,"Feet Elevated"),(4,12,"Feet Elevated"),(2,12,"Feet Elevated"),
          (3,15,"Feet Elevated"),(4,12,"Feet Elevated"),(4,15,"Feet Elevated"),(2,12,"Feet Elevated")]

# Core — Hanging Knee -> Leg Raise
CORE = [(3,12,"Knee Raise"),(3,15,"Knee Raise"),(4,12,"Knee Raise"),(2,12,"Knee Raise"),
        (3,10,"Leg Raise"),(3,12,"Leg Raise"),(4,10,"Leg Raise"),(2,10,"Leg Raise"),
        (3,12,"Leg Raise"),(3,15,"Leg Raise"),(4,12,"Leg Raise"),(2,12,"Leg Raise")]


def heavy_a_steps(w):
    i = w - 1
    # Push emphasis: Legs -> Push-Up (primary) -> Dips -> Pike -> Chin-Up -> Core
    return [
        rep_group(1, "Goblet Squat",  *GOBLET[i][:2], R, GOBLET[i][2]),
        rep_group(2, "Push Up",       *PUSHUP[i][:2], R, PUSHUP[i][2]),
        rep_group(3, "Dips",          *DIPS[i][:2],   R, DIPS[i][2]),
        rep_group(4, "Pike Push Up",  *PIKE[i][:2],   R, PIKE[i][2]),
        rep_group(5, "Chin Up",       *CHIN[i][:2],   R, CHIN[i][2]),
        rep_group(6, "Hanging Raise", *CORE[i][:2],   Ri, CORE[i][2]),
    ]


def heavy_b_steps(w):
    i = w - 1
    # Pull emphasis: Legs -> Pull-Up (primary) -> Gorilla Row -> Inverted Row -> Pike -> Core
    return [
        rep_group(1, "Goblet Squat",  *GOBLET[i][:2],  R, GOBLET[i][2]),
        rep_group(2, "Pull Up",       *PULLUP[i][:2],  R, PULLUP[i][2]),
        rep_group(3, "Gorilla Row",   *GORILLA[i][:2], R, GORILLA[i][2]),
        rep_group(4, "Inverted Row",  *ROW_BW[i][:2],  R, ROW_BW[i][2]),
        rep_group(5, "Pike Push Up",  *PIKE[i][:2],    R, PIKE[i][2]),
        rep_group(6, "Hanging Raise", *CORE[i][:2],    Ri, CORE[i][2]),
    ]


# Find Heavy A / Heavy B workouts by name
all_workouts = garmin.get_workouts(0, 200)
a_pat = re.compile(r"^W(\d+) Heavy A")
b_pat = re.compile(r"^W(\d+) Heavy B")

a_ids, b_ids = {}, {}
for wk in all_workouts:
    name = wk.get("workoutName", "")
    ma, mb = a_pat.match(name), b_pat.match(name)
    if ma:
        a_ids[int(ma.group(1))] = wk["workoutId"]
    elif mb:
        b_ids[int(mb.group(1))] = wk["workoutId"]

print(f"Found {len(a_ids)} Heavy A, {len(b_ids)} Heavy B workouts.\n", file=sys.stderr)

for w in range(1, 13):
    for ids, steps_fn, tag in ((a_ids, heavy_a_steps, "A"), (b_ids, heavy_b_steps, "B")):
        wid = ids.get(w)
        if not wid:
            print(f"  W{w} Heavy {tag}: NOT FOUND", file=sys.stderr)
            continue
        workout = garmin.get_workout_by_id(wid)
        workout["workoutSegments"][0]["workoutSteps"] = steps_fn(w)
        resp = garmin.client.put("connectapi", f"workout-service/workout/{wid}", json=workout)
        print(f"  {workout.get('workoutName')} ({wid}): HTTP {resp.status_code}", file=sys.stderr)

print("\nDone! Heavy A & B updated (calisthenics-first).", file=sys.stderr)
