import json
from pathlib import Path

# ============================================================
# ALERTORA FINAL SPATIAL SANITY CHECK
# ============================================================

FORECAST_FILE = Path("data/processed/alertora_forecast_july29_0200.json")
RISK_FILE = Path("data/processed/risk_zones_july29_0200.json")

MIN_LAT = 25.08
MAX_LAT = 27.00
MIN_LON = 82.08
MAX_LON = 84.00

print("=" * 70)
print("ALERTORA FINAL SPATIAL SANITY CHECK")
print("=" * 70)

# ------------------------------------------------------------
# Load files
# ------------------------------------------------------------

if not FORECAST_FILE.exists():
    print(f"\nERROR: Missing {FORECAST_FILE}")
    raise SystemExit(1)

if not RISK_FILE.exists():
    print(f"\nERROR: Missing {RISK_FILE}")
    raise SystemExit(1)

with open(FORECAST_FILE, "r", encoding="utf-8") as f:
    forecast = json.load(f)

with open(RISK_FILE, "r", encoding="utf-8") as f:
    risk_data = json.load(f)

print("\nFILES")
print("-" * 70)
print(f"Forecast : {FORECAST_FILE}")
print(f"Risk     : {RISK_FILE}")

print("\nIMDAA DOMAIN")
print("-" * 70)
print(f"Latitude : {MIN_LAT} -> {MAX_LAT}")
print(f"Longitude: {MIN_LON} -> {MAX_LON}")


# ------------------------------------------------------------
# Recursive helpers
# ------------------------------------------------------------

def find_objects_with_keys(obj, required_keys):
    """
    Recursively find dictionaries containing all required keys.
    """
    results = []

    if isinstance(obj, dict):
        if all(k in obj for k in required_keys):
            results.append(obj)

        for value in obj.values():
            results.extend(find_objects_with_keys(value, required_keys))

    elif isinstance(obj, list):
        for item in obj:
            results.extend(find_objects_with_keys(item, required_keys))

    return results


def in_domain(lat, lon):
    return (
        MIN_LAT <= float(lat) <= MAX_LAT
        and MIN_LON <= float(lon) <= MAX_LON
    )


def print_coordinate_status(name, lat, lon):
    status = "PASS" if in_domain(lat, lon) else "FAIL"

    print(
        f"{status:5} | "
        f"{name:<8} | "
        f"lat={float(lat):.4f} | "
        f"lon={float(lon):.4f}"
    )

    return status == "PASS"


# ------------------------------------------------------------
# Forecast metadata
# ------------------------------------------------------------

print("\nFORECAST METADATA")
print("-" * 70)

for key in [
    "base_time",
    "forecast_time",
    "timestamp",
    "base_timestamp"
]:
    if key in forecast:
        print(f"{key}: {forecast[key]}")


# ------------------------------------------------------------
# Search for trajectory coordinates
# ------------------------------------------------------------

print("\nSTORM TRAJECTORY")
print("-" * 70)

trajectory_objects = find_objects_with_keys(
    forecast,
    {"latitude", "longitude"}
)

# Remove duplicates while preserving order
seen = set()
trajectory_points = []

for obj in trajectory_objects:
    try:
        lat = float(obj["latitude"])
        lon = float(obj["longitude"])
    except (ValueError, TypeError):
        continue

    key = (lat, lon)

    if key not in seen:
        seen.add(key)
        trajectory_points.append(obj)

if not trajectory_points:
    print("WARNING: No latitude/longitude trajectory objects found.")
else:
    print(f"Found {len(trajectory_points)} coordinate objects.")

    all_inside = True

    for i, point in enumerate(trajectory_points, start=1):
        lat = point["latitude"]
        lon = point["longitude"]

        if not print_coordinate_status(f"point-{i}", lat, lon):
            all_inside = False

    if all_inside:
        print("\nTrajectory domain check: PASS")
    else:
        print("\nTrajectory domain check: CHECK REQUIRED")


# ------------------------------------------------------------
# Search risk-zone bounding boxes
# ------------------------------------------------------------

print("\nRISK-ZONE BOUNDING BOXES")
print("-" * 70)

bbox_objects = find_objects_with_keys(
    risk_data,
    {
        "min_latitude",
        "max_latitude",
        "min_longitude",
        "max_longitude"
    }
)

if not bbox_objects:
    print("WARNING: No bounding boxes found.")
else:

    print(f"Found {len(bbox_objects)} bounding boxes.")

    all_boxes_inside = True

    for i, box in enumerate(bbox_objects, start=1):

        min_lat = float(box["min_latitude"])
        max_lat = float(box["max_latitude"])
        min_lon = float(box["min_longitude"])
        max_lon = float(box["max_longitude"])

        valid = (
            MIN_LAT <= min_lat <= MAX_LAT
            and MIN_LAT <= max_lat <= MAX_LAT
            and MIN_LON <= min_lon <= MAX_LON
            and MIN_LON <= max_lon <= MAX_LON
            and min_lat <= max_lat
            and min_lon <= max_lon
        )

        print(
            f"{'PASS' if valid else 'FAIL':5} | "
            f"Zone {i:<3} | "
            f"lat {min_lat:.4f}-{max_lat:.4f} | "
            f"lon {min_lon:.4f}-{max_lon:.4f}"
        )

        if not valid:
            all_boxes_inside = False

    print()

    if all_boxes_inside:
        print("Risk-zone domain check: PASS")
    else:
        print("Risk-zone domain check: FAIL")


# ------------------------------------------------------------
# Horizon detection
# ------------------------------------------------------------

print("\nFORECAST HORIZONS")
print("-" * 70)

horizon_names = [
    "+1h",
    "+2h",
    "+3h",
    "+4h",
    "+5h",
    "+6h"
]

for horizon in horizon_names:

    found = False

    def recursive_find(obj):
        nonlocal_dummy = None

        if isinstance(obj, dict):
            for key, value in obj.items():

                key_string = str(key).lower()

                if horizon.lower() in key_string:
                    return True

                result = recursive_find(value)

                if result:
                    return True

        elif isinstance(obj, list):
            for item in obj:
                result = recursive_find(item)

                if result:
                    return True

        return False

    found = recursive_find(forecast)

    print(
        f"{'FOUND' if found else 'NOT FOUND':10} {horizon}"
    )


# ------------------------------------------------------------
# Final result
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FINAL SANITY CHECK")
print("=" * 70)

print("""
Required checks:

[ ] Storm trajectory +1h -> +6h visually verified
[ ] Risk-zone bounding boxes visually verified
[ ] Timeline switches correctly
[ ] No risk zone outside IMDAA domain
[ ] No coordinate inversion
[ ] No stale July 15 data
[ ] No browser console errors

IMPORTANT:
This script validates the data.
The final map/timeline check must be performed in the browser.
""")

print("=" * 70)