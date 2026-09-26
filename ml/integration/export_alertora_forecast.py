import json
import os


ML_FILE = "data/processed/ml_output_july29_0200.json"
FORWARD_FILE = (
    "data/processed/forward_6h_nowcast_july29_0200.json"
)
EXPLANATION_FILE = (
    "data/processed/explanation_july29_0200.json"
)

OUTPUT_FILE = (
    "data/processed/alertora_forecast_july29_0200.json"
)


def main():
    print("Loading ML output...")

    with open(
        ML_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        ml_data = json.load(f)

    print("Loading forward nowcast...")

    with open(
        FORWARD_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        forward_data = json.load(f)

    print("Loading XAI output...")

    with open(
        EXPLANATION_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        explanation_data = json.load(f)

    # ---------------------------------------------------------
    # Extract forecast horizons
    # ---------------------------------------------------------

    horizons = []

    for horizon in forward_data["horizons"]:

        horizons.append({
            "lead_hours": horizon["lead_hours"],
            "lead_minutes": horizon["lead_minutes"],

            "storm_position": (
                horizon["storm_position"]
            ),

            "summary": horizon["summary"],

            "grid": horizon["grid"]
        })

    # ---------------------------------------------------------
    # Build final Alertora contract
    # ---------------------------------------------------------

    output = {
        "product": "ALERTORA_FORECAST",

        "version": "1.0",

        "forecast": {
            "base_time": forward_data[
                "base_time"
            ],

            "horizon_hours": 6,

            "source": {
                "dataset": "NCMRWF IMDAA",
                "resolution": (
                    "approximately 12 km"
                ),
                "temporal_resolution": "hourly"
            }
        },

        "method": forward_data["method"],

        "method_note": forward_data[
            "important_note"
        ],

        "storm": {
            "track_id": forward_data[
                "storm_track"
            ]["track_id"],

            "current_position": forward_data[
                "storm_track"
            ]["current_position"],

            "motion": forward_data[
                "storm_track"
            ]["motion"]
        },

        "horizons": horizons,

        "explainability": {
            "method": explanation_data[
                "explanation_method"
            ],

            "global_top_features": (
                explanation_data[
                    "global_top_features"
                ]
            ),

            "cell_explanations": (
                explanation_data[
                    "cell_explanations"
                ]
            )
        },

        "historical_verification": (
            ml_data[
                "historical_verification"
            ]
        )
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

    print("\n" + "=" * 65)
    print("ALERTORA FORECAST HANDOFF")
    print("=" * 65)

    print(
        f"Base time: "
        f"{output['forecast']['base_time']}"
    )

    print(
        f"Horizons: "
        f"{len(horizons)}"
    )

    print(
        f"Storm track: "
        f"{output['storm']['track_id']}"
    )

    print(
        "\nForecast summary:"
    )

    for horizon in horizons:
        summary = horizon["summary"]

        print(
            f"  +{horizon['lead_hours']:.0f}h | "
            f"high-risk cells: "
            f"{summary['predicted_high_rain_cells']} | "
            f"max: "
            f"{summary['maximum_probability']:.4f}"
        )

    print(
        "\nXAI features:"
    )

    for feature in output[
        "explainability"
    ]["global_top_features"][:5]:

        print(
            f"  {feature['feature']}: "
            f"{feature['mean_abs_shap']:.6f}"
        )

    print(
        f"\nSaved: {OUTPUT_FILE}"
    )

    print("=" * 65)


if __name__ == "__main__":
    main()