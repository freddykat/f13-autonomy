# BMW CAN/FlexRay Cross-Transport Correspondence

## Purpose

This stage tests whether high-confidence CAN and FlexRay function evidence from
the same function family behaves like the same underlying information in one
synchronized passive capture.

It is designed to help answer a key F13 integration question:

> Is a function available directly on CAN, only on FlexRay, or represented on
> both networks through forwarding/derivation?

A strong correspondence is still not proof that ZGW created, forwarded, or owns
the signal. ECU origin remains unresolved until additional topology and
diagnostic evidence exists.

## Inputs

1. A synchronized transport-aware trace accepted by `bmw_transport.py`.
2. Cross-session evidence produced by `bmw_cross_session_evidence.py`.

Only CAN/FlexRay evidence with the same `function_family` is compared.

## Method

For each CAN/FlexRay candidate pair:

1. extract the exact raw field independently on each transport;
2. preserve FlexRay channel/slot/cycle or schedule filtering;
3. search a bounded timing lag;
4. perform unique nearest-neighbor timestamp alignment;
5. compute Pearson correlation;
6. accept either same or inverted raw polarity;
7. score temporal correlation, sample overlap, and prior evidence quality.

Different raw scales and offsets are allowed because correlation is invariant to
linear scale/offset.

## Relationship labels

`STRONG_DUAL_TRANSPORT_CORRESPONDENCE`

Requires strong correlation, sufficient aligned pairs, good overlap, and strong
cross-session evidence.

The associated gateway hypothesis is only:

`POSSIBLE_ZGW_FORWARD_OR_DERIVED_REPRESENTATION`

It does not mean ZGW derivation has been proven.

`POSSIBLE_DUAL_TRANSPORT_CORRESPONDENCE`

A weaker but still interesting relation requiring more evidence.

`WEAK_OR_UNRELATED`

The synchronized raw series do not currently support a useful correspondence.

## Example

```text
FlexRay candidate:
  STEERING_LIKE
  channel A
  slot 77
  cycle 3
  int16 BE

CAN candidate:
  STEERING_LIKE
  can0 / 0x123
  int16 BE

synchronized observation:
  abs correlation = 0.997
  overlap = 0.91
  best lag = -10 ms

result:
  STRONG_DUAL_TRANSPORT_CORRESPONDENCE
  POSSIBLE_ZGW_FORWARD_OR_DERIVED_REPRESENTATION
```

This still leaves multiple physical explanations:

- ZGW forwards the original information;
- ZGW derives/re-encodes it;
- two ECUs publish correlated values from the same source;
- one value is a transformed estimate of the other.

## Running

```bash
python tools/bmw_cross_transport_correspondence.py \
  synchronized_can_flexray.jsonl \
  cross_session_evidence.json \
  --max-lag-ms 100 \
  --lag-step-ms 5 \
  --alignment-tolerance-ms 25 \
  --output cross_transport_correspondence.json
```

## December use

For a candidate such as steering angle:

1. repeat left/right/center events across multiple sessions;
2. build independent CAN and FlexRay evidence;
3. synchronize CAN and passive FlexRay capture;
4. run this correspondence stage;
5. compare timing and raw correlation;
6. corroborate with read-only ICM/ZGW diagnostics;
7. only then decide whether CAN alone is sufficient for the openpilot adapter.

The same method can later be applied to:

- yaw rate;
- vehicle speed;
- ACC state;
- ACC following gap;
- lead range;
- blind-spot state;
- IAS/rear-steer observations.

## Safety boundary

This tool remains offline/read-only.

It does not:

- prove gateway ownership;
- modify BMW coding;
- write diagnostics;
- generate a DBC;
- assign engineering scale/units;
- create `CarState` or `RadarData`;
- transmit CAN;
- transmit FlexRay;
- create a BMW controller;
- grant actuation authority.

Every output remains:

`UNVALIDATED_CROSS_TRANSPORT_CORRESPONDENCE`
