import os
import xarray as xr

INPUT_FILE = "data/processed/imdaa_july2020.nc"
OUTPUT_FILE = "data/processed/imdaa_20200729.nc"

START_TIME = "2020-07-29 00:00:00"
END_TIME = "2020-07-29 23:00:00"


def main():
    print("Loading full July dataset...")

    ds = xr.open_dataset(INPUT_FILE)

    print(
        f"Full dataset: "
        f"{ds.time.values[0]} -> {ds.time.values[-1]}"
    )

    subset = ds.sel(
        time=slice(
            START_TIME,
            END_TIME
        )
    )

    print("\nJuly 29 subset:")
    print(subset)

    print(
        f"\nTimestamps: {len(subset.time)}"
    )

    print(
        f"Grid: "
        f"{len(subset.lat)} x {len(subset.lon)}"
    )

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    subset.to_netcdf(
        OUTPUT_FILE
    )

    print(
        f"\nSaved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()