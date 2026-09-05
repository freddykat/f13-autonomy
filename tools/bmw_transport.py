#!/usr/bin/env python3
"""Transport-aware passive BMW frame model for CAN and FlexRay captures.

This module is deliberately read-only. It preserves transport provenance so
FlexRay slots/cycles are never flattened into fake CAN addresses.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TransportIdentity:
    transport: str
    bus: str | None = None
    address: int | None = None
    channel: str | None = None
    slot_id: int | None = None
    cycle: int | None = None
    base_cycle: int | None = None
    cycle_repetition: int | None = None
    frame_id: int | None = None

    def __post_init__(self) -> None:
        transport = self.transport.upper()
        object.__setattr__(self, "transport", transport)
        if transport == "CAN":
            if self.address is None:
                raise ValueError("CAN identity requires address")
        elif transport == "FLEXRAY":
            if self.slot_id is None:
                raise ValueError("FlexRay identity requires slot_id")
            if self.cycle_repetition is not None and self.base_cycle is None:
                raise ValueError("cycle_repetition requires base_cycle")
            if self.cycle_repetition is not None and self.cycle_repetition <= 0:
                raise ValueError("cycle_repetition must be positive")
        else:
            raise ValueError(f"unsupported transport: {self.transport}")

    def correlation_key(self) -> tuple[Any, ...]:
        """Stable identity used for passive signal correlation.

        CAN is keyed by bus/address.

        FlexRay preserves channel + slot and, when a schedule identity is
        supplied, base_cycle/cycle_repetition. Otherwise the observed cycle is
        kept in the key. This avoids merging different cycle multiplexes.
        """
        if self.transport == "CAN":
            return ("CAN", self.bus or "unknown", self.address)

        cycle_key: tuple[Any, ...]
        if self.base_cycle is not None:
            cycle_key = ("schedule", self.base_cycle, self.cycle_repetition)
        else:
            cycle_key = ("cycle", self.cycle)
        return (
            "FLEXRAY",
            self.channel or "unknown",
            self.slot_id,
            self.frame_id,
            *cycle_key,
        )


@dataclass(frozen=True)
class BMWTransportFrame:
    t: float
    identity: TransportIdentity
    data: bytes


def _optional_int(obj: dict[str, Any], key: str) -> int | None:
    value = obj.get(key)
    return None if value is None else int(value)


def frame_from_obj(obj: dict[str, Any]) -> BMWTransportFrame:
    """Parse one passive trace object.

    Backwards-compatible CAN input:
      {"t": 1.0, "bus": "can0", "address": 291, "data": "0011"}

    Transport-aware CAN:
      {"t": 1.0, "transport": "CAN", ...}

    FlexRay:
      {
        "t": 1.0,
        "transport": "FLEXRAY",
        "channel": "A",
        "slot_id": 42,
        "cycle": 7,
        "data": "0011"
      }

    Optional FlexRay schedule metadata:
      base_cycle, cycle_repetition, frame_id
    """
    transport = str(obj.get("transport", "CAN")).upper()
    raw = bytes.fromhex(str(obj["data"]))

    if transport == "CAN":
        identity = TransportIdentity(
            transport="CAN",
            bus=str(obj.get("bus", "unknown")),
            address=int(obj["address"]),
        )
    elif transport == "FLEXRAY":
        identity = TransportIdentity(
            transport="FLEXRAY",
            channel=str(obj.get("channel", "unknown")),
            slot_id=int(obj["slot_id"]),
            cycle=_optional_int(obj, "cycle"),
            base_cycle=_optional_int(obj, "base_cycle"),
            cycle_repetition=_optional_int(obj, "cycle_repetition"),
            frame_id=_optional_int(obj, "frame_id"),
        )
    else:
        raise ValueError(f"unsupported transport: {transport}")

    return BMWTransportFrame(t=float(obj["t"]), identity=identity, data=raw)


def load_transport_trace(path: Path) -> list[BMWTransportFrame]:
    frames: list[BMWTransportFrame] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            frames.append(frame_from_obj(obj))
        except Exception as exc:
            raise ValueError(f"{path}:{lineno}: {exc}") from exc
    frames.sort(key=lambda frame: frame.t)
    return frames
