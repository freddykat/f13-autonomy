from services.degradationd.degradationd import (
    CapabilityMode,
    Health,
    SensorHealthState,
    evaluate,
)


def healthy(**overrides):
    data = dict(
        cameras=Health.OK,
        radar=Health.OK,
        bmw_buses=Health.OK,
        imu=Health.OK,
        gnss=Health.OK,
        traffic_control=Health.OK,
        driver_monitoring=Health.OK,
    )
    data.update(overrides)
    return SensorHealthState(**data)


def test_all_healthy_full_shadow():
    d = evaluate(healthy())
    assert d.mode == CapabilityMode.FULL_SHADOW


def test_radar_failure_degrades_but_does_not_stop_if_cameras_work():
    d = evaluate(healthy(radar=Health.FAILED))
    assert d.mode == CapabilityMode.PARTIAL_SHADOW
    assert "RADAR_FAILED" in d.reason_codes


def test_camera_failure_with_radar_still_available_is_minimal():
    d = evaluate(healthy(cameras=Health.FAILED))
    assert d.mode == CapabilityMode.MINIMAL_SHADOW


def test_camera_and_radar_failure_recommends_takeover():
    d = evaluate(healthy(cameras=Health.FAILED, radar=Health.FAILED))
    assert d.mode == CapabilityMode.TAKEOVER_RECOMMENDED
    assert "PRIMARY_PERCEPTION_LOST" in d.reason_codes


def test_bmw_bus_loss_recommends_takeover():
    d = evaluate(healthy(bmw_buses=Health.UNKNOWN))
    assert d.mode == CapabilityMode.TAKEOVER_RECOMMENDED


def test_imu_loss_recommends_takeover():
    d = evaluate(healthy(imu=Health.FAILED))
    assert d.mode == CapabilityMode.TAKEOVER_RECOMMENDED


def test_traffic_control_failure_reduces_capability():
    d = evaluate(healthy(traffic_control=Health.FAILED))
    assert d.mode == CapabilityMode.MINIMAL_SHADOW


def test_gnss_loss_only_degrades_shadow():
    d = evaluate(healthy(gnss=Health.FAILED))
    assert d.mode == CapabilityMode.PARTIAL_SHADOW


def test_driver_monitoring_loss_degrades_supervised_mode():
    d = evaluate(healthy(driver_monitoring=Health.FAILED))
    assert d.mode == CapabilityMode.PARTIAL_SHADOW
