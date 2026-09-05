from tools.bmw_frr_track_hypotheses import (
    FRRTrackHypothesis,
    RawFieldRef,
    TrackFieldCandidate,
    build_track_hypotheses,
)


def ref(bus, address, start, width=2, signed=False, endian="big"):
    return RawFieldRef(bus, address, start, width, signed, endian)


def test_complete_same_message_hypothesis_ranks_high():
    r = TrackFieldCandidate(ref("can0", 0x123, 0), "range", 0.96, 8)
    v = TrackFieldCandidate(ref("can0", 0x123, 2, signed=True), "velocity", 0.94, 8)
    opt = [
        TrackFieldCandidate(ref("can0", 0x123, 4, 1), "validity", 0.9, 8),
        TrackFieldCandidate(ref("can0", 0x123, 5, 1, True), "lateral", 0.85, 8),
        TrackFieldCandidate(ref("can0", 0x123, 6, 1), "track_id", 0.8, 8),
    ]
    h = build_track_hypotheses([r], [v], opt)[0]
    assert h.role_count == 5
    assert h.evidence_coverage == 1.0
    assert h.same_bus_score == 1.0
    assert h.same_address_score == 1.0
    assert h.score > 0.9


def test_cross_bus_pair_is_penalized_not_forbidden():
    r = TrackFieldCandidate(ref("can0", 0x123, 0), "range", 0.9, 5)
    same = TrackFieldCandidate(ref("can0", 0x124, 0), "velocity", 0.9, 5)
    cross = TrackFieldCandidate(ref("can1", 0x124, 0), "velocity", 0.9, 5)
    hs = build_track_hypotheses([r], [same, cross])
    assert hs[0].velocity_field.bus == "can0"
    assert hs[0].score > hs[1].score


def test_optional_roles_are_not_required():
    r = TrackFieldCandidate(ref("can0", 0x123, 0), "range", 0.8, 4)
    v = TrackFieldCandidate(ref("can0", 0x123, 2), "velocity", 0.8, 4)
    h = build_track_hypotheses([r], [v])[0]
    assert h.role_count == 2
    assert h.validity_field is None
    assert h.lateral_field is None
    assert h.track_id_field is None


def test_unknown_roles_are_ignored():
    r = TrackFieldCandidate(ref("can0", 1, 0), "range", 0.8, 4)
    v = TrackFieldCandidate(ref("can0", 1, 2), "velocity", 0.8, 4)
    junk = TrackFieldCandidate(ref("can0", 1, 4), "checksum", 1.0, 99)
    h = build_track_hypotheses([r], [v], [junk])[0]
    assert h.role_count == 2


def test_safety_boundary_is_explicit():
    fields = set(FRRTrackHypothesis.__dataclass_fields__)
    assert "auto_promote" in fields
    assert "actuation" in fields
    assert "command" not in fields
    assert "dbc" not in fields
    r = TrackFieldCandidate(ref("can0", 1, 0), "range", 0.8, 3)
    v = TrackFieldCandidate(ref("can0", 1, 2), "velocity", 0.8, 3)
    h = build_track_hypotheses([r], [v])[0]
    assert h.mode == "OFFLINE_READ_ONLY_DISCOVERY"
    assert h.auto_promote is False
    assert h.actuation == "NONE"
