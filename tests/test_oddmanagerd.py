from services.oddmanagerd.oddmanagerd import ODDInput, ODDMode, classify


def base(**kwargs):
    d = dict(
        road_type="MOTORWAY",
        route_active=True,
        sensors_ok=True,
        driver_monitoring_ok=True,
        visibility_ok=True,
        severe_weather=False,
        traffic_control_confident=True,
        jurisdiction_known=True,
        highway_validated=True,
    )
    d.update(kwargs)
    return ODDInput(**d)


def test_highway_supervised_requires_route():
    assert classify(base(route_active=True)).mode == ODDMode.HIGHWAY_SUPERVISED
    assert classify(base(route_active=False)).mode == ODDMode.PARTIAL_AUTOPILOT


def test_sensor_failure_forces_manual():
    d = classify(base(sensors_ok=False))
    assert d.mode == ODDMode.MANUAL_ONLY


def test_driver_monitoring_failure_forces_manual():
    d = classify(base(driver_monitoring_ok=False))
    assert d.mode == ODDMode.MANUAL_ONLY


def test_severe_weather_is_shadow_only():
    d = classify(base(severe_weather=True))
    assert d.mode == ODDMode.SHADOW_ONLY


def test_unknown_visibility_is_shadow_only():
    d = classify(base(visibility_ok=None))
    assert d.mode == ODDMode.SHADOW_ONLY


def test_unknown_jurisdiction_is_shadow_only():
    d = classify(base(jurisdiction_known=False))
    assert d.mode == ODDMode.SHADOW_ONLY


def test_unvalidated_highway_does_not_get_highway_supervised():
    d = classify(base(highway_validated=False))
    assert d.mode == ODDMode.PARTIAL_AUTOPILOT


def test_uncertain_traffic_control_blocks_highway_supervised():
    d = classify(base(traffic_control_confident=False))
    assert d.mode == ODDMode.PARTIAL_AUTOPILOT
