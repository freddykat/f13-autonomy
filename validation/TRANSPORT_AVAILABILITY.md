# BMW Transport Availability Summary

## Purpose

This stage converts passive function evidence into a practical observation-path
summary for the BMW F13 project.

It answers:

- does current evidence show the function on CAN?
- does current evidence show it on FlexRay?
- if both are present, are they strongly correlated?
- does the current evidence suggest that FlexRay translation may be required to
  observe this function?

It does not answer whether a decoder is correct or whether any control path is
safe.

## Inputs

1. Cross-session function evidence from:
   `tools/bmw_cross_session_evidence.py`
2. Optional synchronized CAN/FlexRay correspondence from:
   `tools/bmw_cross_transport_correspondence.py`

## Availability labels

### CAN_EVIDENCE_ONLY

A medium/high-confidence CAN candidate exceeds the evidence threshold while no
equivalent FlexRay candidate does.

Observation recommendation:

`CAN_FIRST`

FlexRay translation is not indicated by current evidence for that function.

### FLEXRAY_EVIDENCE_ONLY

A medium/high-confidence FlexRay candidate exists without comparable CAN
evidence.

Observation recommendation:

`FLEXRAY_REQUIRED_FOR_OBSERVATION`

This is the strongest pre-decoder indication that our BMW compatibility layer
may need a FlexRay semantic translation path for this function.

### DUAL_TRANSPORT_CORRELATED

Strong CAN and FlexRay evidence exists and synchronized raw correlation is
strong.

Observation recommendation:

`CAN_MAY_SUFFICE_PENDING_DECODER_VALIDATION`

This does not prove the CAN representation is identical in meaning, freshness,
validity semantics, or safety quality. FlexRay remains useful for validation.

### DUAL_TRANSPORT_UNRESOLVED

Both transports contain plausible candidates but synchronized evidence has not
shown a strong enough correspondence.

Observation recommendation:

`CAPTURE_BOTH_UNTIL_CORROBORATED`

### INSUFFICIENT_EVIDENCE

Current evidence is not strong enough to make a transport recommendation.

## Example future F13 matrix

```text
Function                 Availability                 Runtime observation
STEERING_LIKE            DUAL_TRANSPORT_CORRELATED    CAN may suffice
YAW_LIKE                 CAN_EVIDENCE_ONLY            CAN first
LEAD_RANGE_LIKE          FLEXRAY_EVIDENCE_ONLY        FlexRay likely required
BLINDSPOT_LEFT_STATE     DUAL_TRANSPORT_UNRESOLVED    capture both
```

These are example states only, not claims about the user's 2012 F13.

## Running

```bash
python tools/bmw_transport_availability.py \
  cross_session_evidence.json \
  --correspondence cross_transport_correspondence.json \
  --output transport_availability.json
```

## Relationship to openpilot

Even when the summary says:

`CAN_MAY_SUFFICE_PENDING_DECODER_VALIDATION`

the openpilot read path remains:

`TRANSPORT_CANDIDATE_ONLY_NOT_DECODER_VALIDATED`

A separate evidence gate is still required before populating BMW `CarState`,
`RadarData`, blind-spot state, or any other openpilot interface.

For functions classified as `FLEXRAY_EVIDENCE_ONLY`, the likely architecture
is:

```text
BMW FlexRay
   ↓
passive FlexRay receiver
   ↓
transport-aware decoder
   ↓
BMW semantic state
   ↓
openpilot read-only adapter
```

not:

```text
FlexRay → fake CAN → openpilot
```

## Safety boundary

This tool does not:

- validate a decoder;
- prove ZGW forwarding or derivation;
- assign engineering units or scaling;
- generate DBCs;
- write diagnostics;
- transmit CAN;
- transmit FlexRay;
- create `CarState` or `RadarData`;
- create a BMW controller;
- grant actuation authority.

All output remains:

`UNVALIDATED_TRANSPORT_AVAILABILITY`
