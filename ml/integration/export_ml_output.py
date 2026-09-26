import json
import os

import numpy as np


PREDICTION_FILE = "data/processed/prediction_grid.json"
EXPLANATION_FILE = "data/processed/explanation_july29_0200.json"

OUTPUT_FILE = "data/processed/ml_output_july29_0200.json"

ML_THRESHOLD = 0.25


def main():
    print("Loading prediction grid...")

    with open(
        PREDICTION_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        prediction = json.load(f)

    print("Loading XAI explanation...")

    with open(
        EXPLANATION_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        explanation = json.load(f)

    grid = prediction["grid"]

    latitudes = grid["latitudes"]
    longitudes = grid["longitudes"]
    probabilities = np.array(
        grid["probability"],
        dtype=float
    )

    predicted_event = (
        probabilities >= ML_THRESHOLD
    ).astype(int)

    # ---------------------------------------------------------
    # Build grid cells
    # ---------------------------------------------------------

    cells = []

    for i, latitude in enumerate(latitudes):
        for j, longitude in enumerate(longitudes):

            cells.append({
                "latitude": float(latitude),
                "longitude": float(longitude),
                "probability": round(
                    float(probabilities[i][j]),
                    6
                ),
                "predicted_high_rain": bool(
                    predicted_event[i][j]
                )
            })

    # ---------------------------------------------------------
    # XAI summary
    # ---------------------------------------------------------

    global_features = explanation.get(
        "global_top_features",
        []
    )

    explained_cells = explanation.get(
        "cell_explanations",
        []
    )

    # ---------------------------------------------------------
    # Historical verification
    # ---------------------------------------------------------

    historical_verification = prediction.get(
        "historical_verification"
    )

    # ---------------------------------------------------------
    # Final ML output
    # ---------------------------------------------------------

    output = {
        "product": "ALERTORA_ML_CONVECTIVE_RISK",
        "version": "1.0",

        "forecast": {
            "base_time": prediction["base_time"],
            "forecast_time": prediction["forecast_time"],
            "horizon_minutes": prediction[
                "horizon_minutes"
            ]
        },

        "grid": {
            "rows": len(latitudes),
            "columns": len(longitudes),
            "latitudes": latitudes,
            "longitudes": longitudes,
            "cells": cells
        },

        "model": {
            "name": prediction["model"]["name"],
            "version": prediction["model"].get(
                "version",
                "july2020-v1"
            ),
            "operating_threshold": ML_THRESHOLD
        },

        "summary": {
            "total_cells": len(cells),
            "predicted_high_rain_cells": int(
                predicted_event.sum()
            ),
            "minimum_probability": round(
                float(probabilities.min()),
                6
            ),
            "maximum_probability": round(
                float(probabilities.max()),
                6
            ),
            "mean_probability": round(
                float(probabilities.mean()),
                6
            )
        },

        "explainability": {
            "method": explanation[
                "explanation_method"
            ],
            "global_top_features": global_features,
            "cell_explanations": explained_cells
        },

        "historical_verification": {
            "available": (
                historical_verification is not None
            ),
            "note": (
                "Historical verification only. "
                "Not used as a future forecast input."
            )
        },

        "source": prediction["source"]
    }

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print("\n" + "=" * 60)
    print("ALERTORA ML OUTPUT")
    print("=" * 60)

    print(
        f"Base time: "
        f"{output['forecast']['base_time']}"
    )

    print(
        f"Forecast time: "
        f"{output['forecast']['forecast_time']}"
    )

    print(
        f"Grid: "
        f"{len(latitudes)} x {len(longitudes)}"
    )

    print(
        f"Total cells: "
        f"{output['summary']['total_cells']}"
    )

    print(
        f"High-risk cells: "
        f"{output['summary']['predicted_high_rain_cells']}"
    )

    print(
        f"Maximum probability: "
        f"{output['summary']['maximum_probability']}"
    )

    print(
        f"Mean probability: "
        f"{output['summary']['mean_probability']}"
    )

    print(
        "\nTop ML features:"
    )

    for feature in global_features[:5]:
        print(
            f"  {feature['feature']}: "
            f"{feature['mean_abs_shap']:.6f}"
        )

    print(
        f"\nSaved: {OUTPUT_FILE}"
    )

    print("=" * 60)


if __name__ == "__main__":
    main()