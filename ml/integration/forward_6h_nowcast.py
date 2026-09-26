import json
import math
import os

import numpy as np


ML_FILE = "data/processed/ml_output_july29_0200.json"
STORM_FILE = "data/processed/nowcast_result_july29_0200.json"

OUTPUT_FILE = (
    "data/processed/forward_6h_nowcast_july29_0200.json"
)

ML_THRESHOLD = 0.25

# Spatial influence radius around the projected storm center.
# This is an integration parameter, not a learned meteorological constant.
INFLUENCE_RADIUS_KM = 100.0

HORIZONS_MINUTES = [
    60,
    120,
    180,
    240,
    300,
    360
]


def haversine_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    radius = 6371.0

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return (
        2
        * radius
        * math.asin(math.sqrt(a))
    )


def find_trajectory_point(
    trajectory,
    lead_minutes
):
    if not trajectory:
        return None

    exact = [
        point
        for point in trajectory
        if point["lead_minutes"] == lead_minutes
    ]

    if exact:
        return exact[0]

    # Linear interpolation if an exact lead is unavailable.
    points = sorted(
        trajectory,
        key=lambda x: x["lead_minutes"]
    )

    if lead_minutes < points[0]["lead_minutes"]:
        return None

    if lead_minutes > points[-1]["lead_minutes"]:
        return None

    for left, right in zip(
        points[:-1],
        points[1:]
    ):
        if (
            left["lead_minutes"]
            <= lead_minutes
            <= right["lead_minutes"]
        ):
            span = (
                right["lead_minutes"]
                - left["lead_minutes"]
            )

            ratio = (
                lead_minutes
                - left["lead_minutes"]
            ) / span

            latitude = (
                left["latitude"]
                + ratio
                * (
                    right["latitude"]
                    - left["latitude"]
                )
            )

            longitude = (
                left["longitude"]
                + ratio
                * (
                    right["longitude"]
                    - left["longitude"]
                )
            )

            return {
                "lead_minutes": lead_minutes,
                "latitude": latitude,
                "longitude": longitude,
                "in_domain": (
                    left["in_domain"]
                    and right["in_domain"]
                )
            }

    return None


def build_shifted_risk_grid(
    base_cells,
    storm_position,
    latitudes,
    longitudes
):
    """
    Move the ML risk field toward the projected storm position.

    This is a simple trajectory-based nowcasting layer.
    It is not a new trained ML model.
    """

    projected_lat = storm_position["latitude"]
    projected_lon = storm_position["longitude"]

    result = []

    for cell in base_cells:

        distance = haversine_km(
            cell["latitude"],
            cell["longitude"],
            projected_lat,
            projected_lon
        )

        if distance >= INFLUENCE_RADIUS_KM:
            proximity = 0.0
        else:
            proximity = (
                1.0
                - distance
                / INFLUENCE_RADIUS_KM
            )

        base_probability = cell["probability"]

        # Preserve the ML signal and add a bounded
        # trajectory influence.
        final_probability = (
            0.70 * base_probability
            + 0.30 * proximity
        )

        final_probability = min(
            1.0,
            max(
                0.0,
                final_probability
            )
        )

        result.append({
            "latitude": cell["latitude"],
            "longitude": cell["longitude"],
            "ml_probability": round(
                float(base_probability),
                6
            ),
            "storm_proximity": round(
                float(proximity),
                6
            ),
            "nowcast_probability": round(
                float(final_probability),
                6
            ),
            "predicted_high_rain": (
                final_probability
                >= ML_THRESHOLD
            )
        })

    return result


