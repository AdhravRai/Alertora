import pandas as pd
import numpy as np


INPUT_FILE = "data/processed/ml_features_july01_15.csv"


def main():

    df = pd.read_csv(INPUT_FILE)

    df["time"] = pd.to_datetime(df["time"])

    print("Precipitation statistics:")
    print(df["precipitation"].describe())

    print("\nTarget precipitation statistics:")
    print(df["target_precipitation"].describe())

    print("\nZero precipitation percentage:")

    zero_percentage = (
        (df["precipitation"] == 0).mean() * 100
    )

    print(f"{zero_percentage:.2f}%")

    print("\nTarget zero percentage:")

    target_zero_percentage = (
        (df["target_precipitation"] == 0).mean() * 100
    )

    print(f"{target_zero_percentage:.2f}%")

    print("\nCorrelation with next-hour precipitation:")

    numeric_columns = [
        "precipitation",
        "precipitation_lag1",
        "precipitation_lag3",
        "temperature",
        "relative_humidity",
        "surface_pressure",
        "u_wind",
        "v_wind",
        "cloud_water",
        "wind_speed"
    ]

    print(
        df[numeric_columns + ["target_precipitation"]]
        .corr()["target_precipitation"]
        .sort_values(ascending=False)
    )


if __name__ == "__main__":
    main()