import json
import os

import numpy as np
import pandas as pd
import shap
import xgboost as xgb


FEATURE_FILE = "data/processed/ml_features_july2020.csv"
MODEL_FILE = "data/processed/xgboost_heavy_rain_july2020.json"
PREDICTION_FILE = "data/processed/prediction_grid.json"
OUTPUT_FILE = "data/processed/explanation_july29_0200.json"

BASE_TIME = "2020-07-29 02:00:00"

TOP_CELLS = 10
TOP_FEATURES = 10
BACKGROUND_SAMPLES = 100


def load_prediction_grid():
    with open(PREDICTION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("Loading feature dataset...")

    df = pd.read_csv(
        FEATURE_FILE,
        parse_dates=["time"]
    )

    print("Loading XGBoost model...")

    model = xgb.XGBClassifier()
    model.load_model(MODEL_FILE)

    prediction_data = load_prediction_grid()

    grid = prediction_data["grid"]

    latitudes = grid["latitudes"]
    longitudes = grid["longitudes"]

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
    # Get the 02:00 forecast rows
    # ---------------------------------------------------------

    base_time = pd.Timestamp(BASE_TIME)

    forecast_df = df[
        df["time"] == base_time
    ].copy()

    if forecast_df.empty:
        raise ValueError(
            f"No feature rows found for {BASE_TIME}"
        )

    print(
        f"Forecast rows found: "
        f"{len(forecast_df)}"
    )

    # ---------------------------------------------------------
    # Match grid cells with feature rows
    # ---------------------------------------------------------

    forecast_df["grid_i"] = forecast_df["lat"].apply(
        lambda x: int(
            np.argmin(
                np.abs(
                    np.array(latitudes) - x
                )
            )
        )
    )

    forecast_df["grid_j"] = forecast_df["lon"].apply(
        lambda x: int(
            np.argmin(
                np.abs(
                    np.array(longitudes) - x
                )
            )
        )
    )

    # ---------------------------------------------------------
    # Model predictions
    # ---------------------------------------------------------

    X = forecast_df[feature_columns]

    probabilities_from_model = model.predict_proba(
        X
    )[:, 1]

    forecast_df["model_probability"] = (
        probabilities_from_model
    )

    # ---------------------------------------------------------
    # Select highest-risk cells
    # ---------------------------------------------------------

    selected = forecast_df.sort_values(
        "model_probability",
        ascending=False
    ).head(TOP_CELLS)

    selected_indices = selected.index.tolist()

    X_selected = forecast_df.loc[
        selected_indices,
        feature_columns
    ]

    print(
        f"Explaining top {len(X_selected)} "
        "forecast cells..."
    )

    # ---------------------------------------------------------
    # Model-agnostic SHAP
    # ---------------------------------------------------------

    print(
        "Creating model-agnostic SHAP explainer..."
    )

    background = shap.sample(
        df[feature_columns],
        min(
            BACKGROUND_SAMPLES,
            len(df)
        ),
        random_state=42
    )

    def predict_positive_class(data):
        data = pd.DataFrame(
            data,
            columns=feature_columns
        )

        return model.predict_proba(
            data
        )[:, 1]

    explainer = shap.Explainer(
        predict_positive_class,
        background,
        algorithm="permutation"
    )

    print("Calculating SHAP values...")

    max_evals = (
        2 * len(feature_columns) + 1
    )

    explanation = explainer(
        X_selected,
        max_evals=max_evals
    )

    shap_values = np.asarray(
        explanation.values
    )

    # ---------------------------------------------------------
    # Make sure SHAP output has expected shape
    # ---------------------------------------------------------

    if shap_values.ndim != 2:
        raise ValueError(
            "Unexpected SHAP output shape: "
            f"{shap_values.shape}"
        )

    if shap_values.shape[1] != len(
        feature_columns
    ):
        raise ValueError(
            "SHAP feature count does not match "
            f"model feature count: "
            f"{shap_values.shape[1]} vs "
            f"{len(feature_columns)}"
        )

    # ---------------------------------------------------------
    # Global feature importance
    # ---------------------------------------------------------

    mean_abs_shap = np.mean(
        np.abs(shap_values),
        axis=0
    )

    feature_importance = []

    for feature, importance in zip(
        feature_columns,
        mean_abs_shap
    ):
        feature_importance.append({
            "feature": feature,
            "mean_abs_shap": round(
                float(importance),
                6
            )
        })

    feature_importance.sort(
        key=lambda x: x["mean_abs_shap"],
        reverse=True
    )

    top_features = feature_importance[
        :TOP_FEATURES
    ]

    # ---------------------------------------------------------
    # Per-cell explanations
    # ---------------------------------------------------------

    cell_explanations = []

    for row_number, (index, row) in enumerate(
        selected.iterrows()
    ):

        shap_row = shap_values[row_number]

        contributions = []

        for feature, value, contribution in zip(
            feature_columns,
            X_selected.loc[index].values,
            shap_row
        ):
            contributions.append({
                "feature": feature,
                "value": float(value),
                "shap_value": round(
                    float(contribution),
                    6
                )
            })

        contributions.sort(
            key=lambda x: abs(x["shap_value"]),
            reverse=True
        )

        positive = [
            item
            for item in contributions
            if item["shap_value"] > 0
        ][:5]

        negative = [
            item
            for item in contributions
            if item["shap_value"] < 0
        ][:5]

        cell_explanations.append({
            "latitude": float(row["lat"]),
            "longitude": float(row["lon"]),
            "model_probability": round(
                float(row["model_probability"]),
                6
            ),
            "top_positive_features": positive,
            "top_negative_features": negative
        })

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------

    output = {
        "base_time": BASE_TIME,
        "forecast_time": prediction_data[
            "forecast_time"
        ],
        "model": {
            "name": "XGBoost",
            "version": prediction_data[
                "model"
            ].get(
                "version",
                "july2020-v1"
            )
        },
        "explanation_method": (
            "SHAP PermutationExplainer"
        ),
        "explained_cells": len(
            cell_explanations
        ),
        "global_top_features": top_features,
        "cell_explanations": cell_explanations
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

    # ---------------------------------------------------------
    # Terminal summary
    # ---------------------------------------------------------

    print("\n" + "=" * 55)
    print("XGBOOST EXPLANATION")
    print("=" * 55)

    print(
        f"Base time: {BASE_TIME}"
    )

    print(
        f"Cells explained: "
        f"{len(cell_explanations)}"
    )

    print("\nTop features:")

    for item in top_features:
        print(
            f"  {item['feature']}: "
            f"{item['mean_abs_shap']:.6f}"
        )

    print("\nHighest-risk explained cells:")

    for cell in cell_explanations[:5]:
        print(
            f"  "
            f"{cell['latitude']:.4f}, "
            f"{cell['longitude']:.4f} "
            f"-> "
            f"{cell['model_probability']:.4f}"
        )

    print(
        f"\nSaved: {OUTPUT_FILE}"
    )

    print("=" * 55)


if __name__ == "__main__":
    main()