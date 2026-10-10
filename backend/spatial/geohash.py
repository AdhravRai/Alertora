"""
ALERTORA AI — Pure Python Geohash Implementation
High-performance Base-32 Geohash encoding, decoding, bounding box extraction,
and spatial coverage calculation. Zero external binary dependencies required.
"""

from typing import Dict, List, Set, Tuple

_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"
_BASE32_MAP = {c: i for i, c in enumerate(_BASE32)}

# Direction tables for neighbor calculation
_NEIGHBORS = {
    "right": {
        "even": "bc01fg45238967deuvhjyznpkmstqrwx",
        "odd": "p0r21436x8zb9dcf5h7kjnmqesgutwvy",
    },
    "left": {
        "even": "238967debc01fg45kmstqrwxuvhjyznp",
        "odd": "14365h7k9dcfesgutwvyp0r21436x8zb",
    },
    "top": {
        "even": "p0r21436x8zb9dcf5h7kjnmqesgutwvy",
        "odd": "bc01fg45238967deuvhjyznpkmstqrwx",
    },
    "bottom": {
        "even": "14365h7k9dcfesgutwvyp0r21436x8zb",
        "odd": "238967debc01fg45kmstqrwxuvhjyznp",
    },
}

_BORDERS = {
    "right": {"even": "bcfguvyz", "odd": "prxz"},
    "left": {"even": "0145hjnp", "odd": "028b"},
    "top": {"even": "prxz", "odd": "bcfguvyz"},
    "bottom": {"even": "028b", "odd": "0145hjnp"},
}


def encode(lat: float, lon: float, precision: int = 6) -> str:
    """
    Encode latitude and longitude into a standard base32 geohash string.
    Precision 6 corresponds to approx ~1.2km x 0.6km cell.
    """
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]

    geohash = []
    bits = [16, 8, 4, 2, 1]
    bit = 0
    ch = 0
    is_even = True

    while len(geohash) < precision:
        if is_even:
            mid = (lon_interval[0] + lon_interval[1]) / 2.0
            if lon >= mid:
                ch |= bits[bit]
                lon_interval[0] = mid
            else:
                lon_interval[1] = mid
        else:
            mid = (lat_interval[0] + lat_interval[1]) / 2.0
            if lat >= mid:
                ch |= bits[bit]
                lat_interval[0] = mid
            else:
                lat_interval[1] = mid

        is_even = not is_even

        if bit < 4:
            bit += 1
        else:
            geohash.append(_BASE32[ch])
            bit = 0
            ch = 0

    return "".join(geohash)


def decode_bbox(geohash: str) -> Tuple[float, float, float, float]:
    """
    Decode geohash string into bounding box coordinates:
    Returns (min_lat, min_lon, max_lat, max_lon).
    """
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]
    is_even = True

    for c in geohash.lower():
        cd = _BASE32_MAP.get(c)
        if cd is None:
            raise ValueError(f"Invalid character '{c}' in geohash '{geohash}'")

        for mask in (16, 8, 4, 2, 1):
            if is_even:
                if cd & mask:
                    lon_interval[0] = (lon_interval[0] + lon_interval[1]) / 2.0
                else:
                    lon_interval[1] = (lon_interval[0] + lon_interval[1]) / 2.0
            else:
                if cd & mask:
                    lat_interval[0] = (lat_interval[0] + lat_interval[1]) / 2.0
                else:
                    lat_interval[1] = (lat_interval[0] + lat_interval[1]) / 2.0
            is_even = not is_even

    return (lat_interval[0], lon_interval[0], lat_interval[1], lon_interval[1])


def decode(geohash: str) -> Tuple[float, float]:
    """
    Decode geohash string to its center point (lat, lon).
    """
    min_lat, min_lon, max_lat, max_lon = decode_bbox(geohash)
    return ((min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0)


def adjacent(geohash: str, direction: str) -> str:
    """
    Find neighbor in a cardinal direction ('top', 'bottom', 'right', 'left').
    """
    if not geohash:
        return ""
    geohash = geohash.lower()
    last_char = geohash[-1]
    parent = geohash[:-1]
    type_key = "odd" if (len(geohash) % 2) == 1 else "even"

    # Border check
    if last_char in _BORDERS[direction][type_key] and parent:
        parent = adjacent(parent, direction)

    char_index = _NEIGHBORS[direction][type_key].index(last_char)
    return parent + _BASE32[char_index]


def neighbors(geohash: str) -> Dict[str, str]:
    """
    Returns the 8 surrounding geohash cells (N, S, E, W, NE, NW, SE, SW).
    """
    top = adjacent(geohash, "top")
    bottom = adjacent(geohash, "bottom")
    right = adjacent(geohash, "right")
    left = adjacent(geohash, "left")

    return {
        "n": top,
        "s": bottom,
        "e": right,
        "w": left,
        "ne": adjacent(top, "right"),
        "nw": adjacent(top, "left"),
        "se": adjacent(bottom, "right"),
        "sw": adjacent(bottom, "left"),
    }


def geohashes_for_bbox(
    min_lat: float, min_lon: float, max_lat: float, max_lon: float, precision: int = 6
) -> Set[str]:
    """
    Generate all unique geohashes of given precision covering the given bounding box.
    Iterates along a grid step computed from geohash cell dimension.
    """
    # Approximate cell dimensions by precision (degrees)
    # Precision 5: ~0.044 lat, ~0.088 lon
    # Precision 6: ~0.0055 lat, ~0.011 lon
    # Precision 7: ~0.00068 lat, ~0.0013 lon
    sample_hash = encode(min_lat, min_lon, precision)
    box = decode_bbox(sample_hash)
    lat_step = max((box[2] - box[0]) * 0.75, 0.0001)
    lon_step = max((box[3] - box[1]) * 0.75, 0.0001)

    result: Set[str] = set()
    current_lat = min_lat
    while current_lat <= max_lat + (lat_step * 0.5):
        current_lon = min_lon
        while current_lon <= max_lon + (lon_step * 0.5):
            result.add(encode(current_lat, current_lon, precision))
            current_lon += lon_step
        current_lat += lat_step

    # Ensure corners are explicitly covered
    result.add(encode(min_lat, min_lon, precision))
    result.add(encode(min_lat, max_lon, precision))
    result.add(encode(max_lat, min_lon, precision))
    result.add(encode(max_lat, max_lon, precision))

    return result
