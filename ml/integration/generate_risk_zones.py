import json
import math
import os


INPUT_FILE = (
    "data/processed/alertora_forecast_july29_0200.json"
)

OUTPUT_FILE = (
    "data/processed/risk_zones_july29_0200.json"
)

# Threshold used only for geographic zone generation.
# This does NOT change the ML model threshold.
RISK_THRESHOLD = 0.50

# Ignore isolated 1–2 cell regions.
MIN_ZONE_CELLS = 3


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


def risk_level(probability):
    if probability >= 0.75:
        return "VERY HIGH"

    if probability >= 0.50:
        return "HIGH"

    if probability >= 0.25:
        return "MODERATE"

    return "LOW"


def get_neighbors(
    row,
    col,
    rows,
    cols
):
    """
    Return 8-connected neighboring cells.

    Cells touching horizontally, vertically,
    or diagonally are considered connected.
    """

    neighbors = []

    for row_offset in (-1, 0, 1):
        for col_offset in (-1, 0, 1):

            if (
                row_offset == 0
                and col_offset == 0
            ):
                continue

            new_row = (
                row
                + row_offset
            )

            new_col = (
                col
                + col_offset
            )

            if (
                0 <= new_row < rows
                and 0 <= new_col < cols
            ):
                neighbors.append(
                    (new_row, new_col)
                )

    return neighbors


def find_zones(
    cells,
    rows,
    cols
):
    """
    Find connected geographic regions
    whose nowcast probability is >=
    RISK_THRESHOLD.
    """

    high_risk = set()

    for index, cell in enumerate(cells):

        probability = float(
            cell["nowcast_probability"]
        )

        if probability >= RISK_THRESHOLD:

            row = index // cols
            col = index % cols

            high_risk.add(
                (row, col)
            )

    visited = set()
    components = []

    for start in sorted(high_risk):

        if start in visited:
            continue

        queue = [start]
        visited.add(start)

        component = []

        while queue:

            current = queue.pop()

            component.append(
                current
            )

            row, col = current

            for neighbor in get_neighbors(
                row,
                col,
                rows,
                cols
            ):

                if (
                    neighbor in high_risk
                    and neighbor not in visited
                ):
                    visited.add(neighbor)
                    queue.append(
                        neighbor
                    )

        components.append(
            component
        )

    return components


def build_zone(
    zone_number,
    component,
    cells,
    rows,
    cols,
    storm_position,
    lead_hours
):
    """
    Convert a connected component into
    a geographic risk-zone object.
    """

    zone_cells = []

    for row, col in component:

        index = (
            row * cols
            + col
        )

        zone_cells.append(
            cells[index]
        )

    probabilities = [
        float(
            cell["nowcast_probability"]
        )
        for cell in zone_cells
    ]

    latitudes = [
        float(
            cell["latitude"]
        )
        for cell in zone_cells
    ]

    longitudes = [
        float(
            cell["longitude"]
        )
        for cell in zone_cells
    ]

    peak_probability = max(
        probabilities
    )

    mean_probability = (
        sum(probabilities)
        / len(probabilities)
    )

    center_latitude = (
        sum(latitudes)
        / len(latitudes)
    )

    center_longitude = (
        sum(longitudes)
        / len(longitudes)
    )

    min_latitude = min(latitudes)
    max_latitude = max(latitudes)

    min_longitude = min(longitudes)
    max_longitude = max(longitudes)

    storm_distance = haversine_km(
        center_latitude,
        center_longitude,
        storm_position["latitude"],
        storm_position["longitude"]
    )

    return {
        "zone_id": (
            f"HZ-{zone_number:02d}"
        ),

        "horizon_hours": lead_hours,

        "risk_level": risk_level(
            peak_probability
        ),

        "affected_cells": len(
            zone_cells
        ),

        "peak_probability": round(
            peak_probability,
            6
        ),

        "mean_probability": round(
            mean_probability,
            6
        ),

        "center": {
            "latitude": round(
                center_latitude,
                6
            ),
            "longitude": round(
                center_longitude,
                6
            )
        },

        "bounding_box": {
            "min_latitude": round(
                min_latitude,
                6
            ),
            "max_latitude": round(
                max_latitude,
                6
            ),
            "min_longitude": round(
                min_longitude,
                6
            ),
            "max_longitude": round(
                max_longitude,
                6
            )
        },

        "storm_relation": {
            "distance_km": round(
                storm_distance,
                2
            ),

            "projected_storm_position": {
                "latitude": round(
                    float(
                        storm_position[
                            "latitude"
                        ]
                    ),
                    6
                ),

                "longitude": round(
                    float(
                        storm_position[
                            "longitude"
                        ]
                    ),
                    6
                )
            }
        }
    }


def main():

    print(
        "Loading Alertora forecast..."
    )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    all_horizon_zones = []

    for horizon in data["horizons"]:

        lead_hours = int(
            horizon["lead_hours"]
        )

        grid = horizon["grid"]

        rows = int(
            grid["rows"]
        )

        cols = int(
            grid["columns"]
        )

        cells = grid["cells"]

        expected_cells = (
            rows * cols
        )

        if len(cells) != expected_cells:
            raise ValueError(
                f"Invalid grid at "
                f"+{lead_hours}h: "
                f"{len(cells)} cells, "
                f"expected "
                f"{expected_cells}."
            )

        components = find_zones(
            cells,
            rows,
            cols
        )

        storm_position = (
            horizon["storm_position"]
        )

        zones = []

        for component in components:

            # Remove isolated 1–2 cell regions.
            if len(component) < MIN_ZONE_CELLS:
                continue

            zone = build_zone(
                zone_number=(
                    len(zones) + 1
                ),
                component=component,
                cells=cells,
                rows=rows,
                cols=cols,
                storm_position=(
                    storm_position
                ),
                lead_hours=lead_hours
            )

            zones.append(
                zone
            )

        # Highest-risk zones first.
        zones.sort(
            key=lambda zone:
                zone[
                    "peak_probability"
                ],
            reverse=True
        )

        # Re-number after sorting.
        for index, zone in enumerate(
            zones,
            start=1
        ):
            zone["zone_id"] = (
                f"HZ-{index:02d}"
            )

        all_horizon_zones.append({
            "lead_hours": lead_hours,

            "storm_position": {
                "latitude": round(
                    float(
                        storm_position[
                            "latitude"
                        ]
                    ),
                    6
                ),

                "longitude": round(
                    float(
                        storm_position[
                            "longitude"
                        ]
                    ),
                    6
                )
            },

            "zone_count": len(zones),

            "zones": zones
        })

        print(
            f"+{lead_hours}h: "
            f"{len(zones)} risk zones"
        )

    output = {
        "product": (
            "ALERTORA_RISK_ZONES"
        ),

        "version": "1.0",

        "base_time": (
            data[
                "forecast"
            ][
                "base_time"
            ]
        ),

        "source": {
            "forecast_file": INPUT_FILE,

            "grid": "17 x 17",

            "risk_threshold": (
                RISK_THRESHOLD
            ),

            "minimum_zone_cells": (
                MIN_ZONE_CELLS
            ),

            "grouping": (
                "8-connected "
                "high-risk cells"
            )
        },

        "horizons": (
            all_horizon_zones
        )
    }

    os.makedirs(
        os.path.dirname(
            OUTPUT_FILE
        ),
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

    print("\n" + "=" * 60)
    print(
        "ALERTORA RISK ZONE GENERATOR"
    )
    print("=" * 60)

    print(
        f"Base time: "
        f"{output['base_time']}"
    )

    print(
        f"Spatial threshold: "
        f"{RISK_THRESHOLD}"
    )

    print(
        f"Minimum zone size: "
        f"{MIN_ZONE_CELLS} cells"
    )

    print(
        f"Horizons: "
        f"{len(all_horizon_zones)}"
    )

    print(
        f"Saved: "
        f"{OUTPUT_FILE}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()