#!/usr/bin/env python3
"""Upload 90-day strength program to Garmin Connect (3 phases x 3 workout types)."""
import json
import os
import sys

from garminconnect import Garmin

tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
garmin = Garmin()
garmin.login(tokenstore)
print("Logged in successfully.", file=sys.stderr)


def make_exercise_group(order, name, sets, reps, rest_sec=60, weight_desc=""):
    """Build a RepeatGroupDTO for one exercise: sets x (work + rest)."""
    desc = f"{name}: {sets}x{reps}"
    if weight_desc:
        desc += f" @{weight_desc}"

    work_step = {
        "type": "ExecutableStepDTO",
        "stepOrder": 1,
        "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
        "description": desc,
        "endCondition": {"conditionTypeId": 10, "conditionTypeKey": "reps"},
        "endConditionValue": float(reps) if isinstance(reps, int) else float(reps.split("-")[1]) if "-" in str(reps) else float(reps),
        "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
        "exerciseName": name,
    }

    rest_step = {
        "type": "ExecutableStepDTO",
        "stepOrder": 2,
        "stepType": {"stepTypeId": 4, "stepTypeKey": "recovery"},
        "description": f"Rest {rest_sec}s",
        "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
        "endConditionValue": float(rest_sec),
        "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
    }

    return {
        "type": "RepeatGroupDTO",
        "stepOrder": order,
        "numberOfIterations": sets,
        "workoutSteps": [work_step, rest_step],
    }


def make_timed_exercise_group(order, name, sets, duration_sec, rest_sec=60, weight_desc=""):
    """Build a RepeatGroupDTO for timed exercises (e.g. Farmer's Walk, Plank)."""
    desc = f"{name}: {sets}x{duration_sec}s"
    if weight_desc:
        desc += f" @{weight_desc}"

    work_step = {
        "type": "ExecutableStepDTO",
        "stepOrder": 1,
        "stepType": {"stepTypeId": 3, "stepTypeKey": "interval"},
        "description": desc,
        "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
        "endConditionValue": float(duration_sec),
        "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
        "exerciseName": name,
    }

    rest_step = {
        "type": "ExecutableStepDTO",
        "stepOrder": 2,
        "stepType": {"stepTypeId": 4, "stepTypeKey": "recovery"},
        "description": f"Rest {rest_sec}s",
        "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
        "endConditionValue": float(rest_sec),
        "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
    }

    return {
        "type": "RepeatGroupDTO",
        "stepOrder": order,
        "numberOfIterations": sets,
        "workoutSteps": [work_step, rest_step],
    }


def build_workout(name, description, exercises):
    """Build complete Garmin strength workout JSON."""
    steps = []
    for i, ex in enumerate(exercises):
        if ex.get("timed"):
            steps.append(make_timed_exercise_group(
                order=i + 1,
                name=ex["name"],
                sets=ex["sets"],
                duration_sec=ex["duration_sec"],
                rest_sec=ex.get("rest", 60),
                weight_desc=ex.get("weight", ""),
            ))
        else:
            steps.append(make_exercise_group(
                order=i + 1,
                name=ex["name"],
                sets=ex["sets"],
                reps=ex["reps"],
                rest_sec=ex.get("rest", 60),
                weight_desc=ex.get("weight", ""),
            ))

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


# =============================================================================
# PHASE 1 (Weeks 1-4): Foundation
# =============================================================================

phase1_heavy_a = build_workout(
    "F1 Heavy A (Sal/Cum)",
    "Faz 1 | Floor Press + Chin-Up focus | 3 set | Upper body agirlikli full body",
    [
        {"name": "Goblet Squat", "sets": 3, "reps": 10, "rest": 90, "weight": "14kg KB"},
        {"name": "Floor Press", "sets": 3, "reps": 12, "rest": 90, "weight": "10kg DB"},
        {"name": "Gorilla Row", "sets": 3, "reps": 10, "rest": 90, "weight": "14kg KB"},
        {"name": "Overhead Press", "sets": 3, "reps": 10, "rest": 90, "weight": "10kg DB"},
        {"name": "Chin Up", "sets": 3, "reps": 8, "rest": 90, "weight": "Assisted"},
        {"name": "Knee Raise", "sets": 3, "reps": 12, "rest": 60, "weight": "BW"},
    ],
)

