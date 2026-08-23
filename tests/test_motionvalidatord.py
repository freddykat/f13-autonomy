from simulation.fake_bmw.fake_bmw import (
    motorway_curve,
    straight,
    with_dsc_intervention,
    with_stale_rear_steer,
)
from simulation.m0_types import PlannedMotion
from services.motionvalidatord.motionvalidatord import validate_motion


def test_straight_is_observing():
    bmw = straight(speed_mps=20.0)
    planned = PlannedMotion(0.0, 20.0, 0.0, 0.0, 0.0)
    result = validate_motion(planned, bmw)
    assert result.status == "OBSERVING"
    assert result.curvature_error_1pm == 0.0
    assert result.rear_steer_known is True


def test_stale_rear_steer_reduces_confidence_without_assuming_zero():
    bmw = with_stale_rear_steer(motorway_curve())
    planned = PlannedMotion(0.0, bmw.speed_mps, 0.0, 0.002, 0.055)
    result = validate_motion(planned, bmw)
    assert result.rear_steer_known is False
    assert result.confidence < 1.0


def test_dsc_intervention_is_reported_not_fought():
    bmw = with_dsc_intervention(motorway_curve())
    planned = PlannedMotion(0.0, bmw.speed_mps, 0.0, 0.002, 0.055)
    result = validate_motion(planned, bmw)
    assert result.status == "OEM_STABILITY_INTERVENTION"
    assert result.oem_stability_intervention is True
