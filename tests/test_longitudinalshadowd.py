from services.longitudinalshadowd.longitudinalshadowd import (
    BMWLongitudinalCapability,
    SpeedConstraint,
    effective_speed_limit,
    evaluate,
    stopping_distance_for_speed_change,
)


def cap(comfortable=1.5, maximum=4.0, delay=0.4, confidence=0.95):
    return BMWLongitudinalCapability(comfortable, maximum, delay, confidence)


def test_matrix_limit_overrides_higher_static_limit():
    target, reasons, confidence = effective_speed_limit(
        SpeedConstraint(27.78, "map", 0.95),      # 100 km/h
        SpeedConstraint(22.22, "matrix", 0.98),   # 80 km/h
    )
    assert round(target, 2) == 22.22
    assert reasons == ("LIMIT_FROM_MATRIX",)
    assert confidence == 0.98


def test_stale_matrix_is_ignored():
    target, reasons, _ = effective_speed_limit(
        SpeedConstraint(27.78, "map", 0.95),
        SpeedConstraint(16.67, "matrix", 0.99, stale=True),
    )
    assert round(target, 2) == 27.78
    assert reasons == ("LIMIT_FROM_MAP",)


def test_unknown_limits_fail_unknown_not_unlimited():
    target, reasons, confidence = effective_speed_limit(
        SpeedConstraint(None, "camera", 0.2),
    )
    assert target is None
    assert reasons == ("SPEED_LIMIT_UNKNOWN",)
    assert confidence == 0.0


def test_100_to_80_is_comfortably_feasible_with_distance():
    d = evaluate(
        current_speed_mps=27.78,
        distance_to_constraint_m=180.0,
        capability=cap(comfortable=1.5, maximum=4.0, delay=0.4),
        *[SpeedConstraint(22.22, "matrix", 0.98)],
    )
    assert d.target_speed_mps == 22.22
    assert d.feasible_comfortably is True
    assert d.feasible_max is True
    assert d.start_reducing_now is True


def test_short_distance_exceeds_comfort_margin():
    d = evaluate(
        current_speed_mps=27.78,
        distance_to_constraint_m=35.0,
        capability=cap(comfortable=1.2, maximum=4.0, delay=0.5),
        *[SpeedConstraint(16.67, "matrix", 0.98)],
    )
    assert d.feasible_comfortably is False
    assert "COMFORT_MARGIN_EXCEEDED" in d.reason_codes or "INSUFFICIENT_DECEL_DISTANCE" in d.reason_codes


def test_extremely_short_distance_can_be_physically_insufficient():
    d = evaluate(
        current_speed_mps=33.33,
        distance_to_constraint_m=10.0,
        capability=cap(comfortable=1.5, maximum=4.0, delay=0.8),
        *[SpeedConstraint(13.89, "matrix", 0.99)],
    )
    assert d.feasible_max is False
    assert "INSUFFICIENT_DECEL_DISTANCE" in d.reason_codes


def test_sport_response_delay_can_change_prediction_without_changing_legal_limit():
    comfort = evaluate(
        27.78, 70.0, cap(delay=0.9), SpeedConstraint(22.22, "matrix", 0.98)
    )
    sport = evaluate(
        27.78, 70.0, cap(delay=0.25), SpeedConstraint(22.22, "matrix", 0.98)
    )
    assert comfort.target_speed_mps == sport.target_speed_mps == 22.22
    assert sport.required_decel_mps2 <= comfort.required_decel_mps2


def test_distance_helper_accounts_for_delay():
    no_delay = stopping_distance_for_speed_change(27.78, 22.22, 1.5, 0.0)
    with_delay = stopping_distance_for_speed_change(27.78, 22.22, 1.5, 0.5)
    assert with_delay > no_delay
