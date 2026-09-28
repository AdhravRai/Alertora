import os
import joblib
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


INPUT_FILE = "data/processed/ml_features_july01_15.csv"
MODEL_FILE = "data/processed/xgboost_precipitation.json"


def main():

    df = pd.read_csv(INPUT_FILE)

    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time")

    target = "target_precipitation"

    drop_columns = [
        "time",
        "target_precipitation"
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
    y_train = train[target]

    X_test = test[features]
    y_test = test[target]

    print(f"Training samples: {len(X_train)}")
    print(f"Test samples: {len(X_test)}")
    print(f"Train end: {train['time'].max()}")
    print(f"Test start: {test['time'].min()}")

    model = XGBRegressor(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=-1
    )

    print("\nTraining XGBoost...")

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(X_test)

    predictions = predictions.clip(min=0)

    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = mean_squared_error(
        y_test,
        predictions
    ) ** 0.5

    r2 = r2_score(
        y_test,
        predictions
    )

    print("\nEvaluation:")
    print(f"MAE  : {mae:.4f}")
    print(f"RMSE : {rmse:.4f}")
    print(f"R2   : {r2:.4f}")

    os.makedirs("data/processed", exist_ok=True)

    model.save_model(MODEL_FILE)

    print(f"\nModel saved to: {MODEL_FILE}")


if __name__ == "__main__":
    main()