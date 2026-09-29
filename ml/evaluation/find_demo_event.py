import pandas as pd

FEATURE_FILE = "data/processed/ml_features_july2020.csv"

RAIN_THRESHOLD = 2.2812

df = pd.read_csv(
    FEATURE_FILE,
    parse_dates=["time"]
)

# Only unseen test period
test = df[
    df["time"] >= pd.Timestamp("2020-07-27 00:00:00")
].copy()

# Count high-rain cells at every timestamp
event_counts = (
    test.assign(
        high_rain=test["target_precipitation"] >= RAIN_THRESHOLD
    )
    .groupby("time")["high_rain"]
    .sum()
    .sort_values(ascending=False)
)

print("\nTop historical high-rain events")
print("--------------------------------")

print(
    event_counts.head(20).to_string()
)

print("\nBest demo timestamp:")
print(event_counts.index[0])

print(
    f"High-rain cells: "
    f"{int(event_counts.iloc[0])}"
)