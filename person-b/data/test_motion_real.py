import sys
from pathlib import Path

import numpy as np

# Add person-b to Python path
PERSON_B = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PERSON_B))

from data.imdaa_loader import load_imdaa
from storm_tracking.tracker import extract_storm_cells
from storm_tracking.motion import calculate_motion


DATASET = "person-b/data/processed/imdaa_20200715.nc"


def detect_storms(field):
    """
    Detect relatively strong precipitation cells.
    Units are intentionally not assumed.
    """
    threshold = np.percentile(field, 90)

    return extract_storm_cells(
        field,
        threshold=threshold,
        min_area=2
    )


def match_storms(previous_storms, current_storms):
    """
    Match each previous storm with the nearest current storm.
    This is a simple baseline tracker for our coarse 17x17 grid.
    """

    matches = []

    for previous in previous_storms:

        if not current_storms:
            continue

        nearest = min(
            current_storms,
            key=lambda current: (
                (current["centroid_x"] - previous["centroid_x"]) ** 2
                + (current["centroid_y"] - previous["centroid_y"]) ** 2
            )
        )

        matches.append((previous, nearest))

    return matches


def main():

    fields = load_imdaa(DATASET)

    # First two hourly frames
    frame_0 = fields[0]
    frame_1 = fields[1]

    storms_0 = detect_storms(frame_0.field)
    storms_1 = detect_storms(frame_1.field)

    print("Frame T0:", frame_0.timestamp)
    print("Storms detected:", len(storms_0))

    print("\nFrame T1:", frame_1.timestamp)
    print("Storms detected:", len(storms_1))

    matches = match_storms(storms_0, storms_1)

    print("\nMatched storm movements:")
    print("-" * 60)

    for index, (previous, current) in enumerate(matches, start=1):

        motion = calculate_motion(
            previous,
            current,
            time_minutes=60
        )

        print(f"\nStorm track {index}")

        print(
            "Previous:",
            f"({previous['centroid_x']:.2f}, "
            f"{previous['centroid_y']:.2f})"
        )

        print(
            "Current:",
            f"({current['centroid_x']:.2f}, "
            f"{current['centroid_y']:.2f})"
        )

        print(
            "Movement:",
            f"dx={motion['dx']:.2f}, "
            f"dy={motion['dy']:.2f}"
        )

        print(
            "Velocity:",
            f"vx={motion['vx']:.4f} pixels/min, "
            f"vy={motion['vy']:.4f} pixels/min"
        )

        print(
            "Speed:",
            f"{motion['speed_pixels_per_minute']:.4f} pixels/min"
        )

        print(
            "Direction:",
            f"{motion['direction_degrees']:.2f} degrees"
        )


if __name__ == "__main__":
    main()