import sys
from pathlib import Path
import json

# ---------------------------------------------------------
# Python path
# ---------------------------------------------------------

PERSON_B = Path(__file__).resolve().parent
sys.path.insert(0, str(PERSON_B))


# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------

from data.imdaa_loader import load_imdaa

from storm_tracking.multiframe_tracker import (
    build_tracks,
    get_valid_tracks,
)

from storm_tracking.motion import calculate_motion

from nowcast.geospatial import grid_to_latlon

from hazards.engine import (
    summarize_precipitation,
    detect_relative_heavy_rain,
    detect_relative_extreme,
)

from hazards.fusion import fuse_hazards


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DATASET = (
    "person-b/data/processed/"
    "imdaa_20200715.nc"
)

OUTPUT_FILE = (
    "person-b/output/nowcast_result.json"
)

LEAD_TIMES = [30, 60, 90, 120, 180, 360]

MIN_OBSERVATIONS = 3


# ---------------------------------------------------------
# Domain check
# ---------------------------------------------------------

def is_inside_domain(
    lat,
    lon,
    latitudes,
    longitudes
):
    """
    Check whether a predicted location is inside
    the spatial domain of the IMDAA dataset.
    """

    return (
        float(latitudes.min())
        <= float(lat)
        <= float(latitudes.max())
        and
        float(longitudes.min())
        <= float(lon)
        <= float(longitudes.max())
    )


# ---------------------------------------------------------
# Build trajectory for one storm
# ---------------------------------------------------------

