# M1 Observation Episode Import Contract

Status: read-only development tooling

`validation/observation_episode_importer.py` is the boundary between raw/decoded capture tooling and the deterministic M1 observation corpus.

It does **not** transmit CAN, FlexRay, diagnostic jobs, EPS requests, DSC requests or actuator commands. It only normalizes already-observed data.

## Why this exists

The same physical quantity may arrive through sources with very different temporal meaning:

- passive CAN/FlexRay frame capture
- ENET/HSFZ/UDS diagnostic response
- independent GNSS/IMU
- offline perception / visual odometry

A plausible numeric value is not enough to call two sources independent corroboration. The importer therefore preserves clock-domain and timing provenance before the existing cross-source validator evaluates agreement.

## Source specification

Every source stream declares:

- `source`: stable source name
- `clock_domain`: e.g. `host_monotonic`, `rp2040_monotonic`, `gnss_time`, `unknown`
- `timing_provenance`
- `calibration_version`
- `decoder_version`

Accepted timing provenance tokens currently include:

- `per_sample_monotonic`
- `per_frame_monotonic`
- `diagnostic_response_time`
- `usb_batch_wall_clock`
- `unknown`

The latter three are preserved but are **not** accepted by the default tight cross-source motion policies.

## Observation provenance

Every normalized observation carries:

- signal / value / unit
- validity and confidence
- sample timestamp, when actually known
- receive timestamp
- timing provenance
- clock domain
- calibration version
- decoder version
- capture ID

Missing sample timing remains `None`. The importer must never synthesize a per-sample timestamp from a USB batch timestamp, diagnostic response time or file order.

## ENET boundary

Diagnostic reads may be highly useful for checking semantic meaning and scaling of an ICM/DSC value. Unless the ECU/job exposes a measurement timestamp whose semantics are understood, the host response time is `diagnostic_response_time`, not `per_sample_monotonic`.

This prevents a slow diagnostic transaction from being counted as tight temporal corroboration against IMU or passive bus data.

## Initial flow

```text
raw/passive capture or decoded export
              |
              v
observation_episode_importer
              |
              v
M1 canonical observation episode
              |
              v
observation_corpus_runner
              |
              v
AGREE / DISAGREE / SINGLE_SOURCE / UNKNOWN
```

## Promotion rule

Import success is not signal validation. Cross-source agreement is not actuation authority. Safety-relevant state still needs real F13 calibration, repeatability, source-loss handling and replay regression before promotion into an authoritative `BMWVehicleState` field.

## Next adapters

Adapters should be added only for documented read-only exports, for example:

1. canonical FlexRay trace -> decoded observation stream
2. SocketCAN/candump/ASC -> decoded CAN observation stream
3. ENET measurement export -> diagnostic observation stream
4. GNSS/IMU CSV -> independent motion observation stream

Each adapter must declare what clock it is using instead of silently mapping wall-clock or arrival order into measurement time.
