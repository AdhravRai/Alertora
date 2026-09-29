import os

import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score
)

INPUT_FILE = "data/processed/ml_features_july2020.csv"
MODEL_FILE = "data/processed/xgboost_heavy_rain_july2020.json"

TRAIN_END = "2020-07-21 23:00:00"
VALIDATION_END = "2020-07-26 23:00:00"

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
        INPUT_FILE,
        parse_dates=["time"]
    )

    print(f"Total rows: {len(df)}")

    train = df[
        df["time"] <= pd.Timestamp(TRAIN_END)
    ].copy()

    validation = df[
        (df["time"] > pd.Timestamp(TRAIN_END)) &
        (df["time"] <= pd.Timestamp(VALIDATION_END))
    ].copy()

    test = df[
        df["time"] > pd.Timestamp(VALIDATION_END)
    ].copy()

    print("\nDataset split:")
    print(
        f"Train:      {len(train)} "
        f"({train['time'].min()} -> {train['time'].max()})"
    )

    print(
        f"Validation: {len(validation)} "
        f"({validation['time'].min()} -> {validation['time'].max()})"
    )

    print(
        f"Test:       {len(test)} "
        f"({test['time'].min()} -> {test['time'].max()})"
    )

    # ---------------------------------------------------------
    # Derive heavy-rain threshold ONLY from training data
    # ---------------------------------------------------------

    threshold = train["target_precipitation"].quantile(0.95)

    print("\nHeavy-rain threshold:")
    print(f"95th percentile of training target = {threshold:.4f}")

    # Create binary target
    train["target"] = (
        train["target_precipitation"] >= threshold
    ).astype(int)

    validation["target"] = (
        validation["target_precipitation"] >= threshold
    ).astype(int)

    test["target"] = (
        test["target_precipitation"] >= threshold
    ).astype(int)

    print("\nClass distribution:")

    for name, data in [
        ("Train", train),
        ("Validation", validation),
        ("Test", test)
    ]:
        positives = int(data["target"].sum())
        total = len(data)
        percentage = positives / total * 100

        print(
            f"{name}: "
            f"{positives} positive / {total} "
            f"({percentage:.2f}%)"
        )

    # ---------------------------------------------------------
    # Prepare features
    # ---------------------------------------------------------

    X_train = train[FEATURE_COLUMNS]
    y_train = train["target"]

    X_validation = validation[FEATURE_COLUMNS]
    y_validation = validation["target"]

    X_test = test[FEATURE_COLUMNS]
    y_test = test["target"]

    # ---------------------------------------------------------
    # Handle class imbalance
    # ---------------------------------------------------------

    positive_count = y_train.sum()
    negative_count = len(y_train) - positive_count

    scale_pos_weight = negative_count / positive_count

    print(
        f"\nscale_pos_weight = {scale_pos_weight:.2f}"
    )

    # ---------------------------------------------------------
    # Train XGBoost
    # ---------------------------------------------------------

    print("\nTraining XGBoost...")

    model = XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="auc",
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[
            (X_validation, y_validation)
        ],
        verbose=False
    )

    print("Training complete.")

    # ---------------------------------------------------------
    # Validation evaluation
    # ---------------------------------------------------------

    validation_probability = model.predict_proba(
        X_validation
    )[:, 1]

    validation_prediction = (
        validation_probability >= 0.25
    ).astype(int)

    validation_auc = roc_auc_score(
        y_validation,
        validation_probability
    )

    print("\nValidation results")
    print("------------------")

    print(
        f"ROC-AUC:  {validation_auc:.4f}"
    )

    print(
        f"Precision: "
        f"{precision_score(y_validation, validation_prediction, zero_division=0):.4f}"
    )

    print(
        f"Recall:    "
        f"{recall_score(y_validation, validation_prediction, zero_division=0):.4f}"
    )

    print(
        f"F1:        "
        f"{f1_score(y_validation, validation_prediction, zero_division=0):.4f}"
    )

    print("\nValidation confusion matrix:")

    print(
        confusion_matrix(
            y_validation,
            validation_prediction
        )
    )

    # ---------------------------------------------------------
    # Test evaluation
    # ---------------------------------------------------------

    test_probability = model.predict_proba(
        X_test
    )[:, 1]

    test_prediction = (
        test_probability >= 0.25
    ).astype(int)

    test_auc = roc_auc_score(
        y_test,
        test_probability
    )

    print("\nTest results")
    print("------------")

    print(
        f"ROC-AUC:  {test_auc:.4f}"
    )

    print(
        f"Precision: "
        f"{precision_score(y_test, test_prediction, zero_division=0):.4f}"
    )

    print(
        f"Recall:    "
        f"{recall_score(y_test, test_prediction, zero_division=0):.4f}"
    )

    print(
        f"F1:        "
        f"{f1_score(y_test, test_prediction, zero_division=0):.4f}"
    )

    print("\nTest confusion matrix:")

    print(
        confusion_matrix(
            y_test,
            test_prediction
        )
    )

    # ---------------------------------------------------------
    # Save model
    # ---------------------------------------------------------

    os.makedirs(
        os.path.dirname(MODEL_FILE),
        exist_ok=True
    )

    model.save_model(MODEL_FILE)

    print(
        f"\nModel saved to: {MODEL_FILE}"
    )

    print("\nClassification report:")

    print(
        classification_report(
            y_test,
            test_prediction,
            digits=4,
            zero_division=0
        )
    )


if __name__ == "__main__":
    main()