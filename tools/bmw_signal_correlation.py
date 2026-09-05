#!/usr/bin/env python3
"""Offline, read-only BMW signal correlation analyzer.

Input trace format (JSONL), one frame per line:
  {"t": 12.345, "bus": "can0", "address": 291, "data": "0011223344556677"}

Markers format (JSON array):
  [{"t": 10.0, "event": "BLIND_LEFT_ENTER"}, ...]

The analyzer ranks raw byte/bit candidates by how strongly their state changes
around marked events. It never writes to a vehicle, generates control messages,
or promotes a decoder automatically.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Frame:
    t: float
    bus: str
    address: int
    data: bytes


@dataclass(frozen=True)
class Marker:
    t: float
    event: str


@dataclass(frozen=True)
class Candidate:
    event: str
    bus: str
    address: int
    byte: int
    bit: int | None
    score: float
    observations: int
    before_mean: float
    after_mean: float
    kind: str


def load_trace(path: Path) -> list[Frame]:
    frames: list[Frame] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        obj = json.loads(line)
        raw = bytes.fromhex(obj["data"])
        frames.append(Frame(float(obj["t"]), str(obj.get("bus", "unknown")), int(obj["address"]), raw))
    frames.sort(key=lambda f: f.t)
    return frames


def load_markers(path: Path) -> list[Marker]:
    markers = [Marker(float(x["t"]), str(x["event"])) for x in json.loads(path.read_text(encoding="utf-8"))]
    markers.sort(key=lambda m: m.t)
    return markers


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else math.nan


def _samples(frames: Iterable[Frame], start: float, end: float):
    for frame in frames:
        if start <= frame.t < end:
            yield frame


def _feature_values(frames: Iterable[Frame]):
    """Return grouped byte and bit values for a time window."""
    byte_values: dict[tuple[str, int, int], list[float]] = defaultdict(list)
    bit_values: dict[tuple[str, int, int, int], list[float]] = defaultdict(list)
    for frame in frames:
        for byte_idx, value in enumerate(frame.data):
            byte_values[(frame.bus, frame.address, byte_idx)].append(float(value))
            for bit in range(8):
                bit_values[(frame.bus, frame.address, byte_idx, bit)].append(float((value >> bit) & 1))
    return byte_values, bit_values


def rank_candidates(
    frames: list[Frame],
    markers: list[Marker],
    *,
    before_s: float = 1.0,
    after_s: float = 1.0,
    min_observations: int = 2,
) -> list[Candidate]:
    """Rank features by repeated before/after separation around each marker type.

    Score is the mean absolute normalized state change across marker occurrences.
    Bit features naturally score in [0, 1]. Byte scores are normalized by 255.
    This is a discovery heuristic, not evidence of a decoded signal.
    """
    per_event: dict[str, dict[tuple, list[tuple[float, float]]]] = defaultdict(lambda: defaultdict(list))

    for marker in markers:
        before_frames = list(_samples(frames, marker.t - before_s, marker.t))
        after_frames = list(_samples(frames, marker.t, marker.t + after_s))
        before_bytes, before_bits = _feature_values(before_frames)
        after_bytes, after_bits = _feature_values(after_frames)

        for key in set(before_bytes) & set(after_bytes):
            per_event[marker.event][("byte",) + key].append((_mean(before_bytes[key]), _mean(after_bytes[key])))
        for key in set(before_bits) & set(after_bits):
            per_event[marker.event][("bit",) + key].append((_mean(before_bits[key]), _mean(after_bits[key])))

    ranked: list[Candidate] = []
    for event, features in per_event.items():
        for key, pairs in features.items():
            if len(pairs) < min_observations:
                continue
            kind = key[0]
            changes = [abs(a - b) for a, b in pairs]
            scale = 1.0 if kind == "bit" else 255.0
            score = sum(changes) / len(changes) / scale
            before_mean = sum(a for a, _ in pairs) / len(pairs)
            after_mean = sum(b for _, b in pairs) / len(pairs)
            if kind == "bit":
                _, bus, address, byte_idx, bit = key
            else:
                _, bus, address, byte_idx = key
                bit = None
            ranked.append(Candidate(
                event=event,
                bus=bus,
                address=address,
                byte=byte_idx,
                bit=bit,
                score=score,
                observations=len(pairs),
                before_mean=before_mean,
                after_mean=after_mean,
                kind=kind,
            ))

    ranked.sort(key=lambda c: (-c.score, -c.observations, c.event, c.bus, c.address, c.byte, -1 if c.bit is None else c.bit))
    return ranked


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank raw BMW bus signal candidates around event markers")
    parser.add_argument("trace", type=Path)
    parser.add_argument("markers", type=Path)
    parser.add_argument("--before", type=float, default=1.0)
    parser.add_argument("--after", type=float, default=1.0)
    parser.add_argument("--min-observations", type=int, default=2)
    parser.add_argument("--top", type=int, default=50)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    ranked = rank_candidates(load_trace(args.trace), load_markers(args.markers), before_s=args.before, after_s=args.after, min_observations=args.min_observations)
    payload = {
        "mode": "OFFLINE_READ_ONLY_DISCOVERY",
        "auto_promote": False,
        "actuation_authority": "NONE",
        "candidates": [asdict(x) for x in ranked[: args.top]],
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
