from app.services.geo import haversine_km, venue_distance_km


def test_haversine_same_point_is_zero():
    assert haversine_km(47.6062, -122.3321, 47.6062, -122.3321) == 0.0


def test_haversine_known_distance():
    # Seattle Space Needle -> Pike Place Market, roughly 1.3 km apart
    d = haversine_km(47.6205, -122.3493, 47.6097, -122.3422)
    assert 1.0 < d < 1.8


def test_venue_distance_km_returns_none_when_any_coordinate_missing():
    assert venue_distance_km(None, None, 47.6, -122.3) is None
    assert venue_distance_km(47.6, -122.3, None, None) is None
    assert venue_distance_km(47.6, -122.3, 47.6, None) is None


def test_venue_distance_km_computes_when_all_present():
    d = venue_distance_km(47.6205, -122.3493, 47.6097, -122.3422)
    assert d is not None
    assert 1.0 < d < 1.8
