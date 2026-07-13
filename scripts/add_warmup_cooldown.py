#!/usr/bin/env python3
"""Add warm-up and cool-down steps to all 9 workouts (in-place update)."""
import json
import os
import sys

from garminconnect import Garmin

tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
garmin = Garmin()
garmin.login(tokenstore)
print("Logged in successfully.", file=sys.stderr)


def warmup_step(order, description, duration_sec):
    return {
        "type": "ExecutableStepDTO",
        "stepOrder": order,
        "stepType": {"stepTypeId": 1, "stepTypeKey": "warmup"},
        "description": description,
        "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
        "endConditionValue": float(duration_sec),
        "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
    }


def cooldown_step(order, description, duration_sec):
    return {
        "type": "ExecutableStepDTO",
        "stepOrder": order,
        "stepType": {"stepTypeId": 2, "stepTypeKey": "cooldown"},
        "description": description,
        "endCondition": {"conditionTypeId": 2, "conditionTypeKey": "time"},
        "endConditionValue": float(duration_sec),
        "targetType": {"workoutTargetTypeId": 1, "workoutTargetTypeKey": "no.target"},
    }


# =============================================================================
# WARM-UP & COOL-DOWN DEFINITIONS per workout type
# =============================================================================

# Heavy A: Goblet Squat, Floor Press, Gorilla Row, OHP, Chin-Up, Knee Raise
# Muscles: chest, back, shoulders, biceps, quads, core
HEAVY_A_WARMUP = [
    warmup_step(1, "Kol cevirmeler + Omuz rotasyonlari", 90),
    warmup_step(2, "KB Halo (hafif) + Bodyweight Squat", 90),
    warmup_step(3, "Incline Push-Up (yavas) + Scapula Pull-Up", 90),
]

HEAVY_A_COOLDOWN = [
    cooldown_step(1, "Gogus germe (kapi veya duvar) + Lat germe", 90),
    cooldown_step(2, "Omuz cross-body + Triceps germe + Biceps germe", 90),
    cooldown_step(3, "Hip flexor germe + Hamstring germe + Quadriceps germe", 90),
]

# Heavy B: Goblet Squat, Dips, Inverted Row, OHP, Gorilla Row, Knee Raise
# Muscles: chest, triceps, back, shoulders, quads, core
HEAVY_B_WARMUP = [
    warmup_step(1, "Kol cevirmeler + Omuz rotasyonlari", 90),
    warmup_step(2, "KB Halo (hafif) + Bodyweight Squat", 90),
    warmup_step(3, "Scapula Dips (yavas) + Scapula Pull-Up", 90),
]

HEAVY_B_COOLDOWN = [
    cooldown_step(1, "Gogus germe (kapi veya duvar) + Triceps germe", 90),
    cooldown_step(2, "Lat germe + Omuz cross-body + Biceps germe", 90),
    cooldown_step(3, "Hip flexor germe + Hamstring germe + Quadriceps germe", 90),
]

# Isolation: Hammer Curl, Triceps Extension, Lateral Raise, Farmer's Walk
# Muscles: biceps, triceps, shoulders (lateral), forearms
ISOLATION_WARMUP = [
    warmup_step(1, "Bilek cevirmeler + Onkol rotasyonlari", 60),
    warmup_step(2, "Kol salinimlari + Omuz cevirmeler (ileri-geri)", 90),
]

ISOLATION_COOLDOWN = [
    cooldown_step(1, "Biceps germe + Triceps germe + Onkol germe", 90),
    cooldown_step(2, "Omuz cross-body germe + Boyun yan germe + Trap germe", 90),
]

# =============================================================================
# Map workout IDs to their warm-up/cool-down
# =============================================================================

WORKOUT_CONFIG = {
    1630804979: ("F1 Heavy A", HEAVY_A_WARMUP, HEAVY_A_COOLDOWN),
    1630804988: ("F1 Heavy B", HEAVY_B_WARMUP, HEAVY_B_COOLDOWN),
    1630805008: ("F1 Izole",   ISOLATION_WARMUP, ISOLATION_COOLDOWN),
    1630805017: ("F2 Heavy A", HEAVY_A_WARMUP, HEAVY_A_COOLDOWN),
    1630805022: ("F2 Heavy B", HEAVY_B_WARMUP, HEAVY_B_COOLDOWN),
    1630805026: ("F2 Izole",   ISOLATION_WARMUP, ISOLATION_COOLDOWN),
    1630805032: ("F3 Heavy A", HEAVY_A_WARMUP, HEAVY_A_COOLDOWN),
    1630805036: ("F3 Heavy B", HEAVY_B_WARMUP, HEAVY_B_COOLDOWN),
    1630805040: ("F3 Izole",   ISOLATION_WARMUP, ISOLATION_COOLDOWN),
}

for wid, (name, wu_steps, cd_steps) in WORKOUT_CONFIG.items():
    print(f"Updating: {name} ({wid})...", file=sys.stderr, end=" ")

    workout = garmin.get_workout_by_id(wid)
    segment = workout["workoutSegments"][0]
    existing_steps = segment["workoutSteps"]

    # Build new step list: warm-up + existing (renumbered) + cool-down
    new_steps = []
    order = 1

    # Warm-up steps
    for ws in wu_steps:
        ws = dict(ws)
        ws["stepOrder"] = order
        new_steps.append(ws)
        order += 1

    # Existing exercise steps (renumber)
    for step in existing_steps:
        step = dict(step)
        step["stepOrder"] = order
        new_steps.append(step)
        order += 1

    # Cool-down steps
    for cs in cd_steps:
        cs = dict(cs)
        cs["stepOrder"] = order
        new_steps.append(cs)
        order += 1

    segment["workoutSteps"] = new_steps

    # Update via PUT
    url = f"workout-service/workout/{wid}"
    resp = garmin.client.put("connectapi", url, json=workout)
    print(f"HTTP {resp.status_code} ({len(wu_steps)} warmup + {len(existing_steps)} exercise + {len(cd_steps)} cooldown = {len(new_steps)} steps)", file=sys.stderr)

print("\nDone! All workouts updated with warm-up and cool-down.", file=sys.stderr)
