from __future__ import annotations

from dataclasses import fields

from tools.bmw_transport_availability import (
    FunctionTransportSummary,
    _Correspondence,
    _Evidence,
    summarize_transport_availability,
)


def _evidence(
    family: str,
    transport: str,
    source: str,
    *,
    score: float = 0.90,
    confidence: str = "HIGH",
) -> _Evidence:
    return _Evidence(
        function_family=family,
        transport=transport,
        source_key=source,
        evidence_score=score,
        confidence=confidence,
    )


def test_can_only_evidence_prefers_can_first():
    summaries = summarize_transport_availability([
        _evidence("STEERING_LIKE", "CAN", "CAN|can0|291"),
    ], [])

    item = summaries[0]
    assert item.availability == "CAN_EVIDENCE_ONLY"
    assert item.observation_path == "CAN_FIRST"
    assert item.flexray_translation_need == "NOT_INDICATED_BY_CURRENT_EVIDENCE"


def test_flexray_only_evidence_marks_translation_likely_required():
    summaries = summarize_transport_availability([
        _evidence("YAW_LIKE", "FLEXRAY", "FLEXRAY|A|77|None|cycle|3"),
    ], [])

    item = summaries[0]
    assert item.availability == "FLEXRAY_EVIDENCE_ONLY"
    assert item.observation_path == "FLEXRAY_REQUIRED_FOR_OBSERVATION"
    assert item.flexray_translation_need == "LIKELY_REQUIRED_FOR_THIS_FUNCTION"


def test_strong_dual_transport_correspondence_allows_can_runtime_candidate():
    can_source = "CAN|can0|291"
    flex_source = "FLEXRAY|A|77|None|cycle|3"
    evidence = [
        _evidence("STEERING_LIKE", "CAN", can_source),
        _evidence("STEERING_LIKE", "FLEXRAY", flex_source),
    ]
    correspondence = [
        _Correspondence(
            function_family="STEERING_LIKE",
            can_source_key=can_source,
            flexray_source_key=flex_source,
            correspondence_score=0.98,
            relationship="STRONG_DUAL_TRANSPORT_CORRESPONDENCE",
            gateway_hypothesis="POSSIBLE_ZGW_FORWARD_OR_DERIVED_REPRESENTATION",
        )
    ]

    summaries = summarize_transport_availability(evidence, correspondence)

    item = summaries[0]
    assert item.availability == "DUAL_TRANSPORT_CORRELATED"
    assert item.observation_path == "CAN_MAY_SUFFICE_PENDING_DECODER_VALIDATION"
    assert item.flexray_translation_need == "POSSIBLY_OPTIONAL_FOR_RUNTIME_OBSERVATION"
    assert item.gateway_hypothesis == "POSSIBLE_ZGW_FORWARD_OR_DERIVED_REPRESENTATION"


def test_dual_transport_without_strong_correspondence_remains_unresolved():
    can_source = "CAN|can0|291"
    flex_source = "FLEXRAY|A|77|None|cycle|3"
    evidence = [
        _evidence("LEAD_RANGE_LIKE", "CAN", can_source),
        _evidence("LEAD_RANGE_LIKE", "FLEXRAY", flex_source),
    ]
    correspondence = [
        _Correspondence(
            function_family="LEAD_RANGE_LIKE",
            can_source_key=can_source,
            flexray_source_key=flex_source,
            correspondence_score=0.72,
            relationship="POSSIBLE_DUAL_TRANSPORT_CORRESPONDENCE",
            gateway_hypothesis="NOT_INFERRED",
        )
    ]

    summaries = summarize_transport_availability(evidence, correspondence)

    item = summaries[0]
    assert item.availability == "DUAL_TRANSPORT_UNRESOLVED"
    assert item.observation_path == "CAPTURE_BOTH_UNTIL_CORROBORATED"
    assert item.flexray_translation_need == "UNRESOLVED"


def test_low_confidence_or_low_score_evidence_is_insufficient():
    evidence = [
        _evidence(
            "ACC_ACTIVE_STATE_LIKE",
            "CAN",
            "CAN|can0|500",
            score=0.95,
            confidence="LOW",
        ),
        _evidence(
            "ACC_ACTIVE_STATE_LIKE",
            "FLEXRAY",
            "FLEXRAY|A|88|None|cycle|1",
            score=0.50,
            confidence="MEDIUM",
        ),
    ]

    summaries = summarize_transport_availability(evidence, [])

    item = summaries[0]
    assert item.availability == "INSUFFICIENT_EVIDENCE"
    assert item.flexray_translation_need == "UNRESOLVED"


def test_best_transport_candidate_is_used_per_family():
    evidence = [
        _evidence("BRAKE_STATE_LIKE", "CAN", "CAN|can0|100", score=0.70, confidence="MEDIUM"),
        _evidence("BRAKE_STATE_LIKE", "CAN", "CAN|can0|101", score=0.92, confidence="HIGH"),
    ]

    summaries = summarize_transport_availability(evidence, [])

    item = summaries[0]
    assert item.can_source_key == "CAN|can0|101"
    assert item.can_evidence_score == 0.92


def test_summary_has_no_control_or_decoder_authority_fields():
    names = {field.name for field in fields(FunctionTransportSummary)}
    forbidden = {
        "command",
        "actuation",
        "decoder",
        "scale",
        "offset",
        "unit",
        "sendcan",
        "tx",
        "carState",
        "radarData",
    }

    assert forbidden.isdisjoint(names)
    assert FunctionTransportSummary.__dataclass_fields__["status"].default == (
        "UNVALIDATED_TRANSPORT_AVAILABILITY"
    )
