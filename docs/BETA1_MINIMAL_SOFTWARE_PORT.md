# Prototype 001 — Beta 1 Minimal Software Port

## Goal

Define the smallest software path that turns a stock Comma Four from a useful standalone openpilot sensor/computer into a BMW F13-aware shadow integration.

The Beta 1 software target remains read-only.

## Stage comparison

### C0 — Comma Four only

```text
Comma Four
  |
  +--> road cameras
  +--> driver monitoring
  +--> GPS/IMU
  +--> model/planner runtime
  +--> local logging
```

Useful immediately, but the BMW remains unknown to the software.

Missing:

- validated BMW speed;
- steering state;
- pedals;
- ACC state;
- BMW radar;
- blind spot;
- BMW health;
- actuator path.

### B1-S0 — transport ingest

Add:

```text
BMW CAN
  |
  v
transport-aware passive ingest
```

Conditional:

```text
BMW FlexRay
  |
  v
transport-aware passive ingest
```

Required output:

- raw frames;
- timestamps;
- source/bus/channel/slot/cycle provenance;
- freshness/drop information.

No semantic decoder is required yet.

### B1-S1 — core BMW state

Add validated read-only decoders for the minimum ego state:

- vehicle speed;
- steering wheel/front steer angle where available;
- yaw rate;
- longitudinal/lateral acceleration;
- brake pedal;
- accelerator position;
- gear;
- DSC/ICM/EPS health/state.

Output:

```text
BMWVehicleState
```

This is the minimum point where the Comma/openpilot proposal can be compared meaningfully with actual F13 motion.

### B1-S2 — openpilot read-only adapter

Add:

- `bmw_carstate`;
- `bmw_interface`;
- `dashcamOnly = true`;
- no `CarController`;
- no `sendcan`.

Target:

```text
validated BMWVehicleState
      ↓
BMW CarState adapter
      ↓
openpilot CarState
      ↓
openpilot proposal / replay
```

At this stage the car is still human/OEM controlled.

### B1-S3 — OEM ADAS observations

Add when validated:

- FRR/ACC radar adapter;
- SWW/HC2 blind-spot adapter;
- ACC state/set-speed/following-gap;
- KAFAS2 later if fitted.

Target:

```text
BMW FRR evidence
      ↓
RadarData

BMW SWW evidence
      ↓
leftBlindspot / rightBlindspot
```

FRR track output is optional for the earliest Beta 1 pass if only selected-lead evidence is available. Full `RadarData` promotion requires real track validation.

### B1-S4 — BMW shadow-control intent

Use openpilot proposals to populate:

```text
BMWControlIntent
```

with per-domain authority fixed to:

- `SHADOW` or
- `DISABLED`.

No encoder consumes this output.

This stage allows comparison of:

```text
openpilot proposal
vs
human action
vs
BMW actual response
```

without commanding the car.

## Minimum Beta 1 software basket

Required:

1. locked/reproducible Comma Four openpilot baseline;
2. transport-aware passive BMW capture;
3. validated core BMW ego-state decoders;
4. `BMWVehicleState`;
5. read-only `bmw_carstate`;
6. read-only `bmw_interface` with `dashcamOnly`;
7. synchronized replay;
8. `BMWControlIntent` shadow output.

Conditional:

9. FlexRay ingest;
10. FRR `RadarData`;
11. SWW blind-spot;
12. independent GNSS/IMU corroboration.

Deferred:

13. `CarController`;
14. CAN command encoder;
15. FlexRay command encoder;
16. EPS/DSC/DME actuation;
17. parking controller;
18. gear authority.

## What changes versus a supported openpilot car

A supported car already has the missing middle:

```text
Comma
  ↓
known vehicle interface
  ↓
known CarState
  ↓
known safety model
  ↓
known CarController
  ↓
vehicle actuators
```

For the F13, Beta 1 is building and validating only:

```text
known vehicle interface
+
known CarState
+
BMW radar/blindspot observations
```

The actuator half remains intentionally absent.

## Beta 1 acceptance

Beta 1 software is considered successful when a recorded real F13 drive can be replayed deterministically and show:

- synchronized Comma video/model output;
- validated BMW ego state;
- transport provenance;
- openpilot `CarState`;
- openpilot proposal;
- BMW radar/blind-spot state where validated;
- BMW shadow control intent;
- human action;
- measured BMW response;
- no vehicle actuation path.

This establishes that the USD 899-class Comma hardware can remain the main openpilot computer while our software supplies the BMW-specific integration layer.
