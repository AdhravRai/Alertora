import json
import math
from pathlib import Path


FILE_PATH = Path("data/processed/alertora_forecast_july29_0200.json")


def fail(message):
    raise ValueError(f"VALIDATION FAILED: {message}")


def check_number(value, name):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        fail(f"{name} must be numeric")

    if not math.isfinite(value):
        fail(f"{name} must be finite")


def check_probability(value, name):
    check_number(value, name)

    if not 0.0 <= value <= 1.0:
        fail(f"{name} must be between 0 and 1")


def check_position(position, name):
    if not isinstance(position, dict):
        fail(f"{name} must be an object")

    for key in ["latitude", "longitude"]:
        if key not in position:
            fail(f"{name}.{key} is missing")

        check_number(position[key], f"{name}.{key}")

    if not -90 <= position["latitude"] <= 90:
        fail(f"{name}.latitude is outside valid range")

    if not -180 <= position["longitude"] <= 180:
        fail(f"{name}.longitude is outside valid range")


def main():
    print("ALERTORA FORECAST VALIDATOR")
    print("-" * 40)

    if not FILE_PATH.exists():
        fail(f"file not found: {FILE_PATH}")

    with FILE_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    # ---------------------------------------------------------
    # Root structure
    # ---------------------------------------------------------

    required_root = [
        "product",
        "version",
        "forecast",
        "method",
        "method_note",
        "storm",
        "horizons",
        "explainability",
        "historical_verification",
    ]

    for key in required_root:
        if key not in data:
            fail(f"root field '{key}' is missing")

    print("[OK] Root structure")

    # ---------------------------------------------------------
    # Forecast metadata
    # ---------------------------------------------------------

    if data["product"] != "ALERTORA_FORECAST":
        fail("unexpected product name")

    forecast = data["forecast"]

    for key in ["base_time", "horizon_hours", "source"]:
        if key not in forecast:
            fail(f"forecast.{key} is missing")

    if forecast["horizon_hours"] != 6:
        fail("forecast horizon is not 6 hours")

    source = forecast["source"]

    for key in [
        "dataset",
        "resolution",
        "temporal_resolution",
    ]:
        if key not in source:
            fail(f"forecast.source.{key} is missing")

    print("[OK] Forecast metadata")

    # ---------------------------------------------------------
    # Method
    # ---------------------------------------------------------

    method = data["method"]

    for key in [
        "ml_component",
        "spatial_component",
        "influence_radius_km",
        "ml_weight",
        "trajectory_weight",
    ]:
        if key not in method:
            fail(f"method.{key} is missing")

    check_number(
        method["influence_radius_km"],
        "method.influence_radius_km",
    )

    check_number(
        method["ml_weight"],
        "method.ml_weight",
    )

    check_number(
        method["trajectory_weight"],
        "method.trajectory_weight",
    )

    if abs(
        method["ml_weight"]
        + method["trajectory_weight"]
        - 1.0
    ) > 1e-6:
        fail("ML and trajectory weights do not sum to 1")

    print("[OK] Method metadata")

    # ---------------------------------------------------------
    # Method note
    # ---------------------------------------------------------

    if not isinstance(data["method_note"], str):
        fail("method_note must be a string")

    if not data["method_note"].strip():
        fail("method_note is empty")

    print("[OK] Method note")

    # ---------------------------------------------------------
    # Storm
    # ---------------------------------------------------------

    storm = data["storm"]

    for key in [
        "track_id",
        "current_position",
        "motion",
    ]:
        if key not in storm:
            fail(f"storm.{key} is missing")

    check_position(
        storm["current_position"],
        "storm.current_position",
    )

    motion = storm["motion"]

    for key in [
        "vx_grid_per_min",
        "vy_grid_per_min",
        "speed_grid_per_min",
        "direction_degrees",
    ]:
        if key not in motion:
            fail(f"storm.motion.{key} is missing")

        check_number(
            motion[key],
            f"storm.motion.{key}",
        )

    print("[OK] Storm information")

    # ---------------------------------------------------------
    # Horizons
    # ---------------------------------------------------------

    horizons = data["horizons"]

    if not isinstance(horizons, list):
        fail("horizons must be a list")

    if len(horizons) != 6:
        fail(
            f"expected 6 horizons, found {len(horizons)}"
        )

    expected_leads = [1, 2, 3, 4, 5, 6]

    for index, horizon in enumerate(horizons):

        for key in [
            "lead_hours",
            "lead_minutes",
            "storm_position",
            "summary",
            "grid",
        ]:
            if key not in horizon:
                fail(
                    f"horizons[{index}].{key} is missing"
                )

        # Check lead time
        if horizon["lead_hours"] != expected_leads[index]:
            fail(
                f"horizon {index} has unexpected "
                f"lead_hours={horizon['lead_hours']}"
            )

        if (
            horizon["lead_minutes"]
            != expected_leads[index] * 60
        ):
            fail(
                f"horizon {index} has unexpected "
                f"lead_minutes="
                f"{horizon['lead_minutes']}"
            )

        # Storm position
        check_position(
            horizon["storm_position"],
            f"horizons[{index}].storm_position",
        )

        # Summary
        if not isinstance(horizon["summary"], dict):
            fail(
                f"horizons[{index}].summary "
                "must be an object"
            )

        # Grid
        grid = horizon["grid"]

        if not isinstance(grid, dict):
            fail(
                f"horizons[{index}].grid "
                "must be an object"
            )

        # IMPORTANT:
        # Actual schema contains cells directly.
        if "cells" not in grid:
            fail(
                f"horizons[{index}].grid.cells "
                "is missing"
            )

        cells = grid["cells"]

        if not isinstance(cells, list):
            fail(
                f"horizons[{index}].grid.cells "
                "must be a list"
            )

        if len(cells) != 289:
            fail(
                f"horizon {index}: expected 289 cells, "
                f"found {len(cells)}"
            )

        # Validate every cell
        for cell_index, cell in enumerate(cells):

            cell_name = (
                f"horizons[{index}].grid.cells"
                f"[{cell_index}]"
            )

            if not isinstance(cell, dict):
                fail(f"{cell_name} must be an object")

            required_cell_fields = [
                "latitude",
                "longitude",
                "ml_probability",
                "storm_proximity",
                "nowcast_probability",
                "predicted_high_rain",
            ]

            for key in required_cell_fields:
                if key not in cell:
                    fail(
                        f"{cell_name}.{key} is missing"
                    )

            # Coordinates
            check_position(cell, cell_name)

            # Probabilities
            check_probability(
                cell["ml_probability"],
                f"{cell_name}.ml_probability",
            )

            check_probability(
                cell["storm_proximity"],
                f"{cell_name}.storm_proximity",
            )

            check_probability(
                cell["nowcast_probability"],
                f"{cell_name}.nowcast_probability",
            )

            # Boolean classification
            if not isinstance(
                cell["predicted_high_rain"],
                bool,
            ):
                fail(
                    f"{cell_name}.predicted_high_rain "
                    "must be boolean"
                )

    print("[OK] 6 horizons")
    print("[OK] 17 x 17 = 289 cells per horizon")
    print("[OK] Grid coordinates")
    print("[OK] Probability ranges")
    print("[OK] No invalid numeric values")

    # ---------------------------------------------------------
    # Explainability
    # ---------------------------------------------------------

    explainability = data["explainability"]

    for key in [
        "method",
        "global_top_features",
        "cell_explanations",
    ]:
        if key not in explainability:
            fail(
                f"explainability.{key} is missing"
            )

    if not isinstance(
        explainability["global_top_features"],
        list,
    ):
        fail(
            "global_top_features must be a list"
        )

    if len(
        explainability["global_top_features"]
    ) == 0:
        fail("global_top_features is empty")

    if not isinstance(
        explainability["cell_explanations"],
        list,
    ):
        fail(
            "cell_explanations must be a list"
        )

    if len(
        explainability["cell_explanations"]
    ) == 0:
        fail("cell_explanations is empty")

    print("[OK] Explainability / SHAP")

    # ---------------------------------------------------------
    # Historical verification
    # ---------------------------------------------------------

    historical = data["historical_verification"]

    if "available" not in historical:
        fail(
            "historical_verification.available "
            "is missing"
        )

    if historical["available"] is not True:
        fail(
            "historical_verification.available "
            "must be True"
        )

    if "note" not in historical:
        fail(
            "historical_verification.note is missing"
        )

    if (
        "Historical verification only"
        not in historical["note"]
    ):
        fail(
            "historical verification note does not "
            "clearly identify the data as historical"
        )

    print("[OK] Historical verification flag")

    # ---------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------

    print("-" * 40)
    print("VALIDATION PASSED")
    print(f"Base time: {forecast['base_time']}")
    print(f"Horizons: {len(horizons)}")
    print("Grid: 17 x 17 = 289 cells/horizon")
    print(f"Storm track: {storm['track_id']}")
    print("Historical verification: YES")
    print("-" * 40)


if __name__ == "__main__":
    main()