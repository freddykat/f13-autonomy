# Passive FlexRay Capture Conformance Contract

Status: M1 / receive-only validation

Purpose: evaluate any FlexRay capture interface (commercial or open-source) with the same deterministic, non-actuating criteria before its data is trusted by `bmwstated`, `motionvalidatord`, replay tooling, or later HIL work.

## Safety boundary

This contract covers receive-only capture and offline replay.

Out of scope:
- transmitting FlexRay frames to the vehicle
- MITM modification of frames
- EPS/DSC/ICM/HSR actuation
- replay onto a live vehicle bus
- command-generation validation

An interface may support transmission, but the M1 test configuration must not require or exercise it.

## Canonical trace record

Each captured frame is normalized to a transport-neutral record:

```json
{
  "host_time_ns": 1234567890,
  "source_time_ns": 1234567000,
  "channel": "A",
  "slot_id": 42,
  "cycle": 17,
  "payload_hex": "00112233",
  "payload_length": 4,
  "frame_flags": [],
  "capture_sequence": 1234,
  "source": "adapter-name"
}
```

Required fields:
- monotonic `host_time_ns`
- channel identity when observable
- slot ID
- cycle counter when observable
- exact payload bytes and declared length
- monotonically increasing capture sequence
- source/adapter identifier

Optional-but-preserved fields:
- adapter hardware timestamp
- CRC/header status
- sync/startup/frame flags
- physical-layer/error status
- raw vendor metadata

Unknown values remain explicit `null`/`UNKNOWN`; they must not be fabricated.

## Conformance dimensions

### C1 — monotonicity
No timestamp or capture-sequence regression inside a single acquisition epoch.

### C2 — deterministic decode
The same raw input must produce byte-identical canonical records after normalization, excluding intentionally variable file metadata.

### C3 — payload fidelity
For a reference stream, slot/cycle/payload tuples must match the reference interface. No silent byte truncation, padding or endian reinterpretation.

### C4 — loss observability
Drops must be observable through at least one of:
- explicit adapter drop/error counters
- sequence discontinuities generated below the application parser
- independently demonstrated reference mismatch

An adapter that can lose frames silently is not trusted as an authoritative motion-state source.

### C5 — timestamp quality
Measure, do not assume:
- capture jitter relative to a reference interface
- clock drift over a sustained capture
- host-vs-hardware timestamp behaviour
- timestamp behaviour under USB/host load

Initial M1 acceptance target is chosen only after reference measurements. No arbitrary precision claim is hard-coded into production interfaces.

### C6 — source interruption
Disconnect/reconnect or source loss must produce explicit health-state transitions. Stale data must never continue as current state.

### C7 — saturation behaviour
Under worst observed bus/USB/logging load, record:
- maximum sustained frame rate
- dropped records
- queue growth
- CPU utilisation
- storage latency effects

### C8 — replay fidelity
Offline replay from the canonical trace must preserve ordering, timestamps, slot/cycle identity and payload exactly enough for deterministic downstream tests.

## Test phases

### FR-P0 synthetic parser
Feed generated records with known timestamps, cycles and sequence gaps into the validator. No hardware required.

### FR-P1 bench loop/reference
Capture a known repetitive FlexRay source with the candidate and reference interfaces in parallel where practical.

### FR-P2 source-loss test
Remove the source or adapter connection and verify explicit stale/source-loss behaviour.

### FR-P3 host-load test
Repeat capture while CPU, USB and storage are stressed. Compare loss/jitter with baseline.

### FR-P4 recorded BMW passive capture
Only after P0-P3 pass, capture a BMW network receive-only and compare stable slot/cycle statistics across repeated drives/ignition sessions.

## Acceptance states

- `UNASSESSED`: no evidence yet
- `OBSERVATION_ONLY`: useful for exploratory analysis but not authoritative state estimation
- `REPLAY_TRUSTED`: deterministic offline use accepted
- `STATE_SOURCE_CANDIDATE`: loss/timestamp/fidelity behaviour quantified and suitable for further validation
- `REJECTED`: silent loss, non-deterministic decoding, corrupt payloads, or unbounded timestamp faults

None of these states grants vehicle-control authority.

## Adapter evidence bundle

Every adapter evaluation should archive:
- hardware/firmware/software versions
- configuration and wiring mode
- raw capture
- canonical normalized capture
- validator report
- reference-interface comparison if available
- host load and storage conditions
- observed drop/error counters
- test operator notes

## Open-source evaluation

`dynm/pico-flexray` is a relevant candidate because it exposes receive-only capture and Panda-compatible streaming, but M1 adoption depends on measured timestamp, drop/error observability and payload fidelity rather than repository feature claims alone.

Commercial Vector/PEAK-class hardware can be used as a comparison reference where available; vendor status alone does not waive the same evidence requirements.
