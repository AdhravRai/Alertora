import glob
import os
import pandas as pd
import xarray as xr


DATA_DIR = "data/raw"
OUTPUT_FILE = "data/processed/imdaa_july2020.nc"

VARIABLES = {
    "APCP-sfc": ("param8.1.0", "precipitation"),
    "CWP-sfc": ("cwp", "cloud_water"),
    "PRES-sfc": ("sp", "surface_pressure"),
    "RH-2m": ("2r", "relative_humidity"),
    "TMP-2m": ("2t", "temperature"),
    "UGRD-10m": ("10u", "u_wind"),
    "VGRD-10m": ("10v", "v_wind"),
}


def get_files(prefix):
    pattern = os.path.join(DATA_DIR, "**", f"{prefix}_*.nc")
    files = glob.glob(pattern, recursive=True)

    files = [
        f for f in files
        if "20200701" <= os.path.basename(f).split("_")[1][:8] <= "20200731"
    ]

    return sorted(files)


def get_timestamp(file):
    timestamp = os.path.basename(file).split("_")[1]
    return pd.to_datetime(timestamp, format="%Y%m%d%H")


def load_variable(prefix, variable_name, output_name):

    files = get_files(prefix)

    print(f"  {len(files)} files")

    frames = []

    for file in files:

        ds = xr.open_dataset(file)

        data = ds[variable_name]

        if "height" in data.dims:
            data = data.squeeze("height", drop=True)

        if "time" in data.dims:
            data = data.isel(time=0, drop=True)

        timestamp = get_timestamp(file)

        data = data.expand_dims(time=[timestamp])
        data = data.rename(output_name)

        frames.append(data)

        ds.close()

    return xr.concat(
        frames,
        dim="time",
        coords="minimal",
        compat="override"
    ).sortby("time")


def main():

    variables = []

    for prefix, (variable_name, output_name) in VARIABLES.items():

        print(f"Loading {prefix}...")

        data = load_variable(
            prefix,
            variable_name,
            output_name
        )

        print(f"  shape = {data.shape}")

        variables.append(data)

    dataset = xr.merge(
        variables,
        compat="override",
        join="exact"
    )

    print("\nFinal dataset:")
    print(dataset)

    print("\nTime range:")
    print(dataset.time.values[0])
    print(dataset.time.values[-1])

    print(f"\nTotal timestamps: {len(dataset.time)}")

    os.makedirs("data/processed", exist_ok=True)

    dataset.to_netcdf(OUTPUT_FILE)

    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()