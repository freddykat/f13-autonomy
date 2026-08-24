from services.trafficcontrold.trafficcontrold import (
    LaneControlState, LightState, Observation, SignalKind, evaluate,
)


def test_red_light_requires_stop():
    c = evaluate(Observation(1, SignalKind.TRAFFIC_LIGHT, 0.99, light_state=LightState.RED))
    assert c.must_stop
    assert c.reason == "RED_LIGHT"


def test_green_light_does_not_force_stop():
    c = evaluate(Observation(1, SignalKind.TRAFFIC_LIGHT, 0.99, light_state=LightState.GREEN))
    assert not c.must_stop
    assert not c.uncertain


def test_red_x_closes_lane():
    c = evaluate(Observation(1, SignalKind.LANE_CONTROL, 0.98, lane_id="L2", lane_control=LaneControlState.CLOSED))
    assert c.lane_closed
    assert c.lane_id == "L2"


def test_merge_arrow_is_lane_specific():
    c = evaluate(Observation(1, SignalKind.LANE_CONTROL, 0.97, lane_id="L3", lane_control=LaneControlState.MERGE_LEFT))
    assert c.merge_direction == "LEFT"
    assert c.lane_id == "L3"


def test_variable_speed_limit():
    c = evaluate(Observation(1, SignalKind.VARIABLE_SPEED, 0.96, lane_id="L1", speed_limit_kph=80))
    assert c.speed_limit_kph == 80


def test_missing_detection_is_not_treated_as_open():
    c = evaluate(Observation(1, SignalKind.LANE_CONTROL, 0.95, lane_id="L2", lane_control=LaneControlState.UNKNOWN))
    assert c.uncertain


def test_low_confidence_fails_uncertain():
    c = evaluate(Observation(1, SignalKind.TRAFFIC_LIGHT, 0.40, light_state=LightState.GREEN))
    assert c.uncertain


def test_stale_signal_fails_uncertain():
    c = evaluate(Observation(1, SignalKind.VARIABLE_SPEED, 0.99, speed_limit_kph=70, stale=True))
    assert c.uncertain
