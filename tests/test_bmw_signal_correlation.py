from tools.bmw_signal_correlation import Frame, Marker, rank_candidates


def _frame(t, value, address=0x123):
    return Frame(t=t, bus="can0", address=address, data=bytes([value, 0, 0, 0]))


def test_repeated_binary_transition_ranks_expected_bit_first():
    frames = []
    markers = []
    # Two BLIND_LEFT_ENTER events. bit 0 changes 0 -> 1 around each marker.
    for base in (10.0, 20.0):
        markers.append(Marker(base, "BLIND_LEFT_ENTER"))
        frames += [
            _frame(base - 0.8, 0x00),
            _frame(base - 0.3, 0x00),
            _frame(base + 0.2, 0x01),
            _frame(base + 0.7, 0x01),
        ]

    ranked = rank_candidates(frames, markers, before_s=1.0, after_s=1.0, min_observations=2)
    top = ranked[0]
    assert top.event == "BLIND_LEFT_ENTER"
    assert top.address == 0x123
    assert top.byte == 0
    assert top.bit == 0
    assert top.kind == "bit"
    assert top.score == 1.0
    assert top.observations == 2


def test_one_off_change_is_rejected_by_min_observations():
    frames = [_frame(9.5, 0), _frame(10.5, 1)]
    markers = [Marker(10.0, "ACC_ON")]
    ranked = rank_candidates(frames, markers, min_observations=2)
    assert ranked == []


def test_analyzer_does_not_assign_semantics_or_actuation():
    frames = []
    markers = []
    for base in (5.0, 15.0):
        markers.append(Marker(base, "LEAD_ACQUIRE"))
        frames += [_frame(base - 0.2, 10), _frame(base + 0.2, 50)]
    ranked = rank_candidates(frames, markers)
    assert ranked
    # Output candidates are raw evidence only: no control or decoder fields exist.
    candidate = ranked[0]
    assert not hasattr(candidate, "decoder")
    assert not hasattr(candidate, "command")
    assert not hasattr(candidate, "actuation")


def test_separates_same_address_on_different_buses():
    markers = [Marker(10.0, "STEER_LEFT_SLOW"), Marker(20.0, "STEER_LEFT_SLOW")]
    frames = []
    for base in (10.0, 20.0):
        frames += [
            Frame(base - 0.2, "can0", 0x222, bytes([0])),
            Frame(base + 0.2, "can0", 0x222, bytes([1])),
            Frame(base - 0.2, "can1", 0x222, bytes([100])),
            Frame(base + 0.2, "can1", 0x222, bytes([100])),
        ]
    ranked = rank_candidates(frames, markers)
    assert ranked[0].bus == "can0"
