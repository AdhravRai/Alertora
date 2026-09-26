import sys
from pathlib import Path

import numpy as np

# ---------------------------------------------------------
# Python path
# ---------------------------------------------------------

PERSON_B = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PERSON_B))


# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------

from data.imdaa_loader import load_imdaa
from storm_tracking.tracker import extract_storm_cells
from storm_tracking.motion import calculate_motion


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DATASET = "person-b/data/processed/imdaa_20200715.nc"

# Maximum allowed movement between two consecutive
# hourly frames, measured in grid cells.
MAX_DISTANCE = 5.0

# Minimum number of observations required for a
# track to be considered useful for forecasting.
MIN_OBSERVATIONS = 3


# ---------------------------------------------------------
# Storm detection
# ---------------------------------------------------------

def detect_storms(field):
    """
    Detect relatively strong precipitation cells.

    We currently use a percentile threshold because
    the final physical precipitation units have not
    yet been confirmed.
    """

    field = np.asarray(field, dtype=float)

    threshold = np.percentile(field, 90)

    storms = extract_storm_cells(
        field,
        threshold=threshold,
        min_area=2
    )

    return storms


# ---------------------------------------------------------
# One-to-one matching
# ---------------------------------------------------------

def match_storms_one_to_one(previous_storms, current_storms):
    """
    Match storm cells between two consecutive frames.

    A previous storm can match at most one current storm.
    A current storm can be assigned to at most one track.

    Returns:
        matches
        unmatched_previous
        unmatched_current
    """

    if not previous_storms or not current_storms:
        return (
            [],
            list(range(len(previous_storms))),
            list(range(len(current_storms)))
        )

    candidates = []

    # Calculate distance between every possible pair.
    for previous_index, previous in enumerate(previous_storms):

        for current_index, current in enumerate(current_storms):

            dx = (
                current["centroid_x"]
                - previous["centroid_x"]
            )

            dy = (
                current["centroid_y"]
                - previous["centroid_y"]
            )

            distance = float(
                np.sqrt(dx ** 2 + dy ** 2)
            )

            if distance <= MAX_DISTANCE:

                candidates.append(
                    (
                        distance,
                        previous_index,
                        current_index
                    )
                )

    # Closest pairs are assigned first.
    candidates.sort(key=lambda item: item[0])

    used_previous = set()
    used_current = set()

    matches = []

    for distance, previous_index, current_index in candidates:

        # Previous storm already matched.
        if previous_index in used_previous:
            continue

        # Current storm already claimed by another track.
        if current_index in used_current:
            continue

        matches.append(
            (
                previous_index,
                current_index,
                distance
            )
        )

        used_previous.add(previous_index)
        used_current.add(current_index)

    unmatched_previous = [
        index
        for index in range(len(previous_storms))
        if index not in used_previous
    ]

    unmatched_current = [
        index
        for index in range(len(current_storms))
        if index not in used_current
    ]

    return (
        matches,
        unmatched_previous,
        unmatched_current
    )


# ---------------------------------------------------------
# Build multi-frame tracks
# ---------------------------------------------------------

def build_tracks(fields):
    """
    Detect storm cells in all frames and connect them
    into multi-frame tracks.
    """

    # -----------------------------------------------------
    # Detect storms in every frame
    # -----------------------------------------------------

    all_storms = []

    for frame_index, frame in enumerate(fields):

        storms = detect_storms(frame.field)

        all_storms.append(storms)

        print(
            f"Frame {frame_index:02d}: "
            f"{len(storms)} storm cells"
        )

    # -----------------------------------------------------
    # Start tracks from first frame
    # -----------------------------------------------------

    tracks = []

    next_track_id = 1

    for storm in all_storms[0]:

        tracks.append(
            {
                "id": f"track_{next_track_id}",
                "observations": [
                    {
                        "frame": 0,
                        "timestamp": fields[0].timestamp,
                        "storm": storm
                    }
                ]
            }
        )

        next_track_id += 1

    # -----------------------------------------------------
    # Process remaining frames
    # -----------------------------------------------------

    for frame_index in range(1, len(fields)):

        current_storms = all_storms[frame_index]

        # Tracks that were alive in the immediately
        # previous frame.
        active_tracks = [
            track
            for track in tracks
            if track["observations"][-1]["frame"]
            == frame_index - 1
        ]

        previous_storms = [
            track["observations"][-1]["storm"]
            for track in active_tracks
        ]

        (
            matches,
            unmatched_previous,
            unmatched_current
        ) = match_storms_one_to_one(
            previous_storms,
            current_storms
        )

        # -------------------------------------------------
        # Extend existing tracks
        # -------------------------------------------------

        for (
            previous_index,
            current_index,
            distance
        ) in matches:

            track = active_tracks[previous_index]

            current_storm = current_storms[current_index]

            track["observations"].append(
                {
                    "frame": frame_index,
                    "timestamp": fields[frame_index].timestamp,
                    "storm": current_storm
                }
            )

        # -------------------------------------------------
        # Create new tracks for new storm cells
        # -------------------------------------------------

        for current_index in unmatched_current:

            current_storm = current_storms[current_index]

            tracks.append(
                {
                    "id": f"track_{next_track_id}",
                    "observations": [
                        {
                            "frame": frame_index,
                            "timestamp": fields[frame_index].timestamp,
                            "storm": current_storm
                        }
                    ]
                }
            )

            next_track_id += 1

    return tracks


