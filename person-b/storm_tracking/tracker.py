import numpy as np
from scipy import ndimage


def extract_storm_cells(field, threshold=10.0, min_area=5):
    """
    Extract storm cells from a 2D precipitation field.

    Parameters
    ----------
    field : numpy.ndarray
        2D precipitation/rain-rate field.

    threshold : float
        Minimum precipitation value considered a storm cell.

    min_area : int
        Minimum number of pixels required for a valid cell.

    Returns
    -------
    list
        Detected storm cells.
    """

    field = np.asarray(field, dtype=float)

    # Replace invalid values
    field = np.nan_to_num(field, nan=0.0)

    # Create binary storm mask
    storm_mask = field >= threshold

    # Find connected components
    labels, num_features = ndimage.label(storm_mask)

    storms = []

    for storm_id in range(1, num_features + 1):

        # Get pixels belonging to this storm
        pixels = np.argwhere(labels == storm_id)

        # Ignore very small regions
        if len(pixels) < min_area:
            continue

        y = pixels[:, 0]
        x = pixels[:, 1]

        # Calculate centroid
        centroid_x = x.mean()
        centroid_y = y.mean()

        # Get intensity values
        cell_values = field[labels == storm_id]

        storms.append({
            "id": f"storm_{len(storms) + 1}",
            "centroid_x": float(centroid_x),
            "centroid_y": float(centroid_y),
            "max_intensity": float(np.max(cell_values)),
            "mean_intensity": float(np.mean(cell_values)),
            "area_pixels": int(len(pixels))
        })

    return storms


# Simple local test
if __name__ == "__main__":

    # Create a 100x100 test precipitation field
    field = np.zeros((100, 100))

    # Storm cell 1
    field[20:35, 30:50] = 25

    # Storm cell 2
    field[60:75, 65:85] = 40

    storms = extract_storm_cells(
        field,
        threshold=10,
        min_area=10
    )

    print("\nDetected storm cells:")

    for storm in storms:
        print(storm)