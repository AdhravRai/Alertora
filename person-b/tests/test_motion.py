import sys
from pathlib import Path

# Add person-b/storm_tracking to Python path
storm_tracking_path = (
    Path(__file__).resolve().parents[1] / "storm_tracking"
)

sys.path.insert(0, str(storm_tracking_path))

from motion import calculate_motion


# Storm position at T-30
previous_storm = {
    "id": "storm_1",
    "centroid_x": 30.0,
    "centroid_y": 40.0
}


# Same storm at T0
current_storm = {
    "id": "storm_1",
    "centroid_x": 40.0,
    "centroid_y": 45.0
}


# Calculate movement
motion = calculate_motion(
    previous_storm,
    current_storm,
    time_minutes=30
)


print("\nStorm motion:")
print(motion)