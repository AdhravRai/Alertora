import json
import os

import numpy as np
import pandas as pd
from xgboost import XGBClassifier


FEATURE_FILE = "data/processed/ml_features_july2020.csv"
MODEL_FILE = "data/processed/xgboost_heavy_rain_july2020.json"
OUTPUT_FILE = "data/processed/prediction_grid.json"

# Historical replay timestamp.
# This must be inside the held-out test period.
BASE_TIME = "2020-07-29 02:00:00"

THRESHOLD = 0.25
RAIN_THRESHOLD = 2.2812

FEATURE_COLUMNS = [
    "precipitation",
    "cloud_water",
    "surface_pressure",
    "relative_humidity",
    "temperature",
    "u_wind",
    "v_wind",
    "wind_speed",

    "temperature_lag1",
    "temperature_lag3",
    "relative_humidity_lag1",
    "relative_humidity_lag3",
    "surface_pressure_lag1",
    "surface_pressure_lag3",
    "u_wind_lag1",
    "u_wind_lag3",
    "v_wind_lag1",
    "v_wind_lag3",
    "cloud_water_lag1",
    "cloud_water_lag3",
    "precipitation_lag1",
    "precipitation_lag3",
    "wind_speed_lag1",
    "wind_speed_lag3",

    "precipitation_change",
    "cloud_water_change",
    "humidity_change",
    "temperature_change",
    "wind_speed_change"
]


def main():

    print("Loading feature dataset...")

    df = pd.read_csv(
        FEATURE_FILE,
        parse_dates=["time"]
    )

    base_time = pd.Timestamp(BASE_TIME)

    current = df[
        df["time"] == base_time
    ].copy()

    if current.empty:
        raise ValueError(
            f"No data found for BASE_TIME={BASE_TIME}"
        )

    print(
        f"Grid cells found: {len(current)}"
    )

    # Check expected 17 x 17 grid
    unique_lat = np.sort(current["lat"].unique())
    unique_lon = np.sort(current["lon"].unique())

    expected_cells = len(unique_lat) * len(unique_lon)

    if len(current) != expected_cells:
        raise ValueError(
            f"Incomplete grid: "
            f"{len(current)} rows found, "
            f"expected {expected_cells}"
        )

    print(
        f"Grid: {len(unique_lat)} x {len(unique_lon)}"
    )

    # Load model
    print("Loading XGBoost model...")

    model = XGBClassifier()
    model.load_model(MODEL_FILE)

    # Generate probabilities
    probabilities = model.predict_proba(
        current[FEATURE_COLUMNS]
    )[:, 1]

    current["probability"] = probabilities

    current["predicted_event"] = (
        current["probability"] >= THRESHOLD
    ).astype(int)

    # Sort spatially
    current = current.sort_values(
        ["lat", "lon"]
    )

    probability_grid = current[
        "probability"
    ].to_numpy().reshape(
        len(unique_lat),
        len(unique_lon)
    )

    event_grid = current[
        "predicted_event"
    ].to_numpy().reshape(
        len(unique_lat),
        len(unique_lon)
    )

    # Next-hour actual precipitation is available because
    # this is a historical replay.
    actual_grid = current[
        "target_precipitation"
    ].to_numpy().reshape(
        len(unique_lat),
        len(unique_lon)
    )

    forecast_time = base_time + pd.Timedelta(hours=1)

    output = {
        "base_time": base_time.isoformat(),
        "forecast_time": forecast_time.isoformat(),
        "horizon_minutes": 60,

        "event": {
            "name": "high_rain",
            "threshold": RAIN_THRESHOLD,
            "threshold_unit": "kg/m2",
            "threshold_definition": (
                "95th percentile of training-period "
                "next-hour precipitation"
            )
        },

        "grid": {
            "latitudes": unique_lat.tolist(),
            "longitudes": unique_lon.tolist(),
            "probability": probability_grid.tolist(),
            "predicted_event": event_grid.tolist()
        },

        "historical_verification": {
            "available": True,
            "actual_precipitation": actual_grid.tolist()
        },

        "model": {
            "name": "XGBoost",
            "version": "july2020-v1",
            "operating_threshold": THRESHOLD
        },

        "source": {
            "dataset": "NCMRWF IMDAA",
            "resolution": "approximately 12 km",
            "frequency": "hourly"
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

    print("\nPrediction generated.")

    print(
        f"Base time: {base_time}"
    )

    print(
        f"Forecast time: {forecast_time}"
    )

    print(
        f"Probability min: "
        f"{probability_grid.min():.4f}"
    )

    print(
        f"Probability max: "
        f"{probability_grid.max():.4f}"
    )

    print(
        f"Probability mean: "
        f"{probability_grid.mean():.4f}"
    )

    print(
        f"Predicted high-rain cells: "
        f"{event_grid.sum()}"
    )

    print(
        f"Actual high-rain cells: "
        f"{(actual_grid >= RAIN_THRESHOLD).sum()}"
    )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()