def build_trajectory(track, frame):
    """
    Generate +30m, +60m, +90m, +2h, +3h and +6h
    trajectory from a valid multi-frame storm track.
    """

    observations = track["observations"]

    if len(observations) < MIN_OBSERVATIONS:
        return None

    first = observations[0]
    latest = observations[-1]

    first_storm = first["storm"]
    latest_storm = latest["storm"]

    elapsed_minutes = (
        latest["frame"] - first["frame"]
    ) * 60

    if elapsed_minutes <= 0:
        return None

    # Estimate persistent motion from the complete
    # observed track.
    motion = calculate_motion(
        first_storm,
        latest_storm,
        elapsed_minutes
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

        latitude, longitude = grid_to_latlon(
            future_x,
            future_y,
            frame.latitudes,
            frame.longitudes
        )

        in_domain = is_inside_domain(
            latitude,
            longitude,
            frame.latitudes,
            frame.longitudes
        )

        trajectory.append(
            {
                "lead_minutes": int(lead_minutes),
                "latitude": float(latitude),
                "longitude": float(longitude),
                "grid_x": float(future_x),
                "grid_y": float(future_y),
                "in_domain": bool(in_domain),
            }
        )

    return {
        "motion": {
            "vx_grid_per_min": float(
                motion["vx"]
            ),
            "vy_grid_per_min": float(
                motion["vy"]
            ),
            "speed_grid_per_min": float(
                motion["speed_pixels_per_minute"]
            ),
            "direction_degrees": float(
                motion["direction_degrees"]
            ),
        },
        "trajectory": trajectory,
    }


# ---------------------------------------------------------
# Build storm output
# ---------------------------------------------------------

def build_storm_output(track, fields):
    """
    Convert a tracked storm into the final JSON structure.
    """

    observations = track["observations"]

    if len(observations) < MIN_OBSERVATIONS:
        return None

    latest = observations[-1]

    latest_frame_index = latest["frame"]

    frame = fields[latest_frame_index]

    storm = latest["storm"]

    latitude, longitude = grid_to_latlon(
        storm["centroid_x"],
        storm["centroid_y"],
        frame.latitudes,
        frame.longitudes
    )

    trajectory_result = build_trajectory(
        track,
        frame
    )

    if trajectory_result is None:
        return None

    return {
        "track_id": track["id"],

        "observation_count": int(
            len(observations)
        ),

        "first_frame": int(
            observations[0]["frame"]
        ),

        "last_frame": int(
            observations[-1]["frame"]
        ),

        "latest_timestamp": str(
            latest["timestamp"]
        ),

        "current_position": {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "grid_x": float(
                storm["centroid_x"]
            ),
            "grid_y": float(
                storm["centroid_y"]
            ),
        },

        "intensity": {
            "max_raw": float(
                storm["max_intensity"]
            ),
            "mean_raw": float(
                storm["mean_intensity"]
            ),
        },

        "area_pixels": int(
            storm["area_pixels"]
        ),

        "motion": trajectory_result["motion"],

        "trajectory": trajectory_result[
            "trajectory"
        ],
    }


# ---------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------

def main():

    print("=" * 70)
    print("ALERTORA - PERSON B SPATIAL NOWCAST PIPELINE")
    print("=" * 70)

    # -----------------------------------------------------
    # 1. Load IMDAA
    # -----------------------------------------------------

    print("\n[1/6] Loading IMDAA dataset...")

    fields = load_imdaa(DATASET)

    print(
        f"Loaded {len(fields)} spatial frames."
    )

    latest_frame = fields[-1]

    # -----------------------------------------------------
    # 2. Build multi-frame storm tracks
    # -----------------------------------------------------

    print("\n[2/6] Building multi-frame storm tracks...")

    tracks = build_tracks(fields)

    valid_tracks = get_valid_tracks(
        tracks,
        minimum_observations=MIN_OBSERVATIONS
    )

    print(
        f"Raw tracks: {len(tracks)}"
    )

    print(
        f"Valid tracks: {len(valid_tracks)}"
    )

    # -----------------------------------------------------
    # 3. Current precipitation field
    # -----------------------------------------------------

    print("\n[3/6] Analyzing precipitation field...")

    precipitation = latest_frame.field

    precipitation_summary = (
        summarize_precipitation(
            precipitation
        )
    )

    relative_heavy_rain = (
        detect_relative_heavy_rain(
            precipitation
        )
    )

    relative_extreme = (
        detect_relative_extreme(
            precipitation
        )
    )

    # -----------------------------------------------------
    # 4. Hazard fusion
    # -----------------------------------------------------

    print("\n[4/6] Fusing hazard indicators...")

    hazard_result = fuse_hazards(
        precipitation_summary,
        relative_heavy_rain,
        relative_extreme
    )

    # -----------------------------------------------------
    # 5. Build storm trajectories
    # -----------------------------------------------------

    print("\n[5/6] Generating storm trajectories...")

    storms = []

    for track in valid_tracks:

        storm_output = build_storm_output(
            track,
            fields
        )

        if storm_output is not None:
            storms.append(
                storm_output
            )

    print(
        f"Storm forecasts generated: "
        f"{len(storms)}"
    )

    # -----------------------------------------------------
    # 6. Final JSON
    # -----------------------------------------------------

    print("\n[6/6] Creating final output...")

    result = {

        "forecast_time": str(
            latest_frame.timestamp
        ),

        "dataset": {
            "name": "IMDAA",

            "source_file": (
                "data/processed/"
                "imdaa_20200715.nc"
            ),

            "frame_count": int(
                len(fields)
            ),

            "grid_shape": [
                int(
                    len(latest_frame.latitudes)
                ),
                int(
                    len(latest_frame.longitudes)
                ),
            ],

            "latitude_range": [
                float(
                    latest_frame.latitudes.min()
                ),
                float(
                    latest_frame.latitudes.max()
                ),
            ],

            "longitude_range": [
                float(
                    latest_frame.longitudes.min()
                ),
                float(
                    latest_frame.longitudes.max()
                ),
            ],
        },

        "storms": storms,

        "trajectory": [
            {
                "track_id": storm[
                    "track_id"
                ],

                "points": storm[
                    "trajectory"
                ],
            }

            for storm in storms
        ],

        "hazards": hazard_result,

        "eta": {
            "status": "not_computed",

            "reason": (
                "No target location was "
                "provided for ETA calculation."
            ),
        },

        "metadata": {

            "forecast_leads_minutes":
                LEAD_TIMES,

            "minimum_track_observations":
                MIN_OBSERVATIONS,

            "precipitation_units":
                "unverified",

            "precipitation_semantics":
                "native IMDAA values",

            "note": (
                "Relative precipitation indicators "
                "are used until the IMDAA APCP "
                "unit convention is verified."
            ),
        },
    }

    # -----------------------------------------------------
    # Write output
    # -----------------------------------------------------

    output_path = Path(
        OUTPUT_FILE
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            result,
            file,
            indent=2
        )

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    print(
        f"\nForecast time: "
        f"{result['forecast_time']}"
    )

    print(
        f"Storm forecasts: "
        f"{len(storms)}"
    )

    print(
        "Hazard fusion: "
        "complete"
    )

    print(
        "ETA: "
        "not computed (no target)"
    )

    print(
        f"\nOutput file:\n"
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()