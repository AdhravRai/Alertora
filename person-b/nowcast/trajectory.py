LEAD_TIMES = [30, 60, 90, 120, 180, 360]


def predict_position(storm, motion, lead_minutes):
    future_x = (
        storm["centroid_x"]
        + motion["vx"] * lead_minutes
    )

    future_y = (
        storm["centroid_y"]
        + motion["vy"] * lead_minutes
    )

    return {
        "lead_minutes": lead_minutes,
        "x": float(future_x),
        "y": float(future_y)
    }


def generate_trajectory(storm, motion):
    return [
        predict_position(storm, motion, minutes)
        for minutes in LEAD_TIMES
    ]