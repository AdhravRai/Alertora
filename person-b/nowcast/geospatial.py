import numpy as np


def grid_to_latlon(x, y, latitudes, longitudes):
    """
    Convert grid coordinates to latitude/longitude.

    x = longitude/grid-column position
    y = latitude/grid-row position
    """

    latitudes = np.asarray(latitudes, dtype=float)
    longitudes = np.asarray(longitudes, dtype=float)

    x = float(np.clip(x, 0, len(longitudes) - 1))
    y = float(np.clip(y, 0, len(latitudes) - 1))

    lon = np.interp(
        x,
        np.arange(len(longitudes)),
        longitudes
    )

    lat = np.interp(
        y,
        np.arange(len(latitudes)),
        latitudes
    )

    return float(lat), float(lon)


def latlon_to_grid(lat, lon, latitudes, longitudes):
    """
    Convert latitude/longitude back to grid coordinates.
    """

    latitudes = np.asarray(latitudes, dtype=float)
    longitudes = np.asarray(longitudes, dtype=float)

    x = np.interp(
        lon,
        longitudes,
        np.arange(len(longitudes))
    )

    y = np.interp(
        lat,
        latitudes,
        np.arange(len(latitudes))
    )

    return float(x), float(y)