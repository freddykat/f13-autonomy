# Prototype 001 — Beta 1 Minimum Hardware

Status: minimum useful real-car validation rig.

Beta 1 is intentionally smaller than the full M1/M2 sensor plan. The goal is to prove the BMW compatibility layer around an essentially stock Comma Four/openpilot runtime before buying the rest of the desired hardware.

## Required now

### 1. Comma Four

Role:

- primary front road perception;
- driver monitoring;
- openpilot runtime;
- local logging;
- GPS/IMU reference;
- eventual openpilot vehicle interface host.

Current official shop price reference on 2026-09-06: USD 899 before local tax/import/currency effects.

### 2. Independent passive BMW CAN logger

Recommended development path:

- isolated CAN interface;
- separate logger computer;
- read-only harness;
- reliable timestamps;
- raw capture saved independently of the Comma runtime.

Why keep this separate initially:

- unsupported F13 port work must not depend on one experimental software path;
- raw evidence must survive an openpilot crash/reboot;
- CAN discovery can continue before the BMW interface is integrated into openpilot;
- it provides an independent truth source for replay.

Existing M1 BOM recommendation remains appropriate:

- Raspberry Pi 5 class SBC;
- 1 TB NVMe;
- isolated PEAK PCAN-USB FD class interface;
- protected automotive power.

### 3. Passive vehicle breakout / power harness

Requirements:

- no loom cutting;
- fused protected power;
- removable service disconnect;
- CAN test/access points;
- labelled topology;
- no actuator-output wiring during Beta 1.

### 4. ENET diagnostic access

Required as a research/corroboration tool, not as the primary real-time control bus.

Uses:

- ECU identity;
- software versions;
- read-only semantic corroboration;
- coding/configuration inventory;
- compare candidate raw signals against BMW diagnostic values.

### 5. FlexRay receive-only capability — conditional purchase

Do not make it a prerequisite for the first CAN inventory.

Purchase/add once real captures prove one of these conditions:

- steering/ICM/IAS state missing from accessible CAN;
- useful FRR object data missing from accessible CAN;
- SWW/parking state missing from accessible CAN;
- request↔feedback topology cannot be resolved without the original FlexRay segment.

Beta 1 architecture must already support it in software, but hardware acquisition is conditional.

## Strongly recommended but not a first-day blocker

### Independent GNSS/IMU reference

Useful for:

- yaw-rate validation;
- acceleration validation;
- timestamp cross-check;
- rear-steer/vehicle-motion reconstruction;
- proving BMW motion state rather than trusting one source.

The existing u-blox F9R-class recommendation remains valid for the measurement program.

It is not required merely to boot openpilot or record first CAN captures.

## Defer from Beta 1

### KAFAS2 retrofit

Reason to defer:

The car currently has no KAFAS. Adding KAFAS2 is useful later as an independent OEM perception source, but it does not solve the first F13 compatibility blocker:

`Can we reliably observe the BMW and map it into openpilot?`

Add after the basic CAN/FlexRay decoder path is working.

### Full 360 camera replacement

Defer until:

- Comma road-camera pipeline is stable;
- BMW state is decoded;
- basic radar/blindspot integration works;
- camera synchronization needs are measured.

### LiDAR/depth

Defer until Scene3D has a real measured requirement.

It is highly useful for parking and independent depth validation but not required to prove the highway-first BMW/openpilot port.

### Chestnut / desktop GPU

Defer until a measured model or Scene3D compute bottleneck exists.

The Comma Four should remain the baseline. External GPU compute is an enhancement, not a prerequisite for BMW transport integration.

### Tesla HW4 benchmark hardware

Not part of Beta 1 critical path.

Any Tesla comparison remains an external teacher/benchmark lane.

### Parking automation hardware

Defer all dedicated parking actuation work.

Parking perception can begin passively later, but automated steering/gear/brake authority is a separate validation program.

## Beta 1 hardware tiers

### B1-0 — bench / pre-car

```text
Comma Four
development computer
repo/replay environment
synthetic CAN/FlexRay traces
```

Purpose:

- openpilot baseline;
- decoder tooling;
- replay;
- function identification;
- control-intent shadow architecture.

### B1-1 — first F13 observation

```text
Comma Four
+
passive CAN logger
+
protected harness/power
+
ENET
```

Purpose:

- vehicle inventory;
- synchronized Comma/openpilot logging;
- CAN signal discovery;
- diagnostic corroboration.

This is the minimum real-car basket.

### B1-2 — transport-complete observation

Add:

```text
passive FlexRay RX
+
independent GNSS/IMU if not already installed
```

Only when CAN-only evidence proves insufficient or ambiguous.

### B1-3 — BMW shadow port

No additional perception hardware required if existing BMW/Comma observations are sufficient.

Software target:

```text
BMW CAN/FlexRay
      ↓
validated observation decoders
      ↓
CarState + RadarData
      ↓
stock-ish openpilot
      ↓
BMWControlIntent SHADOW
```

## What Beta 1 should demonstrate

A successful Beta 1 is not autonomous driving.

It is a real F13 replay where we can show, with synchronized provenance:

- Comma road perception;
- driver monitoring;
- BMW speed;
- steering state;
- yaw/acceleration;
- pedals;
- ACC state;
- lead/radar evidence where available;
- blind-spot state where available;
- transport source (CAN/FlexRay);
- openpilot proposal;
- BMW shadow control intent;
- request↔feedback topology candidates;
- no vehicle command path.

## Minimal purchase logic

Buy immediately:

1. Comma Four;
2. passive CAN logger/interface;
3. protected power/harness;
4. storage;
5. ENET cable/interface.

Buy after first evidence:

6. FlexRay RX hardware;
7. independent GNSS/IMU if motion validation needs it.

Do not buy for Beta 1 unless a blocker appears:

8. KAFAS2;
9. surround cameras;
10. LiDAR/depth;
11. Chestnut/eGPU;
12. Tesla HW4 hardware;
13. parking actuator hardware.

## Cost perspective

The approximately USD 899 Comma Four is therefore not competing with the entire F13 project.

It replaces a large amount of hardware/software we would otherwise have to design ourselves:

- cameras;
- driver monitoring;
- model compute;
- GPS/IMU;
- logging UI;
- openpilot runtime.

The BMW-specific spend should be concentrated on **access, decoding, validation and only later actuation**, not on duplicating what the Comma already does well.
