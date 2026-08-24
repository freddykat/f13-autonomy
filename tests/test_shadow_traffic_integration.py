from services.shadowplannerd.shadowplannerd import Action
from services.shadowplannerd.traffic_integration import TrafficControlSummary, plan_with_traffic_control


def test_red_light_stops():
    d = plan_with_traffic_control(
        TrafficControlSummary(must_stop=True),
        left_safe=True,
        right_safe=True,
    )
    assert d.action == Action.STOP


def test_red_x_moves_left_when_safe():
    d = plan_with_traffic_control(
        TrafficControlSummary(current_lane_closed=True),
        left_safe=True,
        right_safe=False,
    )
    assert d.action == Action.LEFT


def test_red_x_moves_right_when_left_unsafe():
    d = plan_with_traffic_control(
        TrafficControlSummary(current_lane_closed=True),
        left_safe=False,
        right_safe=True,
    )
    assert d.action == Action.RIGHT


def test_red_x_slows_if_no_safe_gap():
    d = plan_with_traffic_control(
        TrafficControlSummary(current_lane_closed=True),
        left_safe=False,
        right_safe=False,
    )
    assert d.action == Action.SLOW


def test_matrix_merge_waits_if_target_lane_unsafe():
    d = plan_with_traffic_control(
        TrafficControlSummary(requested_merge=Action.LEFT),
        left_safe=False,
        right_safe=True,
    )
    assert d.action == Action.KEEP


def test_stale_control_never_authorizes_manoeuvre():
    d = plan_with_traffic_control(
        TrafficControlSummary(current_lane_closed=True, stale=True),
        left_safe=True,
        right_safe=True,
    )
    assert d.action == Action.WAIT


def test_low_confidence_control_waits():
    d = plan_with_traffic_control(
        TrafficControlSummary(requested_merge=Action.RIGHT, confidence=0.4),
        left_safe=True,
        right_safe=True,
    )
    assert d.action == Action.WAIT
