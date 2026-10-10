import numpy as np


def summarize_precipitation(field):
    """
    Summarize the precipitation field.

    Values are kept in the dataset's native/raw units
    until the IMDAA precipitation metadata is verified.
    """

    field = np.asarray(field, dtype=float)

    return {
        "minimum": float(np.min(field)),
        "maximum": float(np.max(field)),
        "mean": float(np.mean(field)),
        "p90": float(np.percentile(field, 90)),
        "p95": float(np.percentile(field, 95)),
        "p99": float(np.percentile(field, 99)),
    }


def detect_relative_heavy_rain(field, percentile=95):
    """
    Detect relatively high precipitation areas using a
    percentile-based threshold.

    This is NOT a physical mm/hr heavy-rain threshold.
    It is only a relative indicator until units are verified.
    """

    field = np.asarray(field, dtype=float)

    threshold = float(
        np.percentile(field, percentile)
    )

    mask = field >= threshold

    return {
        "indicator": "relative_heavy_rain",
        "threshold_percentile": percentile,
        "threshold_raw_value": threshold,
        "affected_pixels": int(np.sum(mask)),
        "fraction_of_grid": float(np.mean(mask)),
    }


def detect_relative_extreme(field, percentile=99):
    """
    Detect the highest precipitation tail of the field.

    This is a relative extreme indicator, not a confirmed
    cloudburst classification.
    """

    field = np.asarray(field, dtype=float)

    threshold = float(
        np.percentile(field, percentile)
    )

    mask = field >= threshold

    return {
        "indicator": "relative_extreme_precipitation",
        "threshold_percentile": percentile,
        "threshold_raw_value": threshold,
        "affected_pixels": int(np.sum(mask)),
        "fraction_of_grid": float(np.mean(mask)),
    }