import glob
import os
import pandas as pd
import xarray as xr


DATA_DIR = "data/raw/f91110cd-f5a7-4cb4-b47f-8671c828331e"
OUTPUT_FILE = "data/processed/imdaa_20200715.nc"


VARIABLES = {
    "APCP-sfc": ("param8.1.0", "precipitation"),
    "CWP-sfc": ("cwp", "cloud_water"),
    "PRES-sfc": ("sp", "surface_pressure"),
    "RH-2m": ("2r", "relative_humidity"),
    "TMP-2m": ("2t", "temperature"),
    "UGRD-10m": ("10u", "u_wind"),
    "VGRD-10m": ("10v", "v_wind"),
}


def get_timestamp_from_filename(file):
    filename = os.path.basename(file)

    timestamp_string = filename.split("_")[1]

    return pd.to_datetime(timestamp_string, format="%Y%m%d%H")


def load_variable(prefix, variable_name, output_name):

    pattern = os.path.join(DATA_DIR, f"{prefix}_*.nc")
    files = sorted(glob.glob(pattern))

    datasets = []

    for file in files:

        ds = xr.open_dataset(file)

        data = ds[variable_name]

        if "height" in data.dims:
            data = data.squeeze("height", drop=True)

        timestamp = get_timestamp_from_filename(file)

        if "time" in data.dims:
            data = data.isel(time=0, drop=True)

        data = data.expand_dims(time=[timestamp])

        data = data.rename(output_name)

        datasets.append(data)

        ds.close()

    combined = xr.concat(
        datasets,
        dim="time",
        coords="minimal",
        compat="override"
    )

    combined = combined.sortby("time")

    return combined


def main():

    variables = []

    for prefix, (variable_name, output_name) in VARIABLES.items():

        print(f"Loading {prefix}...")

        data = load_variable(
            prefix,
            variable_name,
            output_name
        )

        print(
            f"  shape={data.shape}, "
            f"time={len(data.time)}"
        )

        variables.append(data)

    dataset = xr.merge(
        variables,
        compat="override",
        join="exact"
    )

    print("\nFinal dataset:")
    print(dataset)

    print("\nTime values:")
    print(dataset.time.values)

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    dataset.to_netcdf(OUTPUT_FILE)

    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()