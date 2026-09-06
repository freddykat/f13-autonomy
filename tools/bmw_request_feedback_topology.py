#!/usr/bin/env python3
"""Offline request/feedback topology inference for BMW passive captures.

The tool compares explicitly selected raw candidates and estimates temporal
ordering between them. It is intended for SHADOW/HIL research only.

A node that consistently leads another correlated node is labeled
UPSTREAM_LIKE relative to that peer. This is not proof that the first node is a
control request, nor does it prove ECU ownership or actuator authority.
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tools.bmw_transport import BMWTransportFrame, load_transport_trace


@dataclass(frozen=True)
class TopologyNodeSpec:
    name: str
    function_family: str
    transport: str
    feature_kind: str
    start_byte: int
    width: int | None
    bit: int | None
    signed: bool | None
    endian: str | None
    bus: str | None = None
    address: int | None = None
    channel: str | None = None
    slot_id: int | None = None
    cycle: int | None = None
    base_cycle: int | None = None
    cycle_repetition: int | None = None
    frame_id: int | None = None


@dataclass(frozen=True)
class TopologyEdge:
    source: str
    target: str
    function_family: str
    aligned_pairs: int
    correlation: float
    absolute_correlation: float
    best_lag_ms: float
    lead_relation: str
    overlap_score: float
    edge_score: float
    interpretation: str
    status: str = "UNVALIDATED_REQUEST_FEEDBACK_TOPOLOGY"


def _optional_int(item: dict[str, Any], key: str) -> int | None:
    value = item.get(key)
    return None if value is None else int(value)


def _optional_bool(item: dict[str, Any], key: str) -> bool | None:
    value = item.get(key)
    return None if value is None else bool(value)


def load_nodes(path: Path) -> list[TopologyNodeSpec]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("nodes")
    if not isinstance(items, list):
        raise ValueError(f"{path}: missing nodes list")

    nodes: list[TopologyNodeSpec] = []
    for item in items:
        nodes.append(TopologyNodeSpec(
            name=str(item["name"]),
            function_family=str(item["function_family"]),
            transport=str(item["transport"]).upper(),
            feature_kind=str(item["feature_kind"]),
            start_byte=int(item["start_byte"]),
            width=_optional_int(item, "width"),
            bit=_optional_int(item, "bit"),
            signed=_optional_bool(item, "signed"),
            endian=None if item.get("endian") is None else str(item["endian"]),
            bus=None if item.get("bus") is None else str(item["bus"]),
            address=_optional_int(item, "address"),
            channel=None if item.get("channel") is None else str(item["channel"]),
            slot_id=_optional_int(item, "slot_id"),
            cycle=_optional_int(item, "cycle"),
            base_cycle=_optional_int(item, "base_cycle"),
            cycle_repetition=_optional_int(item, "cycle_repetition"),
            frame_id=_optional_int(item, "frame_id"),
        ))
    return nodes


def _matches(node: TopologyNodeSpec, frame: BMWTransportFrame) -> bool:
    identity = frame.identity
    if identity.transport != node.transport:
        return False

    if node.transport == "CAN":
        if node.bus is not None and identity.bus != node.bus:
            return False
        if node.address is not None and identity.address != node.address:
            return False
        return True

    if node.transport != "FLEXRAY":
        return False

    if node.channel is not None and identity.channel != node.channel:
        return False
    if node.slot_id is not None and identity.slot_id != node.slot_id:
        return False
    if node.frame_id is not None and identity.frame_id is not None and identity.frame_id != node.frame_id:
        return False

    if node.base_cycle is not None:
        repetition = node.cycle_repetition
        if repetition is None or repetition <= 0:
            return False
        if identity.base_cycle is not None:
            if identity.base_cycle != node.base_cycle:
                return False
            if identity.cycle_repetition is not None and identity.cycle_repetition != repetition:
                return False
            return True
        if identity.cycle is None:
            return False
        return (identity.cycle - node.base_cycle) % repetition == 0

    if node.cycle is not None and identity.cycle != node.cycle:
        return False

    return True


def _decode(node: TopologyNodeSpec, data: bytes) -> float | None:
    if node.feature_kind == "bit":
        if node.bit is None or node.start_byte < 0 or node.start_byte >= len(data):
            return None
        if node.bit < 0 or node.bit > 7:
            return None
        return float((data[node.start_byte] >> node.bit) & 1)

    if node.feature_kind != "continuous_integer":
        return None
    if node.width is None or node.signed is None or node.endian is None:
        return None

    end = node.start_byte + node.width
    if node.start_byte < 0 or end > len(data):
        return None
    return float(int.from_bytes(
        data[node.start_byte:end],
        byteorder=node.endian,
        signed=node.signed,
    ))


def _series(node: TopologyNodeSpec, frames: list[BMWTransportFrame]) -> list[tuple[float, float]]:
    result: list[tuple[float, float]] = []
    for frame in frames:
        if not _matches(node, frame):
            continue
        value = _decode(node, frame.data)
        if value is not None:
            result.append((frame.t, value))
    result.sort(key=lambda item: item[0])
    return result


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 3:
        return 0.0
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    denom = math.sqrt(sum(x*x for x in dx) * sum(y*y for y in dy))
    if denom <= 1e-12:
        return 0.0
    return sum(x*y for x, y in zip(dx, dy)) / denom


def _align(
    source: list[tuple[float, float]],
    target: list[tuple[float, float]],
    *,
    lag_s: float,
    tolerance_s: float,
) -> list[tuple[float, float]]:
    if not source or not target:
        return []

    target_times = [t for t, _ in target]
    used: set[int] = set()
    pairs: list[tuple[float, float]] = []

    # Positive lag means source is earlier and target follows after lag.
    for source_t, source_value in source:
        desired_target_t = source_t + lag_s
        idx = bisect.bisect_left(target_times, desired_target_t)
        candidates: list[tuple[float, int]] = []
        for j in (idx - 1, idx, idx + 1):
            if 0 <= j < len(target) and j not in used:
                error = abs(target[j][0] - desired_target_t)
                candidates.append((error, j))
        if not candidates:
            continue
        error, best = min(candidates)
        if error > tolerance_s:
            continue
        used.add(best)
        pairs.append((source_value, target[best][1]))

    return pairs


def infer_request_feedback_topology(
    frames: list[BMWTransportFrame],
    nodes: list[TopologyNodeSpec],
    *,
    max_lag_ms: int = 100,
    lag_step_ms: int = 5,
    alignment_tolerance_ms: float = 10.0,
    minimum_pairs: int = 5,
) -> list[TopologyEdge]:
    if max_lag_ms < 0:
        raise ValueError("max_lag_ms must be non-negative")
    if lag_step_ms <= 0:
        raise ValueError("lag_step_ms must be positive")

    series = {node.name: _series(node, frames) for node in nodes}
    ranked: list[TopologyEdge] = []
    tolerance_s = alignment_tolerance_ms / 1000.0
    lags = list(range(-max_lag_ms, max_lag_ms + 1, lag_step_ms))
    if 0 not in lags:
        lags.append(0)

    for source in nodes:
        for target in nodes:
            if source.name == target.name:
                continue
            if source.function_family != target.function_family:
                continue

            source_series = series[source.name]
            target_series = series[target.name]
            if len(source_series) < minimum_pairs or len(target_series) < minimum_pairs:
                continue

            best: tuple[float, float, int, int] | None = None
            for lag_ms in sorted(set(lags)):
                pairs = _align(
                    source_series,
                    target_series,
                    lag_s=lag_ms / 1000.0,
                    tolerance_s=tolerance_s,
                )
                if len(pairs) < minimum_pairs:
                    continue
                correlation = _pearson(
                    [pair[0] for pair in pairs],
                    [pair[1] for pair in pairs],
                )
                overlap = len(pairs) / float(min(len(source_series), len(target_series)))
                score = abs(correlation) * overlap
                candidate = (score, correlation, lag_ms, len(pairs))
                if best is None or candidate[0] > best[0]:
                    best = candidate

            if best is None:
                continue

            score, correlation, lag_ms, pair_count = best
            overlap = pair_count / float(min(len(source_series), len(target_series)))

            if lag_ms > 0:
                lead_relation = "SOURCE_LEADS_TARGET"
                interpretation = "UPSTREAM_LIKE_RELATIVE_TO_TARGET"
            elif lag_ms < 0:
                lead_relation = "SOURCE_FOLLOWS_TARGET"
                interpretation = "DOWNSTREAM_LIKE_RELATIVE_TO_TARGET"
            else:
                lead_relation = "SIMULTANEOUS_WITHIN_RESOLUTION"
                interpretation = "ORDER_UNRESOLVED"

            ranked.append(TopologyEdge(
                source=source.name,
                target=target.name,
                function_family=source.function_family,
                aligned_pairs=pair_count,
                correlation=correlation,
                absolute_correlation=abs(correlation),
                best_lag_ms=float(lag_ms),
                lead_relation=lead_relation,
                overlap_score=overlap,
                edge_score=score,
                interpretation=interpretation,
            ))

    ranked.sort(key=lambda item: (
        -item.edge_score,
        -item.absolute_correlation,
        -item.overlap_score,
        item.function_family,
        item.source,
        item.target,
    ))
    return ranked


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Infer passive BMW request/feedback topology from synchronized raw traces"
    )
    parser.add_argument("trace", type=Path)
    parser.add_argument("nodes", type=Path)
    parser.add_argument("--max-lag-ms", type=int, default=100)
    parser.add_argument("--lag-step-ms", type=int, default=5)
    parser.add_argument("--alignment-tolerance-ms", type=float, default=10.0)
    parser.add_argument("--minimum-pairs", type=int, default=5)
    parser.add_argument("--top", type=int, default=200)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    edges = infer_request_feedback_topology(
        load_transport_trace(args.trace),
        load_nodes(args.nodes),
        max_lag_ms=args.max_lag_ms,
        lag_step_ms=args.lag_step_ms,
        alignment_tolerance_ms=args.alignment_tolerance_ms,
        minimum_pairs=args.minimum_pairs,
    )
    payload = {
        "mode": "OFFLINE_READ_ONLY_TOPOLOGY_INFERENCE",
        "status": "UNVALIDATED_REQUEST_FEEDBACK_TOPOLOGY",
        "request_role_proven": False,
        "ecu_ownership_proven": False,
        "live_transmit": False,
        "diagnostic_writes": False,
        "actuation_authority": "NONE",
        "edges": [asdict(item) for item in edges[: args.top]],
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
