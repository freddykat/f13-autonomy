from tools.bmw_signal_correlation import Frame, Marker
from tools.bmw_continuous_signal_correlation import rank_continuous_candidates


def _frame(t, value, address=0x321, bus="can0"):
    raw = int(value).to_bytes(2, byteorder="big", signed=True) + b"\x00\x00"
    return Frame(t=t, bus=bus, address=address, data=raw)


def test_signed_big_endian_steering_candidate_ranks_high_for_repeated_left_turns():
    frames = []
    markers = []
    for base in (10.0, 20.0, 30.0):
        markers.append(Marker(base, "STEER_LEFT_SLOW"))
        frames += [
            _frame(base - 0.8, 0),
            _frame(base - 0.2, 20),
            _frame(base + 0.2, 300),
            _frame(base + 0.8, 500),
        ]

    ranked = rank_continuous_candidates(
        frames,
        markers,
        expected_direction={"STEER_LEFT_SLOW": +1},
    )
    matching = [c for c in ranked if c.address == 0x321 and c.start_byte == 0 and c.width == 2 and c.signed and c.endian == "big"]
    assert matching
    top = matching[0]
    assert top.observations == 3
    assert top.mean_delta > 0
    assert top.sign_consistency == 1.0
    assert top.direction_match == 1.0
    assert top.score > 0.85


def test_wrong_direction_is_penalized():
    frames = []
    markers = []
    for base in (10.0, 20.0):
        markers.append(Marker(base, "LEAD_CLOSING"))
        frames += [
            _frame(base - 0.5, 1000),
            _frame(base + 0.5, 700),
        ]

    ranked = rank_continuous_candidates(
        frames,
        markers,
        expected_direction={"LEAD_CLOSING": +1},
    )
    candidate = next(c for c in ranked if c.start_byte == 0 and c.width == 2 and c.signed and c.endian == "big")
    assert candidate.mean_delta < 0
    assert candidate.direction_match == 0.0
    assert candidate.score < 0.7


def test_little_endian_interpretations_are_considered_for_multibyte_fields():
    frames = []
    markers = []
    for base in (5.0, 15.0):
        markers.append(Marker(base, "YAW_LEFT"))
        before = (100).to_bytes(2, "little", signed=True) + b"\x00"
        after = (900).to_bytes(2, "little", signed=True) + b"\x00"
        frames += [Frame(base - 0.3, "can1", 0x444, before), Frame(base + 0.3, "can1", 0x444, after)]

    ranked = rank_continuous_candidates(frames, markers, expected_direction={"YAW_LEFT": +1})
    assert any(c.address == 0x444 and c.start_byte == 0 and c.width == 2 and c.endian == "little" for c in ranked)


def test_no_semantic_or_decoder_promotion_fields_exist():
    frames = []
    markers = []
    for base in (5.0, 15.0):
        markers.append(Marker(base, "ACCEL_LIGHT"))
        frames += [_frame(base - 0.2, 0), _frame(base + 0.2, 250)]

    candidate = rank_continuous_candidates(frames, markers)[0]
    assert not hasattr(candidate, "decoder")
    assert not hasattr(candidate, "scale")
    assert not hasattr(candidate, "unit")
    assert not hasattr(candidate, "command")
    assert not hasattr(candidate, "actuation")


def test_invalid_width_is_rejected():
    frames = [_frame(0.0, 0), _frame(1.0, 1)]
    markers = [Marker(0.5, "TEST"), Marker(0.75, "TEST")]
    try:
        rank_continuous_candidates(frames, markers, widths=(4,))
    except ValueError:
        pass
    else:
        raise AssertionError("width 4 should be rejected")
