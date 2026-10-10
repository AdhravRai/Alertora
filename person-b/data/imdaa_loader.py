import sys
from pathlib import Path

import xarray as xr
import numpy as np

# Add person-b to Python's import path
PERSON_B = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PERSON_B))

from data.loader import SpatialField, validate_spatial_field


def load_imdaa(filepath):
    """
    Load precipitation frames from an IMDAA NetCDF file.

    Returns:
        list[SpatialField]: One SpatialField for each time step.
    """

    ds = xr.open_dataset(filepath)

    precipitation = ds["precipitation"]

    spatial_fields = []

    for i in range(len(ds.time)):
        field = np.asarray(
            precipitation.isel(time=i).values,
            dtype=float
        )

        spatial_field = SpatialField(
            timestamp=ds.time.values[i],
            latitudes=np.asarray(ds.lat.values, dtype=float),
            longitudes=np.asarray(ds.lon.values, dtype=float),
            field=field,
            variable="precipitation",
            units="unknown"
        )

        validate_spatial_field(spatial_field)

        spatial_fields.append(spatial_field)

    ds.close()

    return spatial_fields


if __name__ == "__main__":

    filepath = "person-b/data/processed/imdaa_20200715.nc"

    fields = load_imdaa(filepath)

    print("IMDAA loaded successfully!")
    print("Number of frames:", len(fields))

    first = fields[0]
    last = fields[-1]

    print("\nFirst frame:")
    print("Timestamp:", first.timestamp)
    print("Shape:", first.field.shape)
    print("Min:", np.min(first.field))
    print("Max:", np.max(first.field))

    print("\nLast frame:")
    print("Timestamp:", last.timestamp)
    print("Shape:", last.field.shape)
    print("Min:", np.min(last.field))
    print("Max:", np.max(last.field))

    print("\nGeographic information:")
    print(
        "Latitude range:",
        first.latitudes.min(),
        "to",
        first.latitudes.max()
    )

    print(
        "Longitude range:",
        first.longitudes.min(),
        "to",
        first.longitudes.max()
    )

    print("Units:", first.units)