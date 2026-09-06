from __future__ import annotations

from dataclasses import fields

from tools.bmw_request_feedback_topology import (
    TopologyEdge,
    TopologyNodeSpec,
    infer_request_feedback_topology,
)
from tools.bmw_transport import BMWTransportFrame, TransportIdentity


def _raw(value: int) -> bytes:
    return int(value).to_bytes(2, byteorder="big", signed=True)


def _node(name: str, address: int) -> TopologyNodeSpec:
    return TopologyNodeSpec(
        name=name,
        function_family="STEERING_CONTROL_CHAIN",
        transport="CAN",
        feature_kind="continuous_integer",
        start_byte=0,
        width=2,
        bit=None,
        signed=True,
        endian="big",
        bus="can0",
        address=address,
    )


def _trace(delay_feedback: float = 0.010, delay_yaw: float = 0.030):
    request_id = TransportIdentity(transport="CAN", bus="can0", address=0x100)
    feedback_id = TransportIdentity(transport="CAN", bus="can0", address=0x101)
    yaw_id = TransportIdentity(transport="CAN", bus="can0", address=0x102)

    frames: list[BMWTransportFrame] = []
    values = [0, 10, 25, 40, 20, -5, -25, -10, 5, 30]
    for i, value in enumerate(values):
        t = 1.0 + i * 0.1
        frames.append(BMWTransportFrame(t, request_id, _raw(value)))
        frames.append(BMWTransportFrame(t + delay_feedback, feedback_id, _raw(value * 2)))
        frames.append(BMWTransportFrame(t + delay_yaw, yaw_id, _raw(-value * 3)))
    frames.sort(key=lambda f: f.t)
    return frames


def test_request_like_candidate_leads_feedback_candidate():
    nodes = [_node("candidate_request", 0x100), _node("candidate_feedback", 0x101)]

    ranked = infer_request_feedback_topology(
        _trace(),
        nodes,
        max_lag_ms=50,
        lag_step_ms=5,
        alignment_tolerance_ms=2,
        minimum_pairs=5,
    )

    edge = next(item for item in ranked if item.source == "candidate_request")
    assert edge.target == "candidate_feedback"
    assert edge.absolute_correlation > 0.999
    assert edge.best_lag_ms == 10.0
    assert edge.lead_relation == "SOURCE_LEADS_TARGET"
    assert edge.interpretation == "UPSTREAM_LIKE_RELATIVE_TO_TARGET"


def test_feedback_candidate_leads_physical_yaw_response():
    nodes = [
        _node("candidate_feedback", 0x101),
        _node("physical_yaw", 0x102),
    ]

    ranked = infer_request_feedback_topology(
        _trace(),
        nodes,
        max_lag_ms=50,
        lag_step_ms=5,
        alignment_tolerance_ms=2,
        minimum_pairs=5,
    )

    edge = next(item for item in ranked if item.source == "candidate_feedback")
    assert edge.target == "physical_yaw"
    assert edge.absolute_correlation > 0.999
    assert edge.best_lag_ms == 20.0
    assert edge.lead_relation == "SOURCE_LEADS_TARGET"


def test_different_function_families_are_not_connected():
    a = _node("a", 0x100)
    b = TopologyNodeSpec(
        **{**a.__dict__, "name": "b", "address": 0x101, "function_family": "OTHER"}
    )

    assert infer_request_feedback_topology(_trace(), [a, b]) == []


def test_edge_is_explicitly_unvalidated_and_non_actuating():
    names = {field.name for field in fields(TopologyEdge)}
    forbidden = {
        "command",
        "actuation",
        "can_id",
        "slot_id",
        "payload",
        "checksum",
        "sendcan",
        "tx",
    }
    assert forbidden.isdisjoint(names)
    assert TopologyEdge.__dataclass_fields__["status"].default == (
        "UNVALIDATED_REQUEST_FEEDBACK_TOPOLOGY"
    )
