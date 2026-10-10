import sys
from pathlib import Path

import numpy as np

PERSON_B = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PERSON_B))

from data.imdaa_loader import load_imdaa
from storm_tracking.tracker import extract_storm_cells
from storm_tracking.motion import calculate_motion
from nowcast.geospatial import grid_to_latlon


DATASET = "person-b/data/processed/imdaa_20200715.nc"

LEAD_TIMES = [30, 60, 90, 120, 180, 360]


def detect_storms(field):
    threshold = np.percentile(field, 90)

    return extract_storm_cells(
        field,
        threshold=threshold,
        min_area=2
    )


def match_storms(previous_storms, current_storms):
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

    frame_0 = fields[0]
    frame_1 = fields[1]

    storms_0 = detect_storms(frame_0.field)
    storms_1 = detect_storms(frame_1.field)

    matches = match_storms(storms_0, storms_1)

    print("REAL IMDAA TRAJECTORY")
    print("=" * 60)

    print("T0:", frame_0.timestamp)
    print("T1:", frame_1.timestamp)
    print("Matched tracks:", len(matches))

    for track_id, (previous, current) in enumerate(matches, start=1):

        motion = calculate_motion(
            previous,
            current,
            time_minutes=60
        )

        print("\n" + "-" * 60)
        print(f"Storm track {track_id}")

        # Current storm location
        current_lat, current_lon = grid_to_latlon(
            current["centroid_x"],
            current["centroid_y"],
            frame_1.latitudes,
            frame_1.longitudes
        )

        print(
            f"Current position: "
            f"lat={current_lat:.4f}, "
            f"lon={current_lon:.4f}"
        )

        print(
            f"Motion: "
            f"vx={motion['vx']:.4f} grid/min, "
            f"vy={motion['vy']:.4f} grid/min"
        )

        print("\nForecast trajectory:")

        for lead_minutes in LEAD_TIMES:

            future_x = (
                current["centroid_x"]
                + motion["vx"] * lead_minutes
            )

            future_y = (
                current["centroid_y"]
                + motion["vy"] * lead_minutes
            )

            future_lat, future_lon = grid_to_latlon(
                future_x,
                future_y,
                frame_1.latitudes,
                frame_1.longitudes
            )

            print(
                f"+{lead_minutes:>3} min  "
                f"lat={future_lat:.4f}, "
                f"lon={future_lon:.4f}"
            )


if __name__ == "__main__":
    main()