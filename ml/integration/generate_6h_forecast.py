import json
import os

import numpy as np
import pandas as pd
import xgboost as xgb


FEATURE_FILE = "data/processed/ml_features_july2020.csv"
MODEL_FILE = "data/processed/xgboost_heavy_rain_july2020.json"
OUTPUT_FILE = "data/processed/ml_forecast_6h_july29_0200.json"

BASE_TIME = "2020-07-29 02:00:00"

PROBABILITY_THRESHOLD = 0.25

HORIZONS = [1, 2, 3, 4, 5, 6]


def main():
    print("Loading feature dataset...")

    df = pd.read_csv(
        FEATURE_FILE,
        parse_dates=["time"]
    )

    print("Loading XGBoost model...")

    model = xgb.XGBClassifier()
    model.load_model(MODEL_FILE)

    # ---------------------------------------------------------
    # Feature columns
    # ---------------------------------------------------------

    excluded_columns = [
        "time",
        "lon",
        "lat",
        "target_precipitation"
    ]

    feature_columns = [
        column
        for column in df.columns
        if column not in excluded_columns
    ]

    # ---------------------------------------------------------
    # Forecast timestamps
    # ---------------------------------------------------------

    base_time = pd.Timestamp(BASE_TIME)

    forecast_outputs = []

    print(
        f"Generating 0–6 hour forecast "
        f"from {BASE_TIME}..."
    )

    for horizon in HORIZONS:

        forecast_time = (
            base_time
            + pd.Timedelta(hours=horizon)
        )

        frame = df[
            df["time"] == forecast_time
        ].copy()

        if frame.empty:
            print(
                f"WARNING: No feature frame "
                f"for {forecast_time}"
            )
            continue

        X = frame[feature_columns]

        probabilities = model.predict_proba(
            X
        )[:, 1]

        predicted_high_rain = (
            probabilities
            >= PROBABILITY_THRESHOLD
        )

        cells = []

        for index, row in frame.iterrows():

            cells.append({
                "latitude": float(row["lat"]),
                "longitude": float(row["lon"]),
                "probability": round(
                    float(probabilities[
                        frame.index.get_loc(index)
                    ]),
                    6
                ),
                "predicted_high_rain": bool(
                    predicted_high_rain[
                        frame.index.get_loc(index)
                    ]
                )
            })

        forecast_outputs.append({
            "horizon_hours": horizon,
            "forecast_time": forecast_time.isoformat(),
            "grid": {
                "rows": 17,
                "columns": 17,
                "cells": cells
            },
            "summary": {
                "total_cells": len(cells),
                "predicted_high_rain_cells": int(
                    predicted_high_rain.sum()
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
            f"  +{horizon}h "
            f"{forecast_time}: "
            f"{len(cells)} cells, "
            f"high-risk={predicted_high_rain.sum()}, "
            f"max={probabilities.max():.4f}"
        )

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------

    output = {
        "product": "ALERTORA_ML_6H_FORECAST",
        "version": "1.0",

        "base_time": base_time.isoformat(),

        "forecast_method": (
            "Existing next-hour XGBoost model "
            "evaluated on successive hourly "
            "IMDAA feature frames."
        ),

        "method_note": (
            "This is a multi-hour baseline, "
            "not six independently trained "
            "forecast models."
        ),

        "model": {
            "name": "XGBoost",
            "operating_threshold": (
                PROBABILITY_THRESHOLD
            )
        },

        "horizons": forecast_outputs,

        "source": {
            "dataset": "NCMRWF IMDAA",
            "resolution": "approximately 12 km",
            "temporal_resolution": "hourly"
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

    print("\n" + "=" * 60)
    print("6-HOUR ML FORECAST")
    print("=" * 60)

    print(
        f"Base time: {base_time.isoformat()}"
    )

    print(
        f"Horizons generated: "
        f"{len(forecast_outputs)}"
    )

    for item in forecast_outputs:
        print(
            f"  +{item['horizon_hours']}h -> "
            f"{item['forecast_time']} | "
            f"high-risk cells: "
            f"{item['summary']['predicted_high_rain_cells']} | "
            f"max probability: "
            f"{item['summary']['maximum_probability']:.4f}"
        )

    print(
        f"\nSaved: {OUTPUT_FILE}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()