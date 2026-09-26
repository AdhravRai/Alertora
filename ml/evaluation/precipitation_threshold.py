import pandas as pd


INPUT_FILE = "data/processed/ml_features_july01_15.csv"


def main():

    df = pd.read_csv(INPUT_FILE)

    print("Current precipitation quantiles:")
    print(
        df["precipitation"].quantile(
            [0.50, 0.75, 0.90, 0.95, 0.99, 0.995, 0.999]
        )
    )

    print("\nNext-hour precipitation quantiles:")
    print(
        df["target_precipitation"].quantile(
            [0.50, 0.75, 0.90, 0.95, 0.99, 0.995, 0.999]
        )
    )


if __name__ == "__main__":
    main()