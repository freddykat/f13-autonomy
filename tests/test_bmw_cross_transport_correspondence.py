from __future__ import annotations

from dataclasses import fields

from tools.bmw_cross_transport_correspondence import (
    CrossTransportCorrespondence,
    EvidenceField,
    rank_cross_transport_correspondence,
)
from tools.bmw_transport import BMWTransportFrame, TransportIdentity


def _field(
    *,
    transport: str,
    source_key: str,
    evidence_score: float = 0.95,
    function_family: str = "STEERING_LIKE",
    bus: str | None = None,
    address: int | None = None,
    channel: str | None = None,
    slot_id: int | None = None,
    cycle: int | None = None,
) -> EvidenceField:
    return EvidenceField(
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
        evidence_score=evidence_score,
        confidence="HIGH",
        bus=bus,
        address=address,
        channel=channel,
        slot_id=slot_id,
        cycle=cycle,
    )


def _raw(value: int) -> bytes:
    return int(value).to_bytes(2, byteorder="big", signed=True)


def _build_trace(
    can_values: list[int],
    flex_values: list[int],
    *,
    flex_delay_s: float = 0.020,
    flex_cycle: int = 3,
    include_wrong_cycle_noise: bool = False,
) -> list[BMWTransportFrame]:
    can_identity = TransportIdentity(transport="CAN", bus="can0", address=0x123)
    flex_identity = TransportIdentity(
        transport="FLEXRAY",
        channel="A",
        slot_id=77,
        cycle=flex_cycle,
    )
    wrong_cycle = TransportIdentity(
        transport="FLEXRAY",
        channel="A",
        slot_id=77,
        cycle=4,
    )

    frames: list[BMWTransportFrame] = []
    for index, (can_value, flex_value) in enumerate(zip(can_values, flex_values)):
        t = 1.0 + index * 0.1
        frames.append(BMWTransportFrame(t, can_identity, _raw(can_value)))
        frames.append(BMWTransportFrame(t + flex_delay_s, flex_identity, _raw(flex_value)))
        if include_wrong_cycle_noise:
            frames.append(BMWTransportFrame(t + 0.001, wrong_cycle, _raw(5000 - index * 313)))
    frames.sort(key=lambda frame: frame.t)
    return frames


def _evidence() -> list[EvidenceField]:
    return [
        _field(
            transport="CAN",
            source_key="CAN|can0|291",
            bus="can0",
            address=0x123,
        ),
        _field(
            transport="FLEXRAY",
            source_key="FLEXRAY|A|77|None|cycle|3",
            channel="A",
            slot_id=77,
            cycle=3,
        ),
    ]


def test_scaled_delayed_can_flexray_series_rank_as_strong_correspondence():
    can_values = [0, 10, 20, 30, 40, 50, 60, 70]
    flex_values = [100 + 2 * value for value in can_values]
    frames = _build_trace(can_values, flex_values)

    ranked = rank_cross_transport_correspondence(
        frames,
        _evidence(),
        max_lag_ms=50,
        lag_step_ms=5,
        alignment_tolerance_ms=5,
    )

    top = ranked[0]
    assert top.absolute_correlation > 0.999
    assert top.raw_polarity_relation == "SAME_RAW_POLARITY"
    assert top.best_lag_ms == -20.0
    assert top.overlap_score == 1.0
    assert top.relationship == "STRONG_DUAL_TRANSPORT_CORRESPONDENCE"
    assert top.gateway_hypothesis == "POSSIBLE_ZGW_FORWARD_OR_DERIVED_REPRESENTATION"
    assert top.status == "UNVALIDATED_CROSS_TRANSPORT_CORRESPONDENCE"


def test_inverted_raw_polarity_is_still_detected():
    can_values = [0, 10, 20, 30, 40, 50, 60, 70]
    flex_values = [1000 - 3 * value for value in can_values]
    frames = _build_trace(can_values, flex_values)

    ranked = rank_cross_transport_correspondence(
        frames,
        _evidence(),
        max_lag_ms=50,
        lag_step_ms=5,
        alignment_tolerance_ms=5,
    )

    top = ranked[0]
    assert top.absolute_correlation > 0.999
    assert top.correlation < 0
    assert top.raw_polarity_relation == "INVERTED_RAW_POLARITY"
    assert top.relationship == "STRONG_DUAL_TRANSPORT_CORRESPONDENCE"


def test_unrelated_series_remain_weak():
    can_values = [0, 1, 2, 3, 4, 5]
    flex_values = [3, 1, 4, 0, 5, 2]
    frames = _build_trace(can_values, flex_values, flex_delay_s=0.0)

    ranked = rank_cross_transport_correspondence(
        frames,
        _evidence(),
        max_lag_ms=0,
        lag_step_ms=5,
        alignment_tolerance_ms=1,
    )

    top = ranked[0]
    assert top.absolute_correlation < 0.2
    assert top.relationship == "WEAK_OR_UNRELATED"
    assert top.gateway_hypothesis == "NOT_INFERRED"


def test_wrong_flexray_cycle_noise_is_not_mixed_into_target_series():
    can_values = [0, 10, 20, 30, 40, 50, 60, 70]
    flex_values = [value * 4 for value in can_values]
    frames = _build_trace(
        can_values,
        flex_values,
        flex_delay_s=0.0,
        include_wrong_cycle_noise=True,
    )

    ranked = rank_cross_transport_correspondence(
        frames,
        _evidence(),
        max_lag_ms=0,
        lag_step_ms=5,
        alignment_tolerance_ms=1,
    )

    top = ranked[0]
    assert top.flexray_samples == len(flex_values)
    assert top.absolute_correlation > 0.999
    assert top.relationship == "STRONG_DUAL_TRANSPORT_CORRESPONDENCE"


def test_different_function_families_are_not_compared():
    frames = _build_trace([0, 1, 2, 3], [0, 1, 2, 3], flex_delay_s=0.0)
    evidence = [
        _field(
            transport="CAN",
            source_key="CAN|can0|291",
            bus="can0",
            address=0x123,
            function_family="STEERING_LIKE",
        ),
        _field(
            transport="FLEXRAY",
            source_key="FLEXRAY|A|77|None|cycle|3",
            channel="A",
            slot_id=77,
            cycle=3,
            function_family="YAW_LIKE",
        ),
    ]

    assert rank_cross_transport_correspondence(frames, evidence) == []


def test_low_evidence_candidates_are_filtered():
    frames = _build_trace([0, 1, 2, 3], [0, 1, 2, 3], flex_delay_s=0.0)
    evidence = [
        _field(
            transport="CAN",
            source_key="CAN|can0|291",
            bus="can0",
            address=0x123,
            evidence_score=0.40,
        ),
        _field(
            transport="FLEXRAY",
            source_key="FLEXRAY|A|77|None|cycle|3",
            channel="A",
            slot_id=77,
            cycle=3,
            evidence_score=0.95,
        ),
    ]

    assert rank_cross_transport_correspondence(
        frames,
        evidence,
        minimum_evidence_score=0.60,
    ) == []


def test_correspondence_record_has_no_control_or_decoder_fields():
    names = {field.name for field in fields(CrossTransportCorrespondence)}
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
    assert CrossTransportCorrespondence.__dataclass_fields__["status"].default == (
        "UNVALIDATED_CROSS_TRANSPORT_CORRESPONDENCE"
    )
