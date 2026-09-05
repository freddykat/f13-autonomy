from tools.bmw_relational_signal_correlation import RelationSpec, rank_relational_candidates
from tools.bmw_signal_correlation import Frame, Marker


def _frame(t: float, value: int, *, bus: str = "can0", address: int = 0x123) -> Frame:
    payload = int(value).to_bytes(2, byteorder="big", signed=True) + b"\x00" * 6
    return Frame(t=t, bus=bus, address=address, data=payload)


def _steering_trace():
    frames = [
        _frame(0.2, 0), _frame(0.8, 0),
        _frame(1.2, 120), _frame(1.8, 120),
        _frame(2.2, 0), _frame(2.8, 0),
        _frame(3.2, -120), _frame(3.8, -120),
        _frame(4.2, 0), _frame(4.8, 0),
        _frame(5.2, 100), _frame(5.8, 100),
        _frame(6.2, 0), _frame(6.8, 0),
        _frame(7.2, -100), _frame(7.8, -100),
        _frame(8.2, 0), _frame(8.8, 0),
    ]
    markers = [
        Marker(t=1.0, event="STEER_LEFT_SLOW"),
        Marker(t=2.0, event="STEER_CENTER"),
        Marker(t=3.0, event="STEER_RIGHT_SLOW"),
        Marker(t=4.0, event="STEER_CENTER"),
        Marker(t=5.0, event="STEER_LEFT_SLOW"),
        Marker(t=6.0, event="STEER_CENTER"),
        Marker(t=7.0, event="STEER_RIGHT_SLOW"),
        Marker(t=8.0, event="STEER_CENTER"),
    ]
    return frames, markers


def test_true_steering_candidate_wins_across_left_right_center():
    frames, markers = _steering_trace()
    relation = RelationSpec(
        name="steering_opposition",
        positive_event="STEER_LEFT_SLOW",
        negative_event="STEER_RIGHT_SLOW",
        baseline_event="STEER_CENTER",
    )
    ranked = rank_relational_candidates(
        frames,
        markers,
        [relation],
        before_s=0.8,
        after_s=0.8,
        min_observations=2,
        widths=(2,),
    )
    best = ranked[0]
    assert best.bus == "can0"
    assert best.address == 0x123
    assert best.start_byte == 0
    assert best.width == 2
    assert best.signed is True
    assert best.endian == "big"
    assert best.opposite_direction_score == 1.0
    assert best.baseline_recovery_score > 0.95
    assert best.score > 0.95


def test_same_direction_left_right_is_penalized():
    frames = [
        _frame(0.2, 0), _frame(0.8, 0), _frame(1.2, 100), _frame(1.8, 100),
        _frame(2.2, 0), _frame(2.8, 0), _frame(3.2, 80), _frame(3.8, 80),
        _frame(4.2, 0), _frame(4.8, 0), _frame(5.2, 110), _frame(5.8, 110),
        _frame(6.2, 0), _frame(6.8, 0), _frame(7.2, 90), _frame(7.8, 90),
    ]
    markers = [
        Marker(1.0, "LEFT"), Marker(3.0, "RIGHT"),
        Marker(5.0, "LEFT"), Marker(7.0, "RIGHT"),
    ]
    relation = RelationSpec("opposed", "LEFT", "RIGHT")
    ranked = rank_relational_candidates(
        frames, markers, [relation], before_s=0.8, after_s=0.8,
        min_observations=2, widths=(2,),
    )
    target = next(c for c in ranked if c.start_byte == 0 and c.signed and c.endian == "big")
    assert target.opposite_direction_score <= 0.5
    assert target.score < 0.8


def test_failure_to_return_to_baseline_is_penalized():
    frames, markers = _steering_trace()
    # Replace center post-event samples with a value far from the midpoint.
    frames = [
        _frame(f.t, 300 if any(abs(f.t - x) < 0.25 for x in (2.2, 2.8, 4.2, 4.8, 6.2, 6.8, 8.2, 8.8)) else int.from_bytes(f.data[:2], "big", signed=True))
        for f in frames
    ]
    relation = RelationSpec("steering", "STEER_LEFT_SLOW", "STEER_RIGHT_SLOW", "STEER_CENTER")
    ranked = rank_relational_candidates(
        frames, markers, [relation], before_s=0.8, after_s=0.8,
        min_observations=2, widths=(2,),
    )
    target = next(c for c in ranked if c.start_byte == 0 and c.signed and c.endian == "big")
    assert target.baseline_recovery_score < 0.5
    assert target.score < 0.9


def test_bus_identity_remains_separate():
    frames, markers = _steering_trace()
    frames += [_frame(f.t, int.from_bytes(f.data[:2], "big", signed=True), bus="can1") for f in frames]
    relation = RelationSpec("steering", "STEER_LEFT_SLOW", "STEER_RIGHT_SLOW", "STEER_CENTER")
    ranked = rank_relational_candidates(
        frames, markers, [relation], before_s=0.8, after_s=0.8,
        min_observations=2, widths=(2,),
    )
    buses = {c.bus for c in ranked if c.start_byte == 0 and c.signed and c.endian == "big"}
    assert {"can0", "can1"}.issubset(buses)


def test_candidate_has_no_semantic_decoder_or_actuation_fields():
    frames, markers = _steering_trace()
    relation = RelationSpec("steering", "STEER_LEFT_SLOW", "STEER_RIGHT_SLOW", "STEER_CENTER")
    candidate = rank_relational_candidates(
        frames, markers, [relation], before_s=0.8, after_s=0.8,
        min_observations=2, widths=(2,),
    )[0]
    for forbidden in ("decoder", "scale", "unit", "command", "actuation", "semantic"):
        assert not hasattr(candidate, forbidden)
