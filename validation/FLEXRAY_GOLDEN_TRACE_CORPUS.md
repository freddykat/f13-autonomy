# FlexRay Golden-Trace Corpus

Status: M1 passive-capture validation

This corpus is for receive-only adapter qualification. It does not define or enable FlexRay transmission, MITM forwarding, EPS control, DSC control, or any other vehicle actuation.

## Purpose

A candidate FlexRay logger should not become an authoritative input merely because it can print plausible-looking frames. It must be compared against a known-good reference capture of the same physical bus interval.

`validation/flexray_trace_compare.py` provides the first offline comparator for that purpose.

## Required paired capture

For each corpus item, record the same physical FlexRay traffic simultaneously with:

- a reference interface, preferably Vector/CANoe or another independently trusted tool; and
- the candidate interface under evaluation.

Do not compare two drives or two separately replayed sessions and call them a fidelity test. The streams must represent the same bus interval.

## Canonical record fields

Both sides should be converted into the canonical records already consumed by `flexray_capture_validator.py`:

- `host_time_ns`
- `capture_sequence`
- `slot_id`
- `cycle`
- `payload_length`
- `payload_hex`
- `channel`
- `source`

Preserve original raw files alongside the normalized representation.

## Corpus manifest

Each paired trace should include a small manifest containing at least:

- corpus item ID
- date
- vehicle/platform or bench source
- network/channel under test
- reference adapter model + software version
- candidate adapter hardware + firmware commit
- capture host OS/kernel where relevant
- physical tap description
- listen-only configuration evidence
- nominal FlexRay cluster/config provenance
- start/stop method
- host load/storage load condition
- raw file hashes
- normalized file hashes
- notes about known source errors or discontinuities

For vehicle-derived captures, omit public VIN/location/personally identifying information.

## Comparison method

The comparator aligns frames by:

`channel + cycle + slot_id + occurrence ordinal`

The occurrence ordinal prevents repeated cycle/slot tuples from being silently collapsed when cycle counters wrap or a capture includes repeated identifiers.

It reports:

- missing frames
- extra frames
- payload mismatches
- payload-length mismatches
- matched frame count
- constant inter-host clock offset
- residual timing error after removing that constant offset

A constant clock offset is expected when two independent capture computers are used and is not by itself a fidelity failure.

## Qualification labels

The current comparator can return:

- `REJECTED`
- `OBSERVATION_ONLY`
- `REPLAY_TRUSTED`
- `STATE_SOURCE_CANDIDATE`

These are passive-data trust labels only. None grants actuation authority.

Current timing defaults are engineering placeholders:

- state-source candidate: max residual <= 2 ms
- replay trusted: max residual <= 10 ms

They are deliberately configurable and must be replaced/tightened when real F13 measurement requirements are established.

Frame/payload fidelity is stricter: any missing, extra, length-mismatched or byte-mismatched frame prevents `REPLAY_TRUSTED` and `STATE_SOURCE_CANDIDATE` under the current policy.

## Minimum corpus progression

### G0 — synthetic

Generated canonical records exercise parser/comparator behavior and clock offset/jitter math.

### G1 — bench replay

A deterministic FlexRay source is captured simultaneously by reference and candidate adapters.

### G2 — quiet vehicle state

Passive capture with ignition/network awake but without deliberate dynamic manoeuvres.

### G3 — representative bus load

Passive capture during a controlled private-area drive or equivalent HIL traffic. The autonomy system remains receive-only.

### G4 — stress

Repeat paired capture while stressing candidate host CPU, USB and storage separately. Drops must become observable rather than silently disappearing.

## Promotion evidence

An adapter cannot become a `STATE_SOURCE_CANDIDATE` from a single short clean trace. Store multiple corpus items covering different durations/load conditions and retain the raw evidence needed to reproduce the comparison.

The first practical blocker is a paired F-series trace captured simultaneously by pico-flexray (or another low-cost candidate) and a trusted Vector/CANoe-class reference interface.
