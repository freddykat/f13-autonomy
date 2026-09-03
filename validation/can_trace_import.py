from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


CANDUMP_RE = re.compile(
    r"^\((?P<ts>\d+(?:\.\d+)?)\)\s+(?P<if>\S+)\s+(?P<id>[0-9A-Fa-f]+)#(?P<data>[0-9A-Fa-f]*)$"
)

# Common Vector ASC classic-CAN form, e.g.:
# 0.123456 1 123 Rx d 8 11 22 33 44 55 66 77 88
ASC_RE = re.compile(
    r"^\s*(?P<ts>\d+(?:\.\d+)?)\s+"
    r"(?P<channel>\d+)\s+"
    r"(?P<id>[0-9A-Fa-f]+)(?P<ext>x)?\s+"
    r"(?P<dir>Rx|Tx)\s+"
    r"d\s+(?P<dlc>\d+)"
    r"(?P<data>(?:\s+[0-9A-Fa-f]{2})*)\s*$"
)

CAPTURE_QUALITIES = {"UNKNOWN", "LOSSY", "OBSERVATION_ONLY", "FULL_RATE_CANDIDATE"}
FILTER_MODES = {"UNKNOWN", "ACCEPT_ALL", "SINGLE_ID_HARDWARE", "MULTI_ID_HARDWARE", "SOFTWARE"}


@dataclass(frozen=True)
class CanonicalCanFrame:
    timestamp_ns: int
    timestamp_provenance: str
    source_format: str
    channel: str
    direction: str
    arbitration_id: int
    is_extended_id: bool
    is_remote_frame: bool
    dlc: int
    data_hex: str


def seconds_to_ns(value: str) -> int:
    # Parsing through decimal text avoids assigning meaning beyond source precision.
    whole, dot, frac = value.partition(".")
    frac = (frac + "000000000")[:9] if dot else "000000000"
    return int(whole) * 1_000_000_000 + int(frac)


def parse_candump_line(line: str) -> CanonicalCanFrame | None:
    text = line.strip()
    if not text or text.startswith("#"):
        return None

    match = CANDUMP_RE.match(text)
    if not match:
        raise ValueError(f"unsupported candump line: {line.rstrip()}")

    data_hex = match.group("data").upper()
    if len(data_hex) % 2:
        raise ValueError("CAN payload hex length must be even")

    arbitration_id = int(match.group("id"), 16)
    return CanonicalCanFrame(
        timestamp_ns=seconds_to_ns(match.group("ts")),
        timestamp_provenance="capture_tool_timestamp",
        source_format="candump",
        channel=match.group("if"),
        direction="Rx",
        arbitration_id=arbitration_id,
        is_extended_id=arbitration_id > 0x7FF,
        is_remote_frame=False,
        dlc=len(data_hex) // 2,
        data_hex=data_hex,
    )


def parse_vector_asc_line(line: str) -> CanonicalCanFrame | None:
    text = line.strip()
    if not text:
        return None

    lower = text.lower()
    if lower.startswith(("date ", "base ", "timestamps ", "internal events", "//")):
        return None

    match = ASC_RE.match(line)
    if not match:
        raise ValueError(f"unsupported Vector ASC CAN line: {line.rstrip()}")

    data_bytes = match.group("data").split()
    dlc = int(match.group("dlc"))
    if len(data_bytes) != dlc:
        raise ValueError(f"ASC DLC/data mismatch: dlc={dlc}, bytes={len(data_bytes)}")

    arbitration_id = int(match.group("id"), 16)
    is_extended = bool(match.group("ext")) or arbitration_id > 0x7FF

    return CanonicalCanFrame(
        timestamp_ns=seconds_to_ns(match.group("ts")),
        timestamp_provenance="capture_tool_timestamp",
        source_format="vector_asc",
        channel=f"asc:{match.group('channel')}",
        direction=match.group("dir"),
        arbitration_id=arbitration_id,
        is_extended_id=is_extended,
        is_remote_frame=False,
        dlc=dlc,
        data_hex="".join(data_bytes).upper(),
    )