phase1_heavy_b = build_workout(
    "F1 Heavy B (Per)",
    "Faz 1 | Dips + Inverted Row focus | 3 set | Upper body agirlikli full body",
    [
        {"name": "Goblet Squat", "sets": 3, "reps": 10, "rest": 90, "weight": "14kg KB"},
        {"name": "Dips", "sets": 3, "reps": 10, "rest": 90, "weight": "Assisted"},
        {"name": "Inverted Row", "sets": 3, "reps": 10, "rest": 90, "weight": "BW"},
        {"name": "Overhead Press", "sets": 3, "reps": 10, "rest": 90, "weight": "10kg DB"},
        {"name": "Gorilla Row", "sets": 3, "reps": 10, "rest": 90, "weight": "14kg KB"},
        {"name": "Knee Raise", "sets": 3, "reps": 12, "rest": 60, "weight": "BW"},
    ],
)

phase1_isolation = build_workout(
    "F1 Izole (Car/Cum/Paz)",
    "Faz 1 | Kol + Omuz + Forearm | Kosu gunu izolasyon | 20-30dk",
    [
        {"name": "Hammer Curl", "sets": 3, "reps": 12, "rest": 60, "weight": "5kg DB"},
        {"name": "Triceps Extension", "sets": 3, "reps": 12, "rest": 60, "weight": "5kg DB"},
        {"name": "Lateral Raise", "sets": 3, "reps": 15, "rest": 45, "weight": "3kg DB"},
        {"name": "Farmers Walk", "sets": 3, "duration_sec": 30, "rest": 60, "weight": "14kg KB", "timed": True},
    ],
)

# =============================================================================
# PHASE 2 (Weeks 5-8): Volume
# =============================================================================

phase2_heavy_a = build_workout(
    "F2 Heavy A (Sal/Cum)",
    "Faz 2 | Floor Press + Chin-Up focus | 4 set | Hacim artisi",
    [
        {"name": "Goblet Squat", "sets": 3, "reps": 12, "rest": 90, "weight": "16kg KB"},
        {"name": "Floor Press", "sets": 4, "reps": 12, "rest": 90, "weight": "10kg DB"},
        {"name": "Gorilla Row", "sets": 4, "reps": 10, "rest": 90, "weight": "16kg KB"},
        {"name": "Overhead Press", "sets": 4, "reps": 10, "rest": 90, "weight": "10kg DB"},
        {"name": "Chin Up", "sets": 3, "reps": 10, "rest": 90, "weight": "Assisted"},
        {"name": "Knee Raise", "sets": 3, "reps": 15, "rest": 60, "weight": "BW"},
    ],
)

phase2_heavy_b = build_workout(
    "F2 Heavy B (Per)",
    "Faz 2 | Dips + Inverted Row focus | 4 set | Hacim artisi",
    [
        {"name": "Goblet Squat", "sets": 3, "reps": 12, "rest": 90, "weight": "16kg KB"},
        {"name": "Dips", "sets": 4, "reps": 10, "rest": 90, "weight": "Assisted"},
        {"name": "Inverted Row", "sets": 4, "reps": 10, "rest": 90, "weight": "BW"},
        {"name": "Overhead Press", "sets": 4, "reps": 10, "rest": 90, "weight": "10kg DB"},
        {"name": "Gorilla Row", "sets": 4, "reps": 10, "rest": 90, "weight": "16kg KB"},
        {"name": "Knee Raise", "sets": 3, "reps": 15, "rest": 60, "weight": "BW"},
    ],
)

