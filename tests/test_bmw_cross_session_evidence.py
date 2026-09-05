from __future__ import annotations

from dataclasses import fields

from tools.bmw_cross_session_evidence import (
    BMWFunctionEvidence,
    SessionHypothesis,
    aggregate_function_evidence,
)


def _hypothesis(
    session_id: str,
    *,
    transport: str = "FLEXRAY",
    source_key: str = "FLEXRAY|A|77|None|cycle|3",
    score: float = 0.95,
    polarity: str = "positive_event_raw_positive",
    function_family: str = "STEERING_LIKE",
    slot_id: int | None = 77,
    bus: str | None = None,
    address: int | None = None,
) -> SessionHypothesis:
    return SessionHypothesis(
        session_id=session_id,
        function_family=function_family,
        function_kind="opposed_continuous",
        transport=transport,
        source_key=source_key,
        feature_kind="continuous_integer",
        start_byte=0,
        width=2,
        bit=None,
        signed=True,
        endian="big",
        score=score,
        direction_score=1.0,
        baseline_score=0.95,
        transition_strength=0.2,
        coverage_score=1.0,
        raw_polarity=polarity,
        slot_id=slot_id,
        bus=bus,
        address=address,
    )


def test_repeated_candidate_across_three_sessions_reaches_high_confidence():
    sessions = [
        ("run001", [_hypothesis("run001", score=0.94)]),
        ("run002", [_hypothesis("run002", score=0.96)]),
        ("run003", [_hypothesis("run003", score=0.95)]),
    ]

    evidence = aggregate_function_evidence(sessions)

    top = evidence[0]
    assert top.function_family == "STEERING_LIKE"
    assert top.transport == "FLEXRAY"
    assert top.slot_id == 77
    assert top.sessions_observed == 3
    assert top.sessions_total == 3
    assert top.session_coverage == 1.0
    assert top.polarity_consistency == 1.0
    assert top.confidence == "HIGH"
    assert top.status == "UNVALIDATED_CROSS_SESSION_EVIDENCE"


def test_one_session_candidate_cannot_be_high_confidence():
    sessions = [
        ("run001", [_hypothesis("run001", score=0.99)]),
        ("run002", []),
        ("run003", []),
    ]

    evidence = aggregate_function_evidence(sessions)

    assert evidence[0].sessions_observed == 1
    assert evidence[0].session_coverage == 1 / 3
    assert evidence[0].confidence == "LOW"


def test_polarity_disagreement_blocks_high_confidence():
    sessions = [
        ("run001", [_hypothesis("run001", polarity="positive_event_raw_positive")]),
        ("run002", [_hypothesis("run002", polarity="positive_event_raw_positive")]),
        ("run003", [_hypothesis("run003", polarity="positive_event_raw_negative")]),
    ]

    evidence = aggregate_function_evidence(sessions)

    assert evidence[0].sessions_observed == 3
    assert evidence[0].polarity_consistency == 2 / 3
    assert evidence[0].confidence != "HIGH"


def test_can_and_flexray_evidence_remain_separate():
    can = _hypothesis(
        "run001",
        transport="CAN",
        source_key="CAN|can0|291",
        slot_id=None,
        bus="can0",
        address=291,
    )
    flexray = _hypothesis("run001")

    sessions = [
        ("run001", [can, flexray]),
        (
            "run002",
            [
                _hypothesis(
                    "run002",
                    transport="CAN",
                    source_key="CAN|can0|291",
                    slot_id=None,
                    bus="can0",
                    address=291,
                ),
                _hypothesis("run002"),
            ],
        ),
    ]

    evidence = aggregate_function_evidence(sessions)

    transports = {item.transport for item in evidence}
    assert transports == {"CAN", "FLEXRAY"}
    assert len(evidence) == 2


def test_duplicate_same_session_keeps_best_hypothesis_only():
    weak = _hypothesis("run001", score=0.55)
    strong = _hypothesis("run001", score=0.95)

    evidence = aggregate_function_evidence([
        ("run001", [weak, strong]),
        ("run002", [_hypothesis("run002", score=0.90)]),
    ])

    top = evidence[0]
    assert top.sessions_observed == 2
    assert top.mean_score == (0.95 + 0.90) / 2


def test_minimum_score_filter_removes_weak_session_hit():
    sessions = [
        ("run001", [_hypothesis("run001", score=0.95)]),
        ("run002", [_hypothesis("run002", score=0.30)]),
        ("run003", [_hypothesis("run003", score=0.93)]),
    ]

    evidence = aggregate_function_evidence(sessions, minimum_hypothesis_score=0.5)

    assert evidence[0].sessions_observed == 2
    assert evidence[0].sessions_total == 3
    assert evidence[0].session_coverage == 2 / 3


def test_cross_session_evidence_has_no_decoder_or_control_fields():
    names = {field.name for field in fields(BMWFunctionEvidence)}
    forbidden = {
        "command",
        "actuation",
        "decoder",
        "scale",
        "offset",
        "unit",
        "sendcan",
        "tx",
        "radarData",
        "carState",
    }

    assert forbidden.isdisjoint(names)
    assert BMWFunctionEvidence.__dataclass_fields__["status"].default == (
        "UNVALIDATED_CROSS_SESSION_EVIDENCE"
    )
