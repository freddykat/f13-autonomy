"""Offline converters into the canonical passive FlexRay trace schema.

No bus I/O or transmit path exists in this module. It only normalizes already
recorded text/CSV data so candidate capture interfaces can be compared against
reference traces using the validation tooling in this repository.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from io import StringIO
from typing import Iterable, Mapping, TextIO


class TraceConversionError(ValueError):
    pass


def _parse_iso_time_ns(value: str) -> int:
    text = value.strip()
    if not text:
        raise TraceConversionError("empty timestamp")
    # Python accepts ISO-8601 offsets; normalize a trailing Z explicitly.
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise TraceConversionError(f"invalid ISO timestamp: {value!r}") from exc
    if dt.tzinfo is None:
        # pico-flexray currently records datetime.now().isoformat(), i.e. local
        # wall clock with no offset. Treat the numeric value consistently for
        # ordering only; callers must not interpret it as UTC provenance.
        epoch = datetime(1970, 1, 1)
        delta = dt - epoch
    else:
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        delta = dt.astimezone(timezone.utc) - epoch
    return int(delta.total_seconds() * 1_000_000_000)


def _parse_int(value: str, *, field: str) -> int:
    text = value.strip()
    try:
        return int(text, 0)
    except ValueError:
        # Decimal CSV exports often omit the 0x prefix, while some fields can
        # contain values such as "01" that int(..., 0) rejects in Python 3.
        try:
            return int(text, 10)
        except ValueError as exc:
            raise TraceConversionError(f"invalid integer for {field}: {value!r}") from exc


def _normalize_payload(value: str) -> str:
    compact = "".join(value.strip().replace("0x", "").replace("0X", "").split())
    compact = compact.replace("-", "").replace(":", "")
    if len(compact) % 2:
        raise TraceConversionError("payload hex must contain complete bytes")
    try:
        bytes.fromhex(compact)
    except ValueError as exc:
        raise TraceConversionError(f"invalid payload hex: {value!r}") from exc
    return compact.lower()


def convert_pico_rows(rows: Iterable[Mapping[str, str]], *, source_name: str = "pico-flexray") -> list[dict]:
    """Convert rows produced by dynm/pico-flexray flexray_stream_recorder.py.

    Important timing limitation: that recorder assigns one wall-clock timestamp
    per USB read batch, so multiple frames commonly share the same timestamp.
    The converter preserves this behavior; it does not synthesize per-frame
    timing that the source did not measure.
    """
    records: list[dict] = []
    for sequence, row in enumerate(rows):
        required = ("timestamp", "source", "frame_id", "payload_length_words", "cycle_count", "payload")
        missing = [key for key in required if key not in row]
        if missing:
            raise TraceConversionError(f"pico row missing columns: {', '.join(missing)}")

        payload = _normalize_payload(row["payload"])
        payload_length_words = _parse_int(row["payload_length_words"], field="payload_length_words")
        payload_length = payload_length_words * 2
        if len(bytes.fromhex(payload)) != payload_length:
            raise TraceConversionError(
                f"pico payload length mismatch: words={payload_length_words} payload_bytes={len(bytes.fromhex(payload))}"
            )

        records.append(
            {
                "host_time_ns": _parse_iso_time_ns(row["timestamp"]),
                "capture_sequence": sequence,
                "channel": None,
                "cycle": _parse_int(row["cycle_count"], field="cycle_count"),
                "slot_id": _parse_int(row["frame_id"], field="frame_id"),
                "payload_length": payload_length,
                "payload_hex": payload,
                "source": source_name,
                "source_endpoint": _parse_int(row["source"], field="source"),
                "timing_provenance": "usb_batch_wall_clock",
            }
        )
    return records


def convert_pico_csv(stream: TextIO | str, *, source_name: str = "pico-flexray") -> list[dict]:
    handle = StringIO(stream) if isinstance(stream, str) else stream
    return convert_pico_rows(csv.DictReader(handle), source_name=source_name)


def convert_mapped_rows(
    rows: Iterable[Mapping[str, str]],
    *,
    columns: Mapping[str, str],
    source_name: str,
    timestamp_scale_ns: int = 1,
) -> list[dict]:
    """Convert a reference-tool CSV using an explicit column mapping.

    This intentionally does not guess a Vector/CANoe export layout. Export
    formats differ by tool/version/configuration; callers must map canonical
    fields to the actual exported column names.

    Required canonical mappings: timestamp, slot_id, payload.
    Optional mappings: cycle, channel, payload_length, capture_sequence.

    `timestamp` must be an integer-like value and `timestamp_scale_ns` converts
    its unit to nanoseconds (e.g. 1_000 for microseconds).
    """
    for required in ("timestamp", "slot_id", "payload"):
        if required not in columns:
            raise TraceConversionError(f"missing required canonical mapping: {required}")

    records: list[dict] = []
    for ordinal, row in enumerate(rows):
        def get(canonical: str) -> str | None:
            name = columns.get(canonical)
            return None if name is None else row.get(name)

        timestamp_raw = get("timestamp")
        slot_raw = get("slot_id")
        payload_raw = get("payload")
        if timestamp_raw is None or slot_raw is None or payload_raw is None:
            raise TraceConversionError(f"reference row[{ordinal}] missing mapped value")

        payload = _normalize_payload(payload_raw)
        declared_length = get("payload_length")
        payload_length = len(bytes.fromhex(payload)) if declared_length is None else _parse_int(declared_length, field="payload_length")
        if payload_length != len(bytes.fromhex(payload)):
            raise TraceConversionError(f"reference row[{ordinal}] payload length mismatch")

        cycle_raw = get("cycle")
        channel_raw = get("channel")
        sequence_raw = get("capture_sequence")
        records.append(
            {
                "host_time_ns": _parse_int(timestamp_raw, field="timestamp") * timestamp_scale_ns,
                "capture_sequence": ordinal if sequence_raw is None else _parse_int(sequence_raw, field="capture_sequence"),
                "channel": None if channel_raw in (None, "") else str(channel_raw),
                "cycle": None if cycle_raw in (None, "") else _parse_int(cycle_raw, field="cycle"),
                "slot_id": _parse_int(slot_raw, field="slot_id"),
                "payload_length": payload_length,
                "payload_hex": payload,
                "source": source_name,
                "timing_provenance": "reference_export",
            }
        )
    return records


def convert_mapped_csv(
    stream: TextIO | str,
    *,
    columns: Mapping[str, str],
    source_name: str,
    timestamp_scale_ns: int = 1,
) -> list[dict]:
    handle = StringIO(stream) if isinstance(stream, str) else stream
    return convert_mapped_rows(
        csv.DictReader(handle),
        columns=columns,
        source_name=source_name,
        timestamp_scale_ns=timestamp_scale_ns,
    )