phase2_isolation = build_workout(
    "F2 Izole (Car/Cum/Paz)",
    "Faz 2 | Kol + Omuz + Forearm | Kosu gunu izolasyon | 4 set",
    [
        {"name": "Hammer Curl", "sets": 4, "reps": 12, "rest": 60, "weight": "10kg DB"},
        {"name": "Triceps Extension", "sets": 4, "reps": 12, "rest": 60, "weight": "10kg DB"},
        {"name": "Lateral Raise", "sets": 4, "reps": 15, "rest": 45, "weight": "5kg DB"},
        {"name": "Farmers Walk", "sets": 3, "duration_sec": 40, "rest": 60, "weight": "16kg KB", "timed": True},
    ],
)

# =============================================================================
# PHASE 3 (Weeks 9-12): Intensity
# =============================================================================

phase3_heavy_a = build_workout(
    "F3 Heavy A (Sal/Cum)",
    "Faz 3 | Floor Press + Chin-Up focus | 4 set | Maksimum agirlik",
    [
        {"name": "Goblet Squat", "sets": 4, "reps": 10, "rest": 90, "weight": "18-20kg KB"},
        {"name": "Floor Press", "sets": 4, "reps": 10, "rest": 90, "weight": "12.5kg DB"},
        {"name": "Gorilla Row", "sets": 4, "reps": 10, "rest": 90, "weight": "18kg KB"},
        {"name": "Overhead Press", "sets": 4, "reps": 8, "rest": 90, "weight": "12.5kg DB"},
        {"name": "Chin Up", "sets": 3, "reps": 8, "rest": 120, "weight": "BW"},
        {"name": "Knee Raise", "sets": 4, "reps": 15, "rest": 60, "weight": "BW"},
    ],
)

phase3_heavy_b = build_workout(
    "F3 Heavy B (Per)",
    "Faz 3 | Dips + Inverted Row focus | 4 set | Maksimum agirlik",
    [
        {"name": "Goblet Squat", "sets": 4, "reps": 10, "rest": 90, "weight": "18-20kg KB"},
        {"name": "Dips", "sets": 4, "reps": 10, "rest": 90, "weight": "BW"},
        {"name": "Inverted Row", "sets": 4, "reps": 10, "rest": 90, "weight": "BW"},
        {"name": "Overhead Press", "sets": 4, "reps": 8, "rest": 90, "weight": "12.5kg DB"},
        {"name": "Gorilla Row", "sets": 4, "reps": 10, "rest": 90, "weight": "18kg KB"},
        {"name": "Knee Raise", "sets": 4, "reps": 15, "rest": 60, "weight": "BW"},
    ],
)

phase3_isolation = build_workout(
    "F3 Izole (Car/Cum/Paz)",
    "Faz 3 | Kol + Omuz + Forearm | Kosu gunu izolasyon | Maksimum agirlik",
    [
        {"name": "Hammer Curl", "sets": 4, "reps": 10, "rest": 60, "weight": "12.5kg DB"},
        {"name": "Triceps Extension", "sets": 4, "reps": 10, "rest": 60, "weight": "12.5kg DB"},
        {"name": "Lateral Raise", "sets": 4, "reps": 12, "rest": 45, "weight": "5kg DB"},
        {"name": "Farmers Walk", "sets": 3, "duration_sec": 45, "rest": 60, "weight": "18-20kg KB", "timed": True},
    ],
)

# =============================================================================
# UPLOAD ALL WORKOUTS
# =============================================================================

all_workouts = [
    phase1_heavy_a, phase1_heavy_b, phase1_isolation,
    phase2_heavy_a, phase2_heavy_b, phase2_isolation,
    phase3_heavy_a, phase3_heavy_b, phase3_isolation,
]

results = []
for w in all_workouts:
    name = w["workoutName"]
    print(f"Uploading: {name}...", file=sys.stderr)
    try:
        result = garmin.upload_workout(w)
        workout_id = result.get("workoutId") if isinstance(result, dict) else None
        print(f"  OK — workout_id: {workout_id}", file=sys.stderr)
        results.append({"name": name, "workout_id": workout_id, "status": "success"})
    except Exception as e:
        print(f"  FAILED — {e}", file=sys.stderr)
        results.append({"name": name, "status": "error", "error": str(e)})

print("\n" + json.dumps(results, indent=2))
