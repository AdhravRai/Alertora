import sys
from pathlib import Path

import numpy as np

# Add person-b to Python path
PERSON_B = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PERSON_B))

from data.imdaa_loader import load_imdaa
from storm_tracking.tracker import extract_storm_cells


DATASET = "person-b/data/processed/imdaa_20200715.nc"


def main():
    fields = load_imdaa(DATASET)

    print("Loaded frames:", len(fields))

    # Test the first real precipitation frame
    frame = fields[0]

    print("\nFrame information:")
    print("Timestamp:", frame.timestamp)
    print("Grid shape:", frame.field.shape)
    print("Minimum:", np.min(frame.field))
    print("Maximum:", np.max(frame.field))
    print("Mean:", np.mean(frame.field))

    # Use a percentile because precipitation units are not
    # finalized yet.
    threshold = np.percentile(frame.field, 90)

    print("\nRelative storm threshold:")
    print("90th percentile:", threshold)

    storms = extract_storm_cells(
        frame.field,
        threshold=threshold,
        min_area=2
    )

    print("\nDetected storm cells:", len(storms))

    for storm in storms:
        print(storm)


if __name__ == "__main__":
    main()
    