def main():
    print("Loading ML output...")

    with open(
        ML_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        ml_data = json.load(f)

    print("Loading storm trajectory...")

    with open(
        STORM_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        storm_data = json.load(f)

    if not storm_data["storms"]:
        raise ValueError(
            "No storm tracks available."
        )

    # ---------------------------------------------------------
    # Use the first valid storm track
    # ---------------------------------------------------------

    storm = storm_data["storms"][0]

    track_id = storm["track_id"]

    trajectory = storm["trajectory"]

    print(
        f"Using storm track: {track_id}"
    )

    print(
        f"Trajectory points: "
        f"{len(trajectory)}"
    )

    # ---------------------------------------------------------
    # ML base grid
    # ---------------------------------------------------------

    base_grid = ml_data["grid"]

    latitudes = base_grid["latitudes"]
    longitudes = base_grid["longitudes"]
    base_cells = base_grid["cells"]

    print(
        f"Base ML grid: "
        f"{len(latitudes)} x "
        f"{len(longitudes)}"
    )

    # ---------------------------------------------------------
    # Generate forward horizons
    # ---------------------------------------------------------

    horizons = []

    base_time = ml_data["forecast"]["base_time"]

    for lead_minutes in HORIZONS_MINUTES:

        trajectory_point = find_trajectory_point(
            trajectory,
            lead_minutes
        )

        if trajectory_point is None:
            print(
                f"Skipping +{lead_minutes} min: "
                "no trajectory point."
            )
            continue

        cells = build_shifted_risk_grid(
            base_cells,
            trajectory_point,
            latitudes,
            longitudes
        )

        probabilities = np.array([
            cell["nowcast_probability"]
            for cell in cells
        ])

        predicted_count = sum(
            cell["predicted_high_rain"]
            for cell in cells
        )

        horizons.append({
            "lead_minutes": lead_minutes,
            "lead_hours": lead_minutes / 60.0,
            "storm_position": {
                "latitude": round(
                    float(
                        trajectory_point[
                            "latitude"
                        ]
                    ),
                    6
                ),
                "longitude": round(
                    float(
                        trajectory_point[
                            "longitude"
                        ]
                    ),
                    6
                )
            },
            "grid": {
                "rows": len(latitudes),
                "columns": len(longitudes),
                "cells": cells
            },
            "summary": {
                "total_cells": len(cells),
                "predicted_high_rain_cells": (
                    int(predicted_count)
                ),
                "maximum_probability": round(
                    float(probabilities.max()),
                    6
                ),
                "mean_probability": round(
                    float(probabilities.mean()),
                    6
                )
            }
        })

        print(
            f"  +{lead_minutes // 60}h "
            f"storm={trajectory_point['latitude']:.4f},"
            f"{trajectory_point['longitude']:.4f} "
            f"| high-risk={predicted_count} "
            f"| max={probabilities.max():.4f}"
        )

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------

    output = {
        "product": (
            "ALERTORA_FORWARD_6H_NOWCAST"
        ),

        "version": "1.0",

        "base_time": base_time,

        "method": {
            "ml_component": (
                "XGBoost heavy-rain probability "
                "field"
            ),
            "spatial_component": (
                "trajectory-based storm "
                "displacement"
            ),
            "influence_radius_km": (
                INFLUENCE_RADIUS_KM
            ),
            "ml_weight": 0.70,
            "trajectory_weight": 0.30
        },

        "important_note": (
            "Forward horizons are generated by "
            "combining the available ML risk field "
            "with observed storm trajectory. "
            "This is a trajectory-based nowcast "
            "baseline, not an independently trained "
            "6-hour ML forecast."
        ),

        "storm_track": {
            "track_id": track_id,
            "current_position": storm[
                "current_position"
            ],
            "motion": storm["motion"]
        },

        "horizons": horizons,

        "source": {
            "ml": ML_FILE,
            "storm_nowcast": STORM_FILE
        }
    }

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            output,
            f,
            indent=2
        )

    print("\n" + "=" * 65)
    print("FORWARD 0–6H NOWCAST")
    print("=" * 65)

    print(
        f"Base time: {base_time}"
    )

    print(
        f"Storm track: {track_id}"
    )

    print(
        f"Horizons generated: "
        f"{len(horizons)}"
    )

    print(
        f"Method: "
        f"70% ML + 30% trajectory proximity"
    )

    print(
        f"\nSaved: {OUTPUT_FILE}"
    )

    print("=" * 65)


if __name__ == "__main__":
    main()