import cv2
import numpy as np


def normalize_field(field):
    """
    Convert a precipitation field to an 8-bit image
    suitable for optical-flow estimation.
    """

    field = np.asarray(field, dtype=np.float32)

    field = np.nan_to_num(
        field,
        nan=0.0,
        posinf=0.0,
        neginf=0.0
    )

    min_value = np.min(field)
    max_value = np.max(field)

    if max_value == min_value:
        return np.zeros_like(field, dtype=np.uint8)

    normalized = (
        (field - min_value)
        / (max_value - min_value)
        * 255
    )

    return normalized.astype(np.uint8)


def estimate_optical_flow(previous_field, current_field):
    """
    Estimate dense motion between two sequential
    precipitation fields.

    Returns
    -------
    flow : numpy.ndarray
        Shape: (height, width, 2)

        flow[..., 0] = x-direction movement
        flow[..., 1] = y-direction movement
    """

    previous = normalize_field(previous_field)
    current = normalize_field(current_field)

    flow = cv2.calcOpticalFlowFarneback(
        previous,
        current,
        None,
        pyr_scale=0.5,
        levels=3,
        winsize=15,
        iterations=3,
        poly_n=5,
        poly_sigma=1.2,
        flags=0
    )

    return flow


def average_motion(flow):
    """
    Calculate average motion across the field.
    """

    vx = flow[..., 0]
    vy = flow[..., 1]

    return {
        "vx": float(np.mean(vx)),
        "vy": float(np.mean(vy))
    }


if __name__ == "__main__":

    # ------------------------------------
    # TEST: moving precipitation cell
    # ------------------------------------

    previous_field = np.zeros((100, 100), dtype=np.float32)
    current_field = np.zeros((100, 100), dtype=np.float32)

    # Storm at T-30
    previous_field[40:55, 20:35] = 50

    # Same storm moved right/down at T0
    current_field[45:60, 30:45] = 50

    flow = estimate_optical_flow(
        previous_field,
        current_field
    )

    motion = average_motion(flow)

    print("\nOptical flow calculated successfully.")

    print("Flow shape:", flow.shape)

    print("Average motion:")
    print(motion)