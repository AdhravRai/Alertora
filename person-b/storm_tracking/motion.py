import math


def calculate_motion(previous_storm, current_storm, time_minutes):
    """
    Calculate storm movement between two observations.

    Parameters
    ----------
    previous_storm : dict
        Storm detected at the previous timestamp.

    current_storm : dict
        Storm detected at the current timestamp.

    time_minutes : float
        Time difference between observations in minutes.

    Returns
    -------
    dict
        Movement vector, speed and direction.
    """

    dx = (
        current_storm["centroid_x"]
        - previous_storm["centroid_x"]
    )

    dy = (
        current_storm["centroid_y"]
        - previous_storm["centroid_y"]
    )

    vx = dx / time_minutes
    vy = dy / time_minutes

    speed = math.sqrt(vx ** 2 + vy ** 2)

    # Direction in degrees
    direction = math.degrees(
        math.atan2(dx, -dy)
    )

    if direction < 0:
        direction += 360

    return {
        "dx": float(dx),
        "dy": float(dy),
        "vx": float(vx),
        "vy": float(vy),
        "speed_pixels_per_minute": float(speed),
        "direction_degrees": float(direction)
    }