from __future__ import annotations

from dataclasses import fields

from tools.bmw_function_identifier import (
    FunctionHypothesis,
    FunctionSpec,
    identify_function_hypotheses,
)
from tools.bmw_signal_correlation import Marker
from tools.bmw_transport import BMWTransportFrame, TransportIdentity, frame_from_obj


def _signed_be(value: int) -> bytes:
    return int(value).to_bytes(2, byteorder="big", signed=True)


def _continuous_event_frames(
    t: float,
    before_value: int,
    after_value: int,
    identity: TransportIdentity,
) -> list[BMWTransportFrame]:
    return [
        BMWTransportFrame(t - 0.4, identity, _signed_be(before_value)),
        BMWTransportFrame(t - 0.2, identity, _signed_be(before_value)),
        BMWTransportFrame(t + 0.2, identity, _signed_be(after_value)),
        BMWTransportFrame(t + 0.4, identity, _signed_be(after_value)),
    ]


def _bit_event_frames(
    t: float,
    before_value: int,
    after_value: int,
    identity: TransportIdentity,
) -> list[BMWTransportFrame]:
    return [
        BMWTransportFrame(t - 0.4, identity, bytes([before_value])),
        BMWTransportFrame(t - 0.2, identity, bytes([before_value])),
        BMWTransportFrame(t + 0.2, identity, bytes([after_value])),
        BMWTransportFrame(t + 0.4, identity, bytes([after_value])),
    ]


def test_legacy_can_trace_defaults_to_can_transport():
    frame = frame_from_obj({
        "t": 1.0,
        "bus": "can0",
        "address": 0x123,
        "data": "0011",
    })

    assert frame.identity.transport == "CAN"
    assert frame.identity.bus == "can0"
    assert frame.identity.address == 0x123


def test_flexray_same_slot_different_cycles_remain_distinct():
    cycle_1 = frame_from_obj({
        "t": 1.0,
        "transport": "FLEXRAY",
        "channel": "A",
        "slot_id": 42,
        "cycle": 1,
        "data": "0001",
    })
    cycle_2 = frame_from_obj({
        "t": 2.0,
        "transport": "FLEXRAY",
        "channel": "A",
        "slot_id": 42,
        "cycle": 2,
        "data": "0001",
    })

    assert cycle_1.identity.correlation_key() != cycle_2.identity.correlation_key()


def test_flexray_schedule_identity_groups_repeating_cycles():
    first = TransportIdentity(
        transport="FLEXRAY",
        channel="A",
        slot_id=42,
        cycle=2,
        base_cycle=2,
        cycle_repetition=4,
    )
    repeated = TransportIdentity(
        transport="FLEXRAY",
        channel="A",
        slot_id=42,
        cycle=6,
        base_cycle=2,
        cycle_repetition=4,
    )

    assert first.correlation_key() == repeated.correlation_key()


def test_identifies_steering_like_signed_flexray_candidate():
    identity = TransportIdentity(
        transport="FLEXRAY",
        channel="A",
        slot_id=77,
        cycle=3,
    )
    frames: list[BMWTransportFrame] = []
    markers: list[Marker] = []

    events = [
        (10.0, "STEER_LEFT_SLOW", 0, 1000),
        (20.0, "STEER_LEFT_SLOW", 0, 1200),
        (30.0, "STEER_RIGHT_SLOW", 0, -1000),
        (40.0, "STEER_RIGHT_SLOW", 0, -1200),
        (50.0, "STEER_CENTER", 600, 0),
        (60.0, "STEER_CENTER", -600, 0),
    ]
    for t, event, before_value, after_value in events:
        markers.append(Marker(t, event))
        frames.extend(_continuous_event_frames(t, before_value, after_value, identity))

    hypotheses = identify_function_hypotheses(
        frames,
        markers,
        [FunctionSpec(
            name="STEERING_LIKE",
            kind="opposed_continuous",
            positive_event="STEER_LEFT_SLOW",
            negative_event="STEER_RIGHT_SLOW",
            baseline_event="STEER_CENTER",
        )],
    )

    top = hypotheses[0]
    assert top.function_family == "STEERING_LIKE"
    assert top.transport == "FLEXRAY"
    assert top.slot_id == 77
    assert top.start_byte == 0
    assert top.width == 2
    assert top.signed is True
    assert top.endian == "big"
    assert top.direction_score == 1.0
    assert top.baseline_score == 1.0


def test_identifies_toggle_like_can_candidate():
    identity = TransportIdentity(transport="CAN", bus="can1", address=0x321)
    frames: list[BMWTransportFrame] = []
    markers: list[Marker] = []

    events = [
        (10.0, "BLIND_LEFT_ENTER", 0x00, 0x04),
        (20.0, "BLIND_LEFT_ENTER", 0x00, 0x04),
        (30.0, "BLIND_LEFT_EXIT", 0x04, 0x00),
        (40.0, "BLIND_LEFT_EXIT", 0x04, 0x00),
    ]
    for t, event, before_value, after_value in events:
        markers.append(Marker(t, event))
        frames.extend(_bit_event_frames(t, before_value, after_value, identity))

    hypotheses = identify_function_hypotheses(
        frames,
        markers,
        [FunctionSpec(
            name="BLINDSPOT_LEFT_STATE_LIKE",
            kind="toggle",
            positive_event="BLIND_LEFT_ENTER",
            negative_event="BLIND_LEFT_EXIT",
        )],
    )

    top = hypotheses[0]
    assert top.transport == "CAN"
    assert top.address == 0x321
    assert top.feature_kind == "bit"
    assert top.start_byte == 0
    assert top.bit == 2
    assert top.direction_score == 1.0
    assert top.transition_strength == 1.0


def test_same_signature_on_can_and_flexray_keeps_provenance_separate():
    can = TransportIdentity(transport="CAN", bus="can0", address=0x111)
    flexray = TransportIdentity(transport="FLEXRAY", channel="B", slot_id=55, cycle=4)
    frames: list[BMWTransportFrame] = []
    markers: list[Marker] = []

    for t, event, before_value, after_value in [
        (10.0, "GAP_UP", 0, 20),
        (20.0, "GAP_UP", 0, 20),
        (30.0, "GAP_DOWN", 0, -20),
        (40.0, "GAP_DOWN", 0, -20),
    ]:
        markers.append(Marker(t, event))
        frames.extend(_continuous_event_frames(t, before_value, after_value, can))
        frames.extend(_continuous_event_frames(t, before_value, after_value, flexray))

    hypotheses = identify_function_hypotheses(
        frames,
        markers,
        [FunctionSpec(
            name="ACC_GAP_CONTROL_LIKE",
            kind="opposed_continuous",
            positive_event="GAP_UP",
            negative_event="GAP_DOWN",
        )],
    )

    transports = {item.transport for item in hypotheses if item.score >= 0.9}
    assert transports == {"CAN", "FLEXRAY"}
    assert len({item.source_key for item in hypotheses if item.score >= 0.9}) >= 2


def test_function_hypothesis_has_no_control_or_decoder_authority_fields():
    names = {field.name for field in fields(FunctionHypothesis)}
    forbidden = {
        "command",
        "actuation",
        "decoder",
        "scale",
        "offset",
        "unit",
        "sendcan",
        "tx",
    }

    assert forbidden.isdisjoint(names)
    assert FunctionHypothesis.__dataclass_fields__["status"].default == (
        "UNVALIDATED_FUNCTION_HYPOTHESIS"
    )
