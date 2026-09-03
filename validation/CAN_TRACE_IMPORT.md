# CAN trace import boundary

`validation/can_trace_import.py` converts receive-only CAN capture exports into a canonical raw-frame document.

Supported initial inputs:

- Linux `candump` classic text form such as `(12.345678901) can0 123#11223344`
- common Vector ASC classic-CAN `Rx`/`Tx` data lines such as `0.123456 1 123 Rx d 8 11 22 33 44 55 66 77 88`

## Deliberate boundary

This importer does **not** decode BMW signal meaning.

Raw capture:

`candump / Vector ASC -> canonical CAN frames -> verified decoder -> observation episode importer -> cross-source validation -> BMWVehicleState candidate`

This separation prevents unverified arbitration IDs, offsets, scaling or sign conventions from being silently promoted into vehicle state.

## Canonical frame fields

Every imported frame preserves timestamp in integer nanoseconds, timestamp provenance, source format, channel/interface, direction, arbitration ID, standard/extended classification, DLC and exact payload bytes.

## Capture-quality provenance

Schema version 2 makes recorder quality explicit instead of asking downstream code to infer it from an apparently plausible trace.

Each capture records:

- `capture_id`
- `clock_domain`
- adapter name
- `listen_only = true / false / null`
- `capture_quality`
- `filter_mode`
- `rx_queue_depth`
- `rx_dropped_count`
- `rx_overflow_count`

Allowed quality states are:

- `UNKNOWN` — acquisition quality has not been characterized
- `LOSSY` — known or strongly evidenced recorder loss; useful for exploration only
- `OBSERVATION_ONLY` — suitable for qualitative observation but not full-rate/timing claims
- `FULL_RATE_CANDIDATE` — acquisition path has evidence consistent with complete frame capture, still subject to independent validation

Allowed filter provenance is `UNKNOWN`, `ACCEPT_ALL`, `SINGLE_ID_HARDWARE`, `MULTI_ID_HARDWARE` or `SOFTWARE`.

A `FULL_RATE_CANDIDATE` cannot simultaneously report a non-zero drop or overflow counter. Missing counters remain `null`; `null` never means zero.

This distinction is motivated by real automotive logger behavior: a decoder may be correct while an undersized receive queue silently drops frames and falsifies apparent message cadence. Capture quality is therefore independent of decoder confidence.

## Timing semantics

`capture_tool_timestamp` means only that the capture tool supplied the timestamp. It does not prove that the timestamp was generated in the CAN controller, adapter firmware, USB driver or host process.

Hardware/driver characterization must therefore occur before timestamps are used for tight cross-source agreement. Non-monotonic timestamps within one imported stream are rejected rather than silently reordered.

## Vector ASC scope

ASC is a broad format with variants across Vector products and export settings. The initial parser intentionally accepts a narrow classic-CAN form and rejects unsupported lines instead of guessing.

CAN FD, remote frames, error frames, trigger blocks and alternate ASC layouts should be added only with representative fixture logs.

## Safety constraint

This utility reads files only. It contains no SocketCAN open/send path, diagnostic request path, CAN transmission API, EPS/DSC interface or FlexRay transmission logic.

The offline decoder carries capture-quality provenance into every observation. A `LOSSY` capture can be inspected, but its observations are explicitly marked `LOSSY_CAPTURE_ONLY`; capture quality can never increase decoder authority and never creates actuation authority.

Any future decoded BMW signal entering `BMWVehicleState` remains subject to the cross-source promotion gate in `validation/CROSS_SOURCE_OBSERVATION_VALIDATION.md`.
