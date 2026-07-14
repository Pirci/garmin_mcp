#!/usr/bin/env python3
"""
Rebuild the 90-day program with:
1. Pull-Up (Assisted) added to Heavy B
2. Weekly progressive overload (reps → sets → weight)
3. Deload every 4th week (W4, W8, W12)

Result: 36 unique workouts (12 Heavy A + 12 Heavy B + 12 Isolation)
Scheduled: 84 sessions (7 days/week x 12 weeks)
"""
import json
import os
import sys
from datetime import date, timedelta

from garminconnect import Garmin

tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
garmin = Garmin()
garmin.login(tokenstore)
print("Logged in successfully.\n", file=sys.stderr)

R = 120   # compound rest
Ri = 90   # isolation rest


# =============================================================================
# HELPERS
# =============================================================================

def rep_group(order, name, sets, reps, rest, weight=""):
    desc = f"{name}: {sets}x{reps}"
    if weight:
        desc += f" @{weight}"
    return {
        "type": "RepeatGroupDTO", "stepOrder": order,
        "numberOfIterations": sets,
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


def timed_group(order, name, sets, dur, rest, weight=""):
    desc = f"{name}: {sets}x{dur}s"
    if weight:
        desc += f" @{weight}"
    return {
        "type": "RepeatGroupDTO", "stepOrder": order,
        "numberOfIterations": sets,
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
# WEEKLY PROGRESSION TABLES
# Week pattern per phase: W1=build, W2=build, W3=peak, W4=deload
# =============================================================================

# --- HEAVY A: Goblet Squat, Floor Press, Gorilla Row, OHP, Chin-Up, Knee Raise ---
HEAVY_A = [
    # Phase 1 (W1-W4)
    {"w": 1,  "dl": False, "sq": (3,10,"14kg KB"), "fp": (3,10,"10kg DB"), "gr": (3,10,"14kg KB"), "ohp": (3, 8,"10kg DB"), "chin": (3,5, "Assisted"), "kr": (3,10,"BW")},
    {"w": 2,  "dl": False, "sq": (3,12,"14kg KB"), "fp": (3,12,"10kg DB"), "gr": (3,12,"14kg KB"), "ohp": (3,10,"10kg DB"), "chin": (3,6, "Assisted"), "kr": (3,12,"BW")},
    {"w": 3,  "dl": False, "sq": (4,10,"14kg KB"), "fp": (4,10,"10kg DB"), "gr": (4,10,"14kg KB"), "ohp": (4, 8,"10kg DB"), "chin": (3,8, "Assisted"), "kr": (3,15,"BW")},
    {"w": 4,  "dl": True,  "sq": (2,10,"12kg KB"), "fp": (2,10,"10kg DB"), "gr": (2,10,"12kg KB"), "ohp": (2, 8,"10kg DB"), "chin": (2,5, "Assisted"), "kr": (2,10,"BW")},
    # Phase 2 (W5-W8)
    {"w": 5,  "dl": False, "sq": (3,10,"16kg KB"), "fp": (3,12,"10kg DB"), "gr": (3,10,"16kg KB"), "ohp": (3,10,"10kg DB"), "chin": (3,8, "Assisted"), "kr": (3,12,"BW")},
    {"w": 6,  "dl": False, "sq": (3,12,"16kg KB"), "fp": (4,10,"10kg DB"), "gr": (3,12,"16kg KB"), "ohp": (3,12,"10kg DB"), "chin": (3,10,"Assisted"), "kr": (3,15,"BW")},
    {"w": 7,  "dl": False, "sq": (4,10,"16kg KB"), "fp": (4,12,"10kg DB"), "gr": (4,10,"16kg KB"), "ohp": (4,10,"10kg DB"), "chin": (4,8, "Assisted"), "kr": (4,12,"BW")},
    {"w": 8,  "dl": True,  "sq": (2,10,"14kg KB"), "fp": (2,10,"10kg DB"), "gr": (2,10,"14kg KB"), "ohp": (2,10,"10kg DB"), "chin": (2,8, "Assisted"), "kr": (2,12,"BW")},
    # Phase 3 (W9-W12)
    {"w": 9,  "dl": False, "sq": (3,10,"18kg KB"), "fp": (4,12,"10kg DB"), "gr": (3,10,"18kg KB"), "ohp": (4,10,"10kg DB"), "chin": (3,4, "BW"),       "kr": (4,12,"BW")},
    {"w": 10, "dl": False, "sq": (3,12,"18kg KB"), "fp": (4,15,"10kg DB"), "gr": (3,12,"18kg KB"), "ohp": (4,12,"10kg DB"), "chin": (3,5, "BW"),       "kr": (4,15,"BW")},
    {"w": 11, "dl": False, "sq": (4,10,"20kg KB"), "fp": (5,12,"10kg DB"), "gr": (4,10,"18kg KB"), "ohp": (5,10,"10kg DB"), "chin": (3,6, "BW"),       "kr": (5,12,"BW")},
    {"w": 12, "dl": True,  "sq": (2,10,"16kg KB"), "fp": (2,12,"10kg DB"), "gr": (2,10,"16kg KB"), "ohp": (2,10,"10kg DB"), "chin": (2,4, "BW"),       "kr": (2,12,"BW")},
]

# --- HEAVY B: Goblet Squat, Dips, Pull-Up, Inverted Row, OHP, Knee Raise ---
HEAVY_B = [
    # Phase 1
    {"w": 1,  "dl": False, "sq": (3,10,"14kg KB"), "dip": (3, 6,"Assisted"), "pu": (3,4, "Assisted"), "ir": (3, 8,"BW"), "ohp": (3, 8,"10kg DB"), "kr": (3,10,"BW")},
    {"w": 2,  "dl": False, "sq": (3,12,"14kg KB"), "dip": (3, 8,"Assisted"), "pu": (3,5, "Assisted"), "ir": (3,10,"BW"), "ohp": (3,10,"10kg DB"), "kr": (3,12,"BW")},
    {"w": 3,  "dl": False, "sq": (4,10,"14kg KB"), "dip": (3,10,"Assisted"), "pu": (3,6, "Assisted"), "ir": (3,12,"BW"), "ohp": (4, 8,"10kg DB"), "kr": (3,15,"BW")},
    {"w": 4,  "dl": True,  "sq": (2,10,"12kg KB"), "dip": (2, 6,"Assisted"), "pu": (2,4, "Assisted"), "ir": (2, 8,"BW"), "ohp": (2, 8,"10kg DB"), "kr": (2,10,"BW")},
    # Phase 2
    {"w": 5,  "dl": False, "sq": (3,10,"16kg KB"), "dip": (3,10,"Assisted"), "pu": (3,6, "Assisted"), "ir": (3,12,"BW"), "ohp": (3,10,"10kg DB"), "kr": (3,12,"BW")},
    {"w": 6,  "dl": False, "sq": (3,12,"16kg KB"), "dip": (3,12,"Assisted"), "pu": (3,8, "Assisted"), "ir": (4,10,"BW"), "ohp": (3,12,"10kg DB"), "kr": (3,15,"BW")},
    {"w": 7,  "dl": False, "sq": (4,10,"16kg KB"), "dip": (4,10,"Assisted"), "pu": (4,6, "Assisted"), "ir": (4,12,"BW"), "ohp": (4,10,"10kg DB"), "kr": (4,12,"BW")},
    {"w": 8,  "dl": True,  "sq": (2,10,"14kg KB"), "dip": (2,10,"Assisted"), "pu": (2,6, "Assisted"), "ir": (2,10,"BW"), "ohp": (2,10,"10kg DB"), "kr": (2,12,"BW")},
    # Phase 3
    {"w": 9,  "dl": False, "sq": (3,10,"18kg KB"), "dip": (3, 6,"BW"),       "pu": (3,3, "BW"),       "ir": (4,12,"BW"), "ohp": (4,10,"10kg DB"), "kr": (4,12,"BW")},
    {"w": 10, "dl": False, "sq": (3,12,"18kg KB"), "dip": (3, 8,"BW"),       "pu": (3,4, "BW"),       "ir": (4,15,"BW"), "ohp": (4,12,"10kg DB"), "kr": (4,15,"BW")},
    {"w": 11, "dl": False, "sq": (4,10,"20kg KB"), "dip": (3,10,"BW"),       "pu": (3,5, "BW"),       "ir": (5,12,"BW"), "ohp": (5,10,"10kg DB"), "kr": (5,12,"BW")},
    {"w": 12, "dl": True,  "sq": (2,10,"16kg KB"), "dip": (2, 6,"BW"),       "pu": (2,3, "BW"),       "ir": (2,12,"BW"), "ohp": (2,10,"10kg DB"), "kr": (2,12,"BW")},
]

# --- ISOLATION: Hammer Curl, Triceps Extension, Lateral Raise, Farmer's Walk ---
ISOLATION = [
    # Phase 1
    {"w": 1,  "dl": False, "hc": (3,10,"5kg DB"),  "te": (3,10,"5kg DB"),  "lr": (3,12,"3kg DB"), "fw": (3,30,"14kg KB")},
    {"w": 2,  "dl": False, "hc": (3,12,"5kg DB"),  "te": (3,12,"5kg DB"),  "lr": (3,15,"3kg DB"), "fw": (3,35,"14kg KB")},
    {"w": 3,  "dl": False, "hc": (3,15,"5kg DB"),  "te": (3,15,"5kg DB"),  "lr": (4,12,"3kg DB"), "fw": (3,40,"14kg KB")},
    {"w": 4,  "dl": True,  "hc": (2,10,"5kg DB"),  "te": (2,10,"5kg DB"),  "lr": (2,12,"3kg DB"), "fw": (2,30,"12kg KB")},
    # Phase 2
    {"w": 5,  "dl": False, "hc": (3,10,"10kg DB"), "te": (3,10,"10kg DB"), "lr": (3,12,"5kg DB"), "fw": (3,30,"16kg KB")},
    {"w": 6,  "dl": False, "hc": (3,12,"10kg DB"), "te": (3,12,"10kg DB"), "lr": (3,15,"5kg DB"), "fw": (3,35,"16kg KB")},
    {"w": 7,  "dl": False, "hc": (4,10,"10kg DB"), "te": (4,10,"10kg DB"), "lr": (4,12,"5kg DB"), "fw": (3,40,"16kg KB")},
    {"w": 8,  "dl": True,  "hc": (2,10,"5kg DB"),  "te": (2,10,"5kg DB"),  "lr": (2,12,"5kg DB"), "fw": (2,30,"14kg KB")},
    # Phase 3
    {"w": 9,  "dl": False, "hc": (3,12,"10kg DB"), "te": (3,12,"10kg DB"), "lr": (4,12,"5kg DB"), "fw": (3,30,"18kg KB")},
    {"w": 10, "dl": False, "hc": (4,10,"10kg DB"), "te": (4,10,"10kg DB"), "lr": (4,15,"5kg DB"), "fw": (3,35,"18kg KB")},
    {"w": 11, "dl": False, "hc": (4,12,"10kg DB"), "te": (4,12,"10kg DB"), "lr": (5,12,"5kg DB"), "fw": (3,40,"20kg KB")},
    {"w": 12, "dl": True,  "hc": (2,10,"10kg DB"), "te": (2,10,"10kg DB"), "lr": (2,12,"5kg DB"), "fw": (2,30,"16kg KB")},
]


def _rg(order, name, tup, rest):
    """Build rep_group from (sets, reps, weight) tuple."""
    sets, reps, weight = tup
    return rep_group(order, name, sets, reps, rest, weight)


def build_heavy_a(week_data):
    w = week_data["w"]
    dl = " [DELOAD]" if week_data["dl"] else ""
    phase = "F1" if w <= 4 else "F2" if w <= 8 else "F3"
    s = week_data
    return workout(
        f"W{w} Heavy A{dl}",
        f"{phase} Hafta {w} | Floor Press + Chin-Up{dl}",
        [
            _rg(1, "Goblet Squat",   s["sq"],   R),
            _rg(2, "Floor Press",    s["fp"],   R),
            _rg(3, "Gorilla Row",    s["gr"],   R),
            _rg(4, "Overhead Press", s["ohp"],  R),
            _rg(5, "Chin Up",        s["chin"], R),
            _rg(6, "Knee Raise",     s["kr"],   Ri),
        ],
    )


def build_heavy_b(week_data):
    w = week_data["w"]
    dl = " [DELOAD]" if week_data["dl"] else ""
    phase = "F1" if w <= 4 else "F2" if w <= 8 else "F3"
    s = week_data
    return workout(
        f"W{w} Heavy B{dl}",
        f"{phase} Hafta {w} | Dips + Pull-Up{dl}",
        [
            _rg(1, "Goblet Squat",   s["sq"],  R),
            _rg(2, "Dips",           s["dip"], R),
            _rg(3, "Pull Up",        s["pu"],  R),
            _rg(4, "Inverted Row",   s["ir"],  R),
            _rg(5, "Overhead Press", s["ohp"], R),
            _rg(6, "Knee Raise",     s["kr"],  Ri),
        ],
    )


def build_isolation(week_data):
    w = week_data["w"]
    dl = " [DELOAD]" if week_data["dl"] else ""
    phase = "F1" if w <= 4 else "F2" if w <= 8 else "F3"
    s = week_data
    return workout(
        f"W{w} Izole{dl}",
        f"{phase} Hafta {w} | Kol + Omuz + Forearm{dl}",
        [
            _rg(        1, "Hammer Curl",        s["hc"], Ri),
            _rg(        2, "Triceps Extension",  s["te"], Ri),
            _rg(        3, "Lateral Raise",      s["lr"], Ri),
            timed_group(4, "Farmers Walk",   s["fw"][0], s["fw"][1], Ri, s["fw"][2]),
        ],
    )


# =============================================================================
# STEP 1: Clean up old workouts
# =============================================================================
print("=== STEP 1: Cleaning old schedule & workouts ===", file=sys.stderr)

OLD_IDS = [
    1630804979, 1630804988, 1630805008,
    1630805017, 1630805022, 1630805026,
    1630805032, 1630805036, 1630805040,
]

query = {"query": 'query{workoutScheduleSummariesScalar(startDate:"2026-07-13", endDate:"2026-10-05")}'}
result = garmin.query_garmin_graphql(query)
scheduled = result.get("data", {}).get("workoutScheduleSummariesScalar", [])
old_set = set(OLD_IDS)

removed = 0
for s in scheduled:
    if s.get("workoutId") in old_set:
        try:
            garmin.unschedule_workout(s["scheduledWorkoutId"])
            removed += 1
        except:
            pass
print(f"  Unscheduled {removed} entries.", file=sys.stderr)

for wid in OLD_IDS:
    try:
        garmin.delete_workout(wid)
    except:
        pass
print(f"  Deleted {len(OLD_IDS)} old workouts.", file=sys.stderr)


# =============================================================================
# STEP 2: Create 36 new workouts
# =============================================================================
print("\n=== STEP 2: Creating 36 weekly workouts ===", file=sys.stderr)

week_ids = {}  # {(week, type): workout_id}

for i, ha in enumerate(HEAVY_A):
    w = ha["w"]
    wk = build_heavy_a(ha)
    result = garmin.upload_workout(wk)
    wid = result.get("workoutId")
    week_ids[(w, "HA")] = wid
    dl = " [DL]" if ha["dl"] else ""
    print(f"  W{w:2d} Heavy A{dl:8s} -> {wid}", file=sys.stderr)

for i, hb in enumerate(HEAVY_B):
    w = hb["w"]
    wk = build_heavy_b(hb)
    result = garmin.upload_workout(wk)
    wid = result.get("workoutId")
    week_ids[(w, "HB")] = wid
    dl = " [DL]" if hb["dl"] else ""
    print(f"  W{w:2d} Heavy B{dl:8s} -> {wid}", file=sys.stderr)

for i, iso in enumerate(ISOLATION):
    w = iso["w"]
    wk = build_isolation(iso)
    result = garmin.upload_workout(wk)
    wid = result.get("workoutId")
    week_ids[(w, "ISO")] = wid
    dl = " [DL]" if iso["dl"] else ""
    print(f"  W{w:2d} Izole{dl:10s} -> {wid}", file=sys.stderr)


# =============================================================================
# STEP 3: Schedule 84 sessions (7 days x 12 weeks)
# =============================================================================
print("\n=== STEP 3: Scheduling 84 sessions ===", file=sys.stderr)

start_monday = date(2026, 7, 13)
schedule = []

for week in range(12):
    w = week + 1
    monday = start_monday + timedelta(weeks=week)

    # Mon: Isolation
    schedule.append({"date": str(monday),                    "wid": week_ids[(w, "ISO")], "label": f"W{w} Pzt Izole"})
    # Tue: Heavy A
    schedule.append({"date": str(monday + timedelta(days=1)), "wid": week_ids[(w, "HA")],  "label": f"W{w} Sal Heavy A"})
    # Wed: Isolation
    schedule.append({"date": str(monday + timedelta(days=2)), "wid": week_ids[(w, "ISO")], "label": f"W{w} Car Izole"})
    # Thu: Heavy B
    schedule.append({"date": str(monday + timedelta(days=3)), "wid": week_ids[(w, "HB")],  "label": f"W{w} Per Heavy B"})
    # Fri: Isolation
    schedule.append({"date": str(monday + timedelta(days=4)), "wid": week_ids[(w, "ISO")], "label": f"W{w} Cum Izole"})
    # Sat: Heavy A
    schedule.append({"date": str(monday + timedelta(days=5)), "wid": week_ids[(w, "HA")],  "label": f"W{w} Cum Heavy A"})
    # Sun: Isolation
    schedule.append({"date": str(monday + timedelta(days=6)), "wid": week_ids[(w, "ISO")], "label": f"W{w} Paz Izole"})

success = 0
for item in schedule:
    try:
        url = f"workout-service/schedule/{item['wid']}"
        resp = garmin.client.post("connectapi", url, json={"date": item["date"]})
        if resp.status_code == 200:
            success += 1
        else:
            print(f"  WARN: {item['label']} HTTP {resp.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"  FAIL: {item['label']} {e}", file=sys.stderr)

print(f"\nDone: {success}/{len(schedule)} sessions scheduled.", file=sys.stderr)
print(json.dumps({"workouts_created": len(week_ids), "sessions_scheduled": success}, indent=2))
