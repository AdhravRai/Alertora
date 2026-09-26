import sys
from pathlib import Path

import numpy as np

PERSON_B = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PERSON_B))

from data.imdaa_loader import load_imdaa
from storm_tracking.tracker import extract_storm_cells
from storm_tracking.motion import calculate_motion
from storm_tracking.multiframe_tracker import (
    build_tracks,
    get_valid_tracks,
)
from nowcast.geospatial import grid_to_latlon


DATASET = "person-b/data/processed/imdaa_20200715.nc"

LEAD_TIMES = [30, 60, 90, 120, 180, 360]


def is_inside_domain(lat, lon, latitudes, longitudes):
    return (
        float(latitudes.min()) <= lat <= float(latitudes.max())
        and
        float(longitudes.min()) <= lon <= float(longitudes.max())
    )


def forecast_track(track, frame):

    observations = track["observations"]

    if len(observations) < 3:
        return None

    # Use the most recent observation as the forecast origin.
    latest = observations[-1]
    latest_storm = latest["storm"]

    # Use the first and latest observation to estimate
    # the overall persistent motion.
    first = observations[0]
    first_storm = first["storm"]

    elapsed_minutes = (
        latest["frame"] - first["frame"]
    ) * 60

    if elapsed_minutes <= 0:
        return None

    motion = calculate_motion(
        first_storm,
        latest_storm,
        time_minutes=elapsed_minutes
    )

    trajectory = []

    for lead_minutes in LEAD_TIMES:

        future_x = (
            latest_storm["centroid_x"]
            + motion["vx"] * lead_minutes
        )

        future_y = (
            latest_storm["centroid_y"]
            + motion["vy"] * lead_minutes
        )

        lat, lon = grid_to_latlon(
            future_x,
            future_y,
            frame.latitudes,
            frame.longitudes
        )

        in_domain = is_inside_domain(
            lat,
            lon,
            frame.latitudes,
            frame.longitudes
        )

        trajectory.append(
            {
                "lead_minutes": lead_minutes,
                "x": float(future_x),
                "y": float(future_y),
                "latitude": float(lat),
                "longitude": float(lon),
                "in_domain": bool(in_domain),
            }
        )

    return {
        "track_id": track["id"],
        "origin_frame": int(latest["frame"]),
        "origin_timestamp": str(latest["timestamp"]),
        "origin_x": float(latest_storm["centroid_x"]),
        "origin_y": float(latest_storm["centroid_y"]),
        "motion": {
            "vx_grid_per_min": float(motion["vx"]),
            "vy_grid_per_min": float(motion["vy"]),
            "speed_grid_per_min": float(
                motion["speed_pixels_per_minute"]
            ),
            "direction_degrees": float(
                motion["direction_degrees"]
            ),
        },
        "trajectory": trajectory,
    }


def main():

    print("=" * 70)
    print("ALERTORA - STORM FORECAST")
    print("=" * 70)

    fields = load_imdaa(DATASET)

    print("\nFrames loaded:", len(fields))

    tracks = build_tracks(fields)

    valid_tracks = get_valid_tracks(
        tracks,
        minimum_observations=3
    )

    print("Valid tracks:", len(valid_tracks))

    print("\n" + "=" * 70)
    print("FORECAST TRAJECTORIES")
    print("=" * 70)

    forecast_count = 0

    # Use each track's final observed frame.
    for track in valid_tracks:

        latest_frame_index = (
            track["observations"][-1]["frame"]
        )

        frame = fields[latest_frame_index]

        forecast = forecast_track(
            track,
            frame
        )

        if forecast is None:
            continue

        forecast_count += 1

        print("\n" + "-" * 70)

        print(
            "Track:",
            forecast["track_id"]
        )

        print(
            "Origin:",
            forecast["origin_timestamp"]
        )

        print(
            "Motion:",
            forecast["motion"]
        )

        print("\nTrajectory:")

        for point in forecast["trajectory"]:

            print(
                f"+{point['lead_minutes']:>3} min | "
                f"lat={point['latitude']:.4f} | "
                f"lon={point['longitude']:.4f} | "
                f"in_domain={point['in_domain']}"
            )

    print("\n" + "=" * 70)
    print(
        "Forecasts generated:",
        forecast_count
    )


if __name__ == "__main__":
    main()
    