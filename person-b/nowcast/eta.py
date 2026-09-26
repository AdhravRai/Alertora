def calculate_eta_to_point(
    storm_x,
    storm_y,
    target_x,
    target_y,
    vx,
    vy
):
    """
    Estimate time for a storm to reach a target grid position.

    Returns minutes, or None if the storm is not moving
    toward the target.
    """

    dx = target_x - storm_x
    dy = target_y - storm_y

    # Avoid division by zero.
    if abs(vx) < 1e-9 and abs(vy) < 1e-9:
        return None

    times = []

    if abs(vx) > 1e-9:
        tx = dx / vx

        if tx >= 0:
            times.append(tx)

    if abs(vy) > 1e-9:
        ty = dy / vy

        if ty >= 0:
            times.append(ty)

    if not times:
        return None

    return float(min(times))