# ---------------------------------------------------------
# Filter valid tracks
# ---------------------------------------------------------

def get_valid_tracks(
    tracks,
    minimum_observations=MIN_OBSERVATIONS
):
    """
    Keep only tracks with enough observations
    for meaningful motion estimation.
    """

    valid_tracks = [
        track
        for track in tracks
        if len(track["observations"])
        >= minimum_observations
    ]

    # Longest tracks first.
    valid_tracks.sort(
        key=lambda track: len(track["observations"]),
        reverse=True
    )

    return valid_tracks


# ---------------------------------------------------------
# Calculate track motion
# ---------------------------------------------------------

def calculate_track_motion(track):
    """
    Calculate overall motion using the first and last
    observation of a valid track.
    """

    observations = track["observations"]

    if len(observations) < 2:
        return None

    first = observations[0]
    last = observations[-1]

    first_storm = first["storm"]
    last_storm = last["storm"]

    frame_difference = (
        last["frame"]
        - first["frame"]
    )

    # IMDAA frames are hourly.
    elapsed_minutes = frame_difference * 60

    if elapsed_minutes <= 0:
        return None

    motion = calculate_motion(
        first_storm,
        last_storm,
        time_minutes=elapsed_minutes
    )

    return motion


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 70)
    print("ALERTORA - IMDAA MULTI-FRAME STORM TRACKING")
    print("=" * 70)

    # -----------------------------------------------------
    # Load real IMDAA data
    # -----------------------------------------------------

    print("\nLoading IMDAA dataset...")

    fields = load_imdaa(DATASET)

    print(
        f"Loaded {len(fields)} spatial frames."
    )

    # -----------------------------------------------------
    # Detect + track
    # -----------------------------------------------------

    print("\nDetecting storm cells...")

    tracks = build_tracks(fields)

    print("\n" + "=" * 70)
    print("TRACKING COMPLETE")
    print("=" * 70)

    print(
        f"\nTotal raw tracks: {len(tracks)}"
    )

    # -----------------------------------------------------
    # Filter short tracks
    # -----------------------------------------------------

    valid_tracks = get_valid_tracks(tracks)

    print(
        f"Valid tracks "
        f"(>= {MIN_OBSERVATIONS} observations): "
        f"{len(valid_tracks)}"
    )

    # -----------------------------------------------------
    # Track summary
    # -----------------------------------------------------

    print("\n" + "=" * 70)
    print("VALID STORM TRACKS")
    print("=" * 70)

    if not valid_tracks:

        print(
            "\nNo tracks contain enough observations "
            "for motion estimation."
        )

        return

    for track in valid_tracks:

        observations = track["observations"]

        first = observations[0]
        last = observations[-1]

        print("\n" + "-" * 70)

        print(
            f"Track ID: {track['id']}"
        )

        print(
            f"Observations: {len(observations)}"
        )

        print(
            f"Frame range: "
            f"{first['frame']} → {last['frame']}"
        )

        print(
            f"Time range: "
            f"{first['timestamp']} → {last['timestamp']}"
        )

        first_storm = first["storm"]
        last_storm = last["storm"]

        print(
            "Start position: "
            f"x={first_storm['centroid_x']:.2f}, "
            f"y={first_storm['centroid_y']:.2f}"
        )

        print(
            "End position: "
            f"x={last_storm['centroid_x']:.2f}, "
            f"y={last_storm['centroid_y']:.2f}"
        )

        motion = calculate_track_motion(track)

        if motion is not None:

            print(
                "Velocity: "
                f"vx={motion['vx']:.4f}, "
                f"vy={motion['vy']:.4f} grid/min"
            )

            print(
                "Speed: "
                f"{motion['speed_pixels_per_minute']:.4f} "
                "grid/min"
            )

            print(
                "Direction: "
                f"{motion['direction_degrees']:.2f} degrees"
            )

        else:

            print(
                "Motion: unavailable"
            )


if __name__ == "__main__":
    main()