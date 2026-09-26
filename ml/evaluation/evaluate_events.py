import json
import os

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)


FEATURE_FILE = "data/processed/ml_features_july2020.csv"
MODEL_FILE = "data/processed/xgboost_heavy_rain_july2020.json"
OUTPUT_FILE = "data/processed/event_evaluation_july2020.json"

TRAIN_END = "2020-07-21 23:00:00"
TEST_START = "2020-07-27 00:00:00"
TEST_END = "2020-07-31 22:00:00"

RAIN_THRESHOLD = 2.2812
PROBABILITY_THRESHOLD = 0.25

MIN_ACTUAL_POSITIVES = 10
MAX_EVENTS = 10


def main():
    print("Loading feature dataset...")

    df = pd.read_csv(
        FEATURE_FILE,
        parse_dates=["time"]
    )

    print("Loading XGBoost model...")

    model = xgb.XGBClassifier()
    model.load_model(MODEL_FILE)

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
    # Test period
    # ---------------------------------------------------------

    test_df = df[
        (df["time"] >= pd.Timestamp(TEST_START))
        & (df["time"] <= pd.Timestamp(TEST_END))
    ].copy()

    if test_df.empty:
        raise ValueError(
            "No rows found in test period."
        )

    print(
        f"Test rows: {len(test_df)}"
    )

    # ---------------------------------------------------------
    # Model predictions
    # ---------------------------------------------------------

    X_test = test_df[feature_columns]

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    test_df["probability"] = probabilities

    test_df["predicted_high_rain"] = (
        probabilities >= PROBABILITY_THRESHOLD
    )

    test_df["actual_high_rain"] = (
        test_df["target_precipitation"]
        >= RAIN_THRESHOLD
    )

    # ---------------------------------------------------------
    # Overall test metrics
    # ---------------------------------------------------------

    y_true = test_df["actual_high_rain"].astype(int)
    y_pred = test_df["predicted_high_rain"].astype(int)

    overall_auc = roc_auc_score(
        y_true,
        probabilities
    )

    overall_precision = precision_score(
        y_true,
        y_pred,
        zero_division=0
    )

    overall_recall = recall_score(
        y_true,
        y_pred,
        zero_division=0
    )

    overall_f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0
    )

    # ---------------------------------------------------------
    # Find event timestamps
    # ---------------------------------------------------------

    event_counts = (
        test_df
        .groupby("time")["actual_high_rain"]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    candidate_events = event_counts[
        event_counts >= MIN_ACTUAL_POSITIVES
    ].head(MAX_EVENTS)

    print(
        f"Candidate events: "
        f"{len(candidate_events)}"
    )

    # ---------------------------------------------------------
    # Event-wise evaluation
    # ---------------------------------------------------------

    events = []

    for timestamp, actual_count in candidate_events.items():

        event_df = test_df[
            test_df["time"] == timestamp
        ]

        actual = event_df[
            "actual_high_rain"
        ].astype(int)

        predicted = event_df[
            "predicted_high_rain"
        ].astype(int)

        event_probabilities = event_df[
            "probability"
        ]

        precision = precision_score(
            actual,
            predicted,
            zero_division=0
        )

        recall = recall_score(
            actual,
            predicted,
            zero_division=0
        )

        f1 = f1_score(
            actual,
            predicted,
            zero_division=0
        )

        if actual.nunique() == 2:
            auc = roc_auc_score(
                actual,
                event_probabilities
            )
        else:
            auc = None

        events.append({
            "forecast_time": (
                timestamp.isoformat()
            ),
            "actual_high_rain_cells": int(
                actual.sum()
            ),
            "predicted_high_rain_cells": int(
                predicted.sum()
            ),
            "precision": round(
                float(precision),
                4
            ),
            "recall": round(
                float(recall),
                4
            ),
            "f1": round(
                float(f1),
                4
            ),
            "roc_auc": (
                round(float(auc), 4)
                if auc is not None
                else None
            ),
            "maximum_probability": round(
                float(event_probabilities.max()),
                4
            )
        })

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    output = {
        "evaluation": {
            "dataset": "IMDAA July 2020",
            "train_period": {
                "end": TRAIN_END
            },
            "test_period": {
                "start": TEST_START,
                "end": TEST_END
            },
            "rain_threshold": RAIN_THRESHOLD,
            "probability_threshold": (
                PROBABILITY_THRESHOLD
            ),
            "minimum_actual_positive_cells": (
                MIN_ACTUAL_POSITIVES
            )
        },

        "overall_test_metrics": {
            "roc_auc": round(
                float(overall_auc),
                4
            ),
            "precision": round(
                float(overall_precision),
                4
            ),
            "recall": round(
                float(overall_recall),
                4
            ),
            "f1": round(
                float(overall_f1),
                4
            )
        },

        "event_count": len(events),

        "events": events
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
    # Terminal output
    # ---------------------------------------------------------

    print("\n" + "=" * 65)
    print("MULTI-EVENT XGBOOST EVALUATION")
    print("=" * 65)

    print(
        f"Test period: "
        f"{TEST_START} -> {TEST_END}"
    )

    print(
        f"\nOverall ROC-AUC: "
        f"{overall_auc:.4f}"
    )

    print(
        f"Overall Precision: "
        f"{overall_precision:.4f}"
    )

    print(
        f"Overall Recall: "
        f"{overall_recall:.4f}"
    )

    print(
        f"Overall F1: "
        f"{overall_f1:.4f}"
    )

    print("\nEvent-wise results:")

    for event in events:
        print(
            f"\n{event['forecast_time']}"
        )

        print(
            f"  Actual cells: "
            f"{event['actual_high_rain_cells']}"
        )

        print(
            f"  Predicted cells: "
            f"{event['predicted_high_rain_cells']}"
        )

        print(
            f"  Precision: "
            f"{event['precision']:.4f}"
        )

        print(
            f"  Recall: "
            f"{event['recall']:.4f}"
        )

        print(
            f"  F1: "
            f"{event['f1']:.4f}"
        )

        if event["roc_auc"] is not None:
            print(
                f"  ROC-AUC: "
                f"{event['roc_auc']:.4f}"
            )

    print(
        f"\nSaved: {OUTPUT_FILE}"
    )

    print("=" * 65)


if __name__ == "__main__":
    main()