def import_lines(lines: Iterable[str], *, source_format: str) -> list[CanonicalCanFrame]:
    parser = {
        "candump": parse_candump_line,
        "vector_asc": parse_vector_asc_line,
    }.get(source_format)
    if parser is None:
        raise ValueError(f"unsupported source format: {source_format}")

    frames: list[CanonicalCanFrame] = []
    previous_ns: int | None = None
    for line in lines:
        frame = parser(line)
        if frame is None:
            continue
        if previous_ns is not None and frame.timestamp_ns < previous_ns:
            raise ValueError("capture timestamps must be monotonic within an imported stream")
        previous_ns = frame.timestamp_ns
        frames.append(frame)
    return frames


def build_capture_document(
    frames: list[CanonicalCanFrame],
    *,
    capture_id: str,
    clock_domain: str,
    adapter: str,
    listen_only: bool | None,
    capture_quality: str = "UNKNOWN",
    filter_mode: str = "UNKNOWN",
    rx_queue_depth: int | None = None,
    rx_dropped_count: int | None = None,
    rx_overflow_count: int | None = None,
) -> dict:
    if capture_quality not in CAPTURE_QUALITIES:
        raise ValueError(f"unsupported capture_quality: {capture_quality}")
    if filter_mode not in FILTER_MODES:
        raise ValueError(f"unsupported filter_mode: {filter_mode}")
    for name, value in (
        ("rx_queue_depth", rx_queue_depth),
        ("rx_dropped_count", rx_dropped_count),
        ("rx_overflow_count", rx_overflow_count),
    ):
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
            raise ValueError(f"{name} must be a non-negative integer or null")
    if capture_quality == "FULL_RATE_CANDIDATE" and (rx_dropped_count not in (0, None) or rx_overflow_count not in (0, None)):
        raise ValueError("FULL_RATE_CANDIDATE cannot declare observed drops or overflows")

    return {
        "schema_version": 2,
        "capture_id": capture_id,
        "mode": "read_only_can_capture_import",
        "clock_domain": clock_domain,
        "adapter": adapter,
        "listen_only": listen_only,
        "capture_quality": capture_quality,
        "filter_mode": filter_mode,
        "rx_queue_depth": rx_queue_depth,
        "rx_dropped_count": rx_dropped_count,
        "rx_overflow_count": rx_overflow_count,
        "frame_count": len(frames),
        "frames": [asdict(frame) for frame in frames],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert receive-only candump or Vector ASC logs into a canonical CAN frame document"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--format", choices=("candump", "vector_asc"), required=True)
    parser.add_argument("--capture-id", required=True)
    parser.add_argument("--clock-domain", default="capture_tool_clock")
    parser.add_argument("--adapter", default="UNSPECIFIED")
    parser.add_argument("--listen-only", choices=("true", "false", "unknown"), default="unknown")
    parser.add_argument("--capture-quality", choices=tuple(sorted(CAPTURE_QUALITIES)), default="UNKNOWN")
    parser.add_argument("--filter-mode", choices=tuple(sorted(FILTER_MODES)), default="UNKNOWN")
    parser.add_argument("--rx-queue-depth", type=int)
    parser.add_argument("--rx-dropped-count", type=int)
    parser.add_argument("--rx-overflow-count", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    listen_only = {"true": True, "false": False, "unknown": None}[args.listen_only]
    frames = import_lines(args.input.read_text(encoding="utf-8").splitlines(), source_format=args.format)
    document = build_capture_document(
        frames,
        capture_id=args.capture_id,
        clock_domain=args.clock_domain,
        adapter=args.adapter,
        listen_only=listen_only,
        capture_quality=args.capture_quality,
        filter_mode=args.filter_mode,
        rx_queue_depth=args.rx_queue_depth,
        rx_dropped_count=args.rx_dropped_count,
        rx_overflow_count=args.rx_overflow_count,
    )
    args.output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
