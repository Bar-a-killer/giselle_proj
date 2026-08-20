import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points, in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def venue_distance_km(
    user_lat: float | None, user_lon: float | None, venue_lat: float | None, venue_lon: float | None
) -> float | None:
    if user_lat is None or user_lon is None or venue_lat is None or venue_lon is None:
        return None
    return haversine_km(user_lat, user_lon, venue_lat, venue_lon)
