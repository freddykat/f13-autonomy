# FlexRay trace conversion and timing provenance

Status: offline/read-only validation tooling only.

## Purpose

The golden-trace comparator operates on one canonical record shape. Real capture tools export different CSV/text layouts, so raw logs must be normalized without inventing information that the source never measured.

Canonical minimum fields:

```text
host_time_ns
capture_sequence
channel
cycle
slot_id
payload_length
payload_hex
source
```

Additional provenance fields are allowed and encouraged.

## pico-flexray recorder

`dynm/pico-flexray/flexray_stream_recorder.py` currently exports:

```text
timestamp, source, indicators, frame_id, payload_length_words,
header_crc, cycle_count, payload, frame_crc
```

`validation/flexray_trace_convert.py::convert_pico_csv()` maps:

- `frame_id -> slot_id`
- `cycle_count -> cycle`
- `payload_length_words * 2 -> payload_length`
- `payload -> payload_hex`
- row ordinal -> `capture_sequence`
- `source` is retained as `source_endpoint`

### Critical timing limitation

The upstream recorder creates `batch_timestamp = datetime.now().isoformat()` once per USB read and assigns that same timestamp to every parsed frame in that USB batch.

Therefore the current CSV is suitable for testing frame presence, ordering, cycle/slot coverage and payload fidelity, but it does **not** provide trustworthy per-frame receive timestamps.

The converter deliberately preserves identical timestamps for frames from the same batch and labels them:

```text
timing_provenance = usb_batch_wall_clock
```

It must not interpolate or synthesize nanosecond frame times.

Until upstream capture exposes per-frame timestamps generated close to the RP2040/receive path, a candidate using this recorder cannot earn timing-based trust solely from the CSV. Frame fidelity and timing fidelity must be scored separately.

## Vector/CANoe or other reference exports

There is no single assumed CSV schema. Tool versions and export configurations differ.

Use `convert_mapped_csv()` with an explicit mapping from the actual export columns to canonical fields. Required mappings are:

- `timestamp`
- `slot_id`
- `payload`

Optional mappings:

- `channel`
- `cycle`
- `payload_length`
- `capture_sequence`

Timestamp units must be supplied explicitly through `timestamp_scale_ns`.

Example conceptual mapping:

```python
columns = {
    "timestamp": "Time_us",
    "channel": "Channel",
    "cycle": "Cycle",
    "slot_id": "Slot",
    "payload": "Data",
}
```

Do not copy this mapping blindly; inspect the real export header first.

## Promotion rule

A comparison report must retain two separate conclusions:

1. **frame fidelity** — missing/extra frames, slot/cycle coverage, payload bytes;
2. **timing fidelity** — only when both capture sources expose independently meaningful per-frame timestamps.

A tool may be useful as `OBSERVATION_ONLY` even when timing fidelity is unavailable. Missing timing provenance must never be converted into a false high-confidence timestamp.

No conversion or comparison result grants transmit, MITM, EPS, DSC, steering, braking or other control authority.
