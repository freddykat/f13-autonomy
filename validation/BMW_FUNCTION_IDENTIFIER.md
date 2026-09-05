# BMW Transport-Aware Function Identifier

## Purpose

This tool prepares the F13 project for the possibility that important BMW
signals are visible only on FlexRay, while others are available through
CAN/ZGW/OBD. It performs passive, offline discovery only.

The core rule is:

> preserve transport first; assign semantics only after evidence.

FlexRay is not converted to a fake CAN address. Channel, slot, cycle or schedule
identity, and optional frame ID remain part of provenance.

## Trace formats

Legacy CAN JSONL remains supported:

```json
{"t":12.345,"bus":"can0","address":291,"data":"00112233"}
```

Explicit CAN:

```json
{"t":12.345,"transport":"CAN","bus":"can0","address":291,"data":"00112233"}
```

FlexRay:

```json
{"t":12.345,"transport":"FLEXRAY","channel":"A","slot_id":77,"cycle":3,"data":"00112233"}
```

When known, a repeating FlexRay schedule may also record:

```json
{
  "t":12.345,
  "transport":"FLEXRAY",
  "channel":"A",
  "slot_id":77,
  "cycle":6,
  "base_cycle":2,
  "cycle_repetition":4,
  "frame_id":123,
  "data":"00112233"
}
```

If schedule metadata is absent, the observed FlexRay cycle stays in the
correlation key so different cycle multiplexes cannot be merged accidentally.

## Function signatures

Function signatures are event relationships, not verified decoders.

Examples:

- `STEERING_LIKE`: left vs right, with center as baseline.
- `YAW_LIKE`: left curve vs right curve, with straight as baseline.
- `LEAD_RANGE_LIKE`: lead opening vs closing, with steady lead as baseline.
- `BLINDSPOT_LEFT_STATE_LIKE`: enter vs exit toggle.
- `BRAKE_STATE_LIKE`: press vs release toggle.

The initial catalog is:

`validation/manifests/prototype_001_bmw_function_signatures.json`

The `_LIKE` suffix is intentional. A high score means "behavior resembles this
event signature", not "this BMW signal has been decoded".

## Running

```bash
python tools/bmw_function_identifier.py \
  capture.jsonl markers.json \
  --signatures validation/manifests/prototype_001_bmw_function_signatures.json \
  --output function_hypotheses.json
```

Output contains transport provenance, raw feature location, score components,
observation counts, and raw polarity.

## December workflow

Recommended controlled observation sequence:

1. record synchronized CAN and passive FlexRay;
2. add event markers while the driver performs repeatable safe maneuvers;
3. run the function identifier;
4. compare top hypotheses across repeated sessions;
5. corroborate with read-only BMW diagnostics and independent sensors;
6. only then promote a candidate into the separate decoder evidence process.

Useful repeated events include steering left/right/center, gentle left/right
curves, steady speed/acceleration/deceleration, ACC on/off, gap up/down, lead
closing/opening/steady/loss, blind-spot enter/exit, and brake press/release.

## Safety boundary

The identifier has no transmit path and no live vehicle-control role.

It does not:

- generate a DBC;
- assign engineering scale, offset, or unit;
- create openpilot `CarState` or `RadarData`;
- issue diagnostic writes;
- transmit CAN or FlexRay;
- create a BMW `CarController`;
- grant actuation authority;
- auto-promote a hypothesis.

All results remain `UNVALIDATED_FUNCTION_HYPOTHESIS` until real-car evidence
passes the project's validation gates.
