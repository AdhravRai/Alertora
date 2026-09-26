import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


INPUT_FILE = "data/processed/ml_features_july01_15.csv"


def main():

    df = pd.read_csv(INPUT_FILE)

    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time")

    split_time = df["time"].quantile(0.8)

    test = df[df["time"] > split_time].copy()

    y_true = test["target_precipitation"]

    # Persistence: next hour precipitation = current hour precipitation
    y_pred = test["precipitation"]

    mae = mean_absolute_error(y_true, y_pred)

    rmse = mean_squared_error(y_true, y_pred) ** 0.5

    r2 = r2_score(y_true, y_pred)

    print("Persistence baseline:")
    print(f"MAE  : {mae:.4f}")
    print(f"RMSE : {rmse:.4f}")
    print(f"R2   : {r2:.4f}")


if __name__ == "__main__":
    main()
    