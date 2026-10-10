import sys
from pathlib import Path

# Add person-b/nowcast to Python path
nowcast_path = (
    Path(__file__).resolve().parents[1] / "nowcast"
)

sys.path.insert(0, str(nowcast_path))

from trajectory import generate_trajectory


# Current storm position at T0
storm = {
    "id": "storm_1",
    "centroid_x": 40.0,
    "centroid_y": 45.0
}


# Motion calculated from previous observations
motion = {
    "vx": 0.3333333333,
    "vy": 0.1666666667
}


trajectory = generate_trajectory(
    storm,
    motion
)


print("\nStorm trajectory:")

for point in trajectory:
    print(point)