def fuse_hazards(
    precipitation_summary,
    relative_heavy_rain,
    relative_extreme
):
    """
    Combine the available hazard indicators.

    These are relative indicators because the IMDAA
    precipitation units are still being verified.
    """

    hazards = []

    if relative_heavy_rain["affected_pixels"] > 0:
        hazards.append(
            {
                "type": "relative_heavy_rain",
                "status": "detected",
                "affected_pixels":
                    relative_heavy_rain["affected_pixels"],
                "fraction_of_grid":
                    relative_heavy_rain["fraction_of_grid"],
            }
        )

    if relative_extreme["affected_pixels"] > 0:
        hazards.append(
            {
                "type": "relative_extreme_precipitation",
                "status": "detected",
                "affected_pixels":
                    relative_extreme["affected_pixels"],
                "fraction_of_grid":
                    relative_extreme["fraction_of_grid"],
            }
        )

    return {
        "status": "relative_indicators_only",
        "hazards": hazards,
        "precipitation_summary": precipitation_summary,
        "units_verified": False,
    }
