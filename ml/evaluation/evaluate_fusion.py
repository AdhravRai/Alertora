import json
import os

import numpy as np
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix
)


PREDICTION_FILE = "data/processed/prediction_grid.json"
FUSION_FILE = "data/processed/hazard_fusion_july29_0200.json"
OUTPUT_FILE = "data/processed/fusion_evaluation_july29_0200.json"

RAIN_THRESHOLD = 2.2812
FUSION_THRESHOLD = 0.50


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def flatten_grid(grid):
    return np.array(grid, dtype=float).flatten()


def evaluate_binary_predictions(y_true, y_pred):
    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred)

    return {
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "confusion_matrix": cm.tolist()
    }


def main():
    print("Loading prediction grid...")
    prediction_data = load_json(PREDICTION_FILE)

    print("Loading fusion result...")
    fusion_data = load_json(FUSION_FILE)

    # ---------------------------------------------------------
    # ML probability
    # ---------------------------------------------------------

    ml_probability = flatten_grid(
        prediction_data["grid"]["probability"]
    )

    # ---------------------------------------------------------
    # Actual precipitation
    # ---------------------------------------------------------

    actual_precipitation = flatten_grid(
        prediction_data[
            "historical_verification"
        ]["actual_precipitation"]
    )

    actual_event = (
        actual_precipitation >= RAIN_THRESHOLD
    ).astype(int)

    # ---------------------------------------------------------
    # ML prediction using operating threshold
    # ---------------------------------------------------------

    model_threshold = prediction_data[
        "model"
    ]["operating_threshold"]

    ml_prediction = (
        ml_probability >= model_threshold
    ).astype(int)

    # ---------------------------------------------------------
    # Fused prediction
    # ---------------------------------------------------------

    fusion_scores = flatten_grid(
        fusion_data["grid"]["final_score"]
    )

    fusion_prediction = (
        fusion_scores >= FUSION_THRESHOLD
    ).astype(int)

    # ---------------------------------------------------------
    # Evaluate ML model
    # ---------------------------------------------------------

    print("\nEvaluating XGBoost...")

    ml_metrics = evaluate_binary_predictions(
        actual_event,
        ml_prediction
    )

    try:
        ml_auc = roc_auc_score(
            actual_event,
            ml_probability
        )
    except ValueError:
        ml_auc = None

    if ml_auc is not None:
        ml_metrics["roc_auc"] = round(
            float(ml_auc),
            4
        )

    # ---------------------------------------------------------
    # Evaluate fused system
    # ---------------------------------------------------------

    print("Evaluating fused system...")

    fusion_metrics = evaluate_binary_predictions(
        actual_event,
        fusion_prediction
    )

    try:
        fusion_auc = roc_auc_score(
            actual_event,
            fusion_scores
        )
    except ValueError:
        fusion_auc = None

    if fusion_auc is not None:
        fusion_metrics["roc_auc"] = round(
            float(fusion_auc),
            4
        )

    # ---------------------------------------------------------
    # Cell counts
    # ---------------------------------------------------------

    actual_high_rain_cells = int(
        actual_event.sum()
    )

    ml_predicted_cells = int(
        ml_prediction.sum()
    )

    fusion_predicted_cells = int(
        fusion_prediction.sum()
    )

    # ---------------------------------------------------------
    # Spatial overlap
    # ---------------------------------------------------------

    true_positive_ml = int(
        np.sum(
            (ml_prediction == 1)
            & (actual_event == 1)
        )
    )

    true_positive_fusion = int(
        np.sum(
            (fusion_prediction == 1)
            & (actual_event == 1)
        )
    )

    # ---------------------------------------------------------
    # Maximum risk information
    # ---------------------------------------------------------

    maximum_risk = fusion_data[
        "maximum_risk_cell"
    ]

    # ---------------------------------------------------------
    # Output
    # ---------------------------------------------------------

    result = {
        "event": {
            "base_time": prediction_data["base_time"],
            "forecast_time": prediction_data["forecast_time"],
            "rain_threshold_kg_m2": RAIN_THRESHOLD
        },
        "cell_counts": {
            "total_cells": int(len(actual_event)),
            "actual_high_rain": actual_high_rain_cells,
            "ml_predicted_high_risk": ml_predicted_cells,
            "fusion_predicted_high_risk": fusion_predicted_cells
        },
        "xgboost_metrics": ml_metrics,
        "fusion_metrics": fusion_metrics,
        "spatial_overlap": {
            "xgboost_true_positive_cells": true_positive_ml,
            "fusion_true_positive_cells": true_positive_fusion
        },
        "fusion_threshold": FUSION_THRESHOLD,
        "maximum_risk_cell": maximum_risk
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
            result,
            f,
            indent=2
        )

    # ---------------------------------------------------------
    # Terminal summary
    # ---------------------------------------------------------

    print("\n" + "=" * 55)
    print("HISTORICAL FUSION EVALUATION")
    print("=" * 55)

    print(
        f"Forecast: "
        f"{prediction_data['base_time']} "
        f"-> "
        f"{prediction_data['forecast_time']}"
    )

    print(
        f"\nActual high-rain cells: "
        f"{actual_high_rain_cells}"
    )

    print(
        f"\nXGBoost predicted cells: "
        f"{ml_predicted_cells}"
    )

    print(
        f"XGBoost precision: "
        f"{ml_metrics['precision']}"
    )

    print(
        f"XGBoost recall: "
        f"{ml_metrics['recall']}"
    )

    print(
        f"XGBoost F1: "
        f"{ml_metrics['f1']}"
    )

    if "roc_auc" in ml_metrics:
        print(
            f"XGBoost ROC-AUC: "
            f"{ml_metrics['roc_auc']}"
        )

    print(
        f"\nFusion predicted cells: "
        f"{fusion_predicted_cells}"
    )

    print(
        f"Fusion precision: "
        f"{fusion_metrics['precision']}"
    )

    print(
        f"Fusion recall: "
        f"{fusion_metrics['recall']}"
    )

    print(
        f"Fusion F1: "
        f"{fusion_metrics['f1']}"
    )

    if "roc_auc" in fusion_metrics:
        print(
            f"Fusion ROC-AUC: "
            f"{fusion_metrics['roc_auc']}"
        )

    print(
        f"\nXGBoost true-positive cells: "
        f"{true_positive_ml}"
    )

    print(
        f"Fusion true-positive cells: "
        f"{true_positive_fusion}"
    )

    print(
        f"\nMaximum fused risk: "
        f"{maximum_risk['score']}"
    )

    print(
        f"Maximum risk location: "
        f"{maximum_risk['latitude']}, "
        f"{maximum_risk['longitude']}"
    )

    print(
        f"Risk level: "
        f"{maximum_risk['risk_level']}"
    )

    print("\nSaved:")
    print(OUTPUT_FILE)
    print("=" * 55)


if __name__ == "__main__":
    main()