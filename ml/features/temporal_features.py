import os
import xarray as xr
import pandas as pd
import numpy as np

INPUT_FILE = "data/processed/imdaa_july2020.nc"
OUTPUT_FILE = "data/processed/ml_features_july2020.csv"


def create_features():
    print("Loading IMDAA dataset...")

    ds = xr.open_dataset(INPUT_FILE)

    df = ds.to_dataframe().reset_index()

    print(f"Raw rows: {len(df)}")
    print(f"Time range: {df['time'].min()} -> {df['time'].max()}")

    # Wind speed
    df["wind_speed"] = np.sqrt(
        df["u_wind"] ** 2 +
        df["v_wind"] ** 2
    )

    # Sort chronologically for each grid cell
    df = df.sort_values(
        ["lat", "lon", "time"]
    ).reset_index(drop=True)

    grouped = df.groupby(
        ["lat", "lon"],
        group_keys=False
    )

    # Variables for temporal features
    lag_columns = [
        "temperature",
        "relative_humidity",
        "surface_pressure",
        "u_wind",
        "v_wind",
        "cloud_water",
        "precipitation",
        "wind_speed"
    ]

    print("Creating lag features...")

    for column in lag_columns:
        df[f"{column}_lag1"] = grouped[column].shift(1)
        df[f"{column}_lag3"] = grouped[column].shift(3)

    # Change over time
    print("Creating temporal change features...")

    df["precipitation_change"] = (
        df["precipitation"] -
        df["precipitation_lag1"]
    )

    df["cloud_water_change"] = (
        df["cloud_water"] -
        df["cloud_water_lag1"]
    )

    df["humidity_change"] = (
        df["relative_humidity"] -
        df["relative_humidity_lag1"]
    )

    df["temperature_change"] = (
        df["temperature"] -
        df["temperature_lag1"]
    )

    df["wind_speed_change"] = (
        df["wind_speed"] -
        df["wind_speed_lag1"]
    )

    # Target: next-hour precipitation
    print("Creating next-hour target...")

    df["target_precipitation"] = grouped[
        "precipitation"
    ].shift(-1)

    # Remove rows where lag/target information is unavailable
    before_drop = len(df)

    df = df.dropna().reset_index(drop=True)

    after_drop = len(df)

    print(f"Rows removed: {before_drop - after_drop}")
    print(f"Final rows: {after_drop}")

    # Save
    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\nFeature dataset created successfully.")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print(f"Saved to: {OUTPUT_FILE}")

    print("\nTime range:")
    print(df["time"].min())
    print(df["time"].max())

    print("\nColumns:")
    print(df.columns.tolist())


if __name__ == "__main__":
    create_features()