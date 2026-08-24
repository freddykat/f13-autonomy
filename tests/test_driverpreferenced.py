from services.driverpreferenced.driverpreferenced import (
    DriverPreferenceProfile, Observation, preference_score, update,
)


def test_safe_legal_left_action_increases_overtake_bias():
    p0 = DriverPreferenceProfile()
    p1 = update(p0, Observation("LEFT", True, True, True))
    assert p1.overtake_bias > p0.overtake_bias
    assert p1.sample_count == 1


def test_illegal_action_is_not_learned():
    p0 = DriverPreferenceProfile()
    p1 = update(p0, Observation("LEFT", False, True, True))
    assert p1 == p0


def test_unsafe_action_is_not_learned():
    p0 = DriverPreferenceProfile()
    p1 = update(p0, Observation("RIGHT", True, False, True))
    assert p1 == p0


def test_vehicle_incapable_action_is_not_learned():
    p0 = DriverPreferenceProfile()
    p1 = update(p0, Observation("LEFT", True, True, False))
    assert p1 == p0


def test_following_gap_updates_gradually():
    p0 = DriverPreferenceProfile(following_time_gap_s=2.0)
    p1 = update(p0, Observation("KEEP", True, True, True, following_time_gap_s=2.5))
    assert 2.0 < p1.following_time_gap_s < 2.5


def test_aggressiveness_is_bounded():
    p0 = DriverPreferenceProfile()
    p1 = update(p0, Observation("KEEP", True, True, True, longitudinal_aggressiveness=5.0))
    assert 0.5 < p1.longitudinal_aggressiveness <= 1.0


def test_preference_score_only_biases_soft_choice():
    p = DriverPreferenceProfile(overtake_bias=0.8, return_right_bias=0.6)
    assert preference_score(p, "LEFT") == 0.8
    assert preference_score(p, "RIGHT") == 0.6
    assert preference_score(p, "KEEP") == 0.2
