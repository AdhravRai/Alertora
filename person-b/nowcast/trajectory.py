def predict_position(storm, motion, lead_minutes):
    """
    Predict storm position after a given number of minutes.
    """

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
    """
    Generate future storm positions.
    """

    lead_times = [
        30,
        60,
        90,
        120,
        180,
        360
    ]

    trajectory = []

    for minutes in lead_times:
        position = predict_position(
            storm,
            motion,
            minutes
        )

        trajectory.append(position)

    return trajectory