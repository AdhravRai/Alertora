import json
import math
import os

ML_FILE = "data/processed/prediction_grid.json"
NOWCAST_FILE = "data/processed/nowcast_result_july29_0200.json"
OUTPUT_FILE = "data/processed/hazard_fusion_july29_0200.json"

STORM_WEIGHT = 0.30
ML_WEIGHT = 0.60
PRECIP_WEIGHT = 0.10

RISK_THRESHOLDS = {
    "LOW": 0.25,
    "MODERATE": 0.50,
    "HIGH": 0.75
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * radius * math.asin(math.sqrt(a))


def normalize_precipitation(value, minimum, maximum):
    if maximum <= minimum:
        return 0.0

    score = (value - minimum) / (maximum - minimum)
    return max(0.0, min(1.0, score))


def risk_level(score):
    if score >= RISK_THRESHOLDS["HIGH"]:
        return "VERY HIGH"
    if score >= RISK_THRESHOLDS["MODERATE"]:
        return "HIGH"
    if score >= RISK_THRESHOLDS["LOW"]:
        return "MODERATE"
    return "LOW"


def main():
    print("Loading ML prediction grid...")
    ml_data = load_json(ML_FILE)

    print("Loading spatial nowcast...")
    nowcast_data = load_json(NOWCAST_FILE)

    grid = ml_data["grid"]

    latitudes = grid["latitudes"]
    longitudes = grid["longitudes"]
    probabilities = grid["probability"]

    print(f"Grid: {len(latitudes)} x {len(longitudes)}")

    base_time = ml_data.get(
        "base_time",
        "2020-07-29T02:00:00"
    )

    forecast_time = ml_data.get(
        "forecast_time",
        "2020-07-29T03:00:00"
    )

    # ---------------------------------------------------------
    # Find the storm trajectory corresponding to +60 minutes
    # ---------------------------------------------------------

    storm_points = []

    for storm in nowcast_data.get("storms", []):
        track_id = storm.get("track_id")

        for point in storm.get("trajectory", []):
            if point.get("lead_minutes") == 60:
                if point.get("in_domain", False):
                    storm_points.append({
                        "track_id": track_id,
                        "latitude": point["latitude"],
                        "longitude": point["longitude"],
                        "lead_minutes": 60
                    })

    print(f"Storm positions at +60 min: {len(storm_points)}")

    # ---------------------------------------------------------
    # Precipitation information
    # ---------------------------------------------------------

    precip_summary = nowcast_data.get(
        "hazards", {}
    ).get(
        "precipitation_summary", {}
    )

    precip_min = precip_summary.get("minimum", 0.0)
    precip_max = precip_summary.get("maximum", 0.0)

    # ---------------------------------------------------------
    # Build fusion grid
    # ---------------------------------------------------------

    final_scores = []
    risk_levels = []

    ml_components = []
    storm_components = []
    precip_components = []

    all_scores = []

    for i, lat in enumerate(latitudes):

        score_row = []
        risk_row = []

        ml_row = []
        storm_row = []
        precip_row = []

        for j, lon in enumerate(longitudes):

            ml_probability = float(probabilities[i][j])

            # ---------------------------------------------
            # Storm proximity signal
            # ---------------------------------------------

            if storm_points:
                distances = []

                for storm in storm_points:
                    distance = haversine_km(
                        lat,
                        lon,
                        storm["latitude"],
                        storm["longitude"]
                    )
                    distances.append(distance)

                nearest_distance = min(distances)

                # 100 km -> 0
                # 0 km -> 1
                storm_signal = max(
                    0.0,
                    min(1.0, 1.0 - nearest_distance / 100.0)
                )

            else:
                nearest_distance = None
                storm_signal = 0.0

            # ---------------------------------------------
            # Precipitation signal
            # ---------------------------------------------

            actual_precip = None

            historical = ml_data.get(
                "historical_verification",
                {}
            )

            actual_grid = historical.get(
                "actual_precipitation"
            )

            if actual_grid:
                actual_precip = float(actual_grid[i][j])

            if actual_precip is not None:
                precip_signal = normalize_precipitation(
                    actual_precip,
                    precip_min,
                    precip_max
                )
            else:
                precip_signal = 0.0

            # ---------------------------------------------
            # Final fusion
            # ---------------------------------------------

            final_score = (
                ML_WEIGHT * ml_probability
                + STORM_WEIGHT * storm_signal
                + PRECIP_WEIGHT * precip_signal
            )

            final_score = max(
                0.0,
                min(1.0, final_score)
            )

            level = risk_level(final_score)

            score_row.append(round(final_score, 6))
            risk_row.append(level)

            ml_row.append(round(ml_probability, 6))
            storm_row.append(round(storm_signal, 6))
            precip_row.append(round(precip_signal, 6))

            all_scores.append(final_score)

        final_scores.append(score_row)
        risk_levels.append(risk_row)

        ml_components.append(ml_row)
        storm_components.append(storm_row)
        precip_components.append(precip_row)

    # ---------------------------------------------------------
    # Find maximum-risk cell
    # ---------------------------------------------------------

    max_score = -1.0
    max_i = 0
    max_j = 0

    for i in range(len(final_scores)):
        for j in range(len(final_scores[i])):
            if final_scores[i][j] > max_score:
                max_score = final_scores[i][j]
                max_i = i
                max_j = j

    max_cell = {
        "latitude": latitudes[max_i],
        "longitude": longitudes[max_j],
        "score": round(max_score, 6),
        "risk_level": risk_levels[max_i][max_j]
    }

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------

    output = {
        "base_time": base_time,
        "forecast_time": forecast_time,
        "grid_shape": [
            len(latitudes),
            len(longitudes)
        ],
        "latitude_range": [
            min(latitudes),
            max(latitudes)
        ],
        "longitude_range": [
            min(longitudes),
            max(longitudes)
        ],
        "weights": {
            "ml_probability": ML_WEIGHT,
            "storm_proximity": STORM_WEIGHT,
            "precipitation_signal": PRECIP_WEIGHT
        },
        "risk_thresholds": RISK_THRESHOLDS,
        "grid": {
            "latitudes": latitudes,
            "longitudes": longitudes,
            "final_score": final_scores,
            "risk_level": risk_levels
        },
        "components": {
            "ml_probability": ml_components,
            "storm_proximity": storm_components,
            "precipitation_signal": precip_components
        },
        "storm_context": {
            "lead_minutes": 60,
            "storms": storm_points
        },
        "maximum_risk_cell": max_cell,
        "metadata": {
            "ml_model": "XGBoost",
            "fusion_type": "deterministic weighted fusion",
            "precipitation_note": (
                "Precipitation component uses the historical "
                "verification grid for this historical demo."
            )
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

    print("\nFusion complete.")
    print(f"Base time: {base_time}")
    print(f"Forecast time: {forecast_time}")
    print(f"Storms at +60 min: {len(storm_points)}")
    print(f"Maximum risk: {max_score:.4f}")
    print(
        f"Maximum risk cell: "
        f"{max_cell['latitude']}, "
        f"{max_cell['longitude']}"
    )
    print(f"Risk level: {max_cell['risk_level']}")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()