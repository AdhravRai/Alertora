from dataclasses import dataclass
from datetime import datetime

import numpy as np


@dataclass
class SpatialField:
    """
    Standard spatial weather-field representation
    used by the Person-B pipeline.
    """

    timestamp: datetime

    latitudes: np.ndarray
    longitudes: np.ndarray

    field: np.ndarray

    variable: str = "precipitation"
    units: str = "mm/hr"


def validate_spatial_field(spatial_field):
    """
    Validate that a spatial field follows
    the Person-B data contract.
    """

    if spatial_field.field.ndim != 2:
        raise ValueError(
            "Weather field must be a 2D array"
        )

    if spatial_field.latitudes.ndim != 1:
        raise ValueError(
            "Latitude must be a 1D array"
        )

    if spatial_field.longitudes.ndim != 1:
        raise ValueError(
            "Longitude must be a 1D array"
        )

    expected_shape = (
        len(spatial_field.latitudes),
        len(spatial_field.longitudes)
    )

    if spatial_field.field.shape != expected_shape:
        raise ValueError(
            f"Field shape {spatial_field.field.shape} "
            f"does not match coordinate shape "
            f"{expected_shape}"
        )

    return True