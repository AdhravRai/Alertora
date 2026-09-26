def is_inside_domain(lat, lon, latitudes, longitudes):
    return (
        float(latitudes.min()) <= lat <= float(latitudes.max())
        and
        float(longitudes.min()) <= lon <= float(longitudes.max())
    )