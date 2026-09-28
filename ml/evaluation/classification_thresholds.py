import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import precision_score, recall_score, f1_score


INPUT_FILE = "data/processed/ml_features_july01_15.csv"

THRESHOLD = 2.3125


def main():

    df = pd.read_csv(INPUT_FILE)

    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time")

    df["heavy_rain"] = (
        df["target_precipitation"] >= THRESHOLD
    ).astype(int)

    drop_columns = [
        "time",
        "target_precipitation",
        "heavy_rain"
    ]

    features = [
        column
        for column in df.columns
        if column not in drop_columns
    ]

    split_time = df["time"].quantile(0.8)

    train = df[df["time"] <= split_time]
    test = df[df["time"] > split_time]

    X_train = train[features]
    y_train = train["heavy_rain"]

    X_test = test[features]
    y_test = test["heavy_rain"]

    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    probabilities = model.predict_proba(X_test)[:, 1]

    print("Threshold | Precision | Recall | F1")
    print("-" * 40)

    for threshold in [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50]:

        predictions = (
            probabilities >= threshold
        ).astype(int)

        precision = precision_score(
            y_test,
            predictions,
            zero_division=0
        )

        recall = recall_score(
            y_test,
            predictions,
            zero_division=0
        )

        f1 = f1_score(
            y_test,
            predictions,
            zero_division=0
        )

        print(
            f"{threshold:8.2f} | "
            f"{precision:9.4f} | "
            f"{recall:6.4f} | "
            f"{f1:6.4f}"
        )


if __name__ == "__main__":
    main()