# Project Status — 2026-09-06

Repository: `freddykat/f13-autonomy`

Current main at start of this status update:

`22a9236adc065977e264a63f5a3c157a6982570b`

## Executive status

The project has moved from broad architecture into a structured pre-vehicle reverse-engineering and integration phase.

The current executable boundary is:

```text
Comma Four / openpilot
        +
BMW CAN/FlexRay passive observation
        +
offline signal discovery
        +
cross-session evidence
        +
read-only BMW CarState/RadarData preparation
        +
BMWControlIntent SHADOW
```

There is still **no BMW actuation path**.

The first real-car objective remains a synchronized F13 observation/shadow dataset in December 2026.

## Upstream openpilot baseline

Current published upstream release:

- openpilot v0.11.1

Prototype 001 currently pins the reviewed official `zeroeleventwo` branch commit:

- openpilot: `044640668aa25d5c72f948ec072bfc259d1b269a`
- opendbc: `b4ef5e1cf406ff143fa67bdbfb154739d43279c9`
- Panda: `dd8a5b3df77706337a11555377e7180c5adc8726`

The pinned `zeroeleventwo` commit must not be described as a published v0.11.2 tag unless upstream publishes that tag.

## BMW signal research stack

The passive discovery chain now includes:

1. BMW signal research matrix
2. semantic target map
3. offline byte/bit correlation
4. continuous integer correlation
5. relational event correlation
6. FRR-specific relational correlation
7. FRR range/velocity field pairing
8. FRR track hypothesis assembly
9. transport-aware CAN/FlexRay frame model
10. transport-aware function identifier
11. cross-session evidence aggregation
12. CAN/FlexRay cross-transport correspondence
13. transport availability summary
14. request/feedback topology inference

The architecture deliberately preserves FlexRay channel/slot/cycle/schedule provenance rather than flattening FlexRay into fake CAN addresses.

## Merged implementation sequence

Recent merged main milestones:

- BMW signal research matrix
- BMW semantic correlation map
- offline BMW signal correlation analyzer
- continuous BMW signal correlation analyzer
- relational BMW signal correlation analyzer
- FRR relational signal correlation analyzer
- FRR range/velocity field pairing
- passive FRR track hypothesis builder
- transport-aware BMW function hypothesis identifier
- BMW cross-session function evidence engine
- BMW CAN/FlexRay cross-transport correspondence analyzer
- BMW transport availability summary
- BMW control architecture research boundary
- passive BMW request/feedback topology analyzer
- minimal Comma Four F13 Beta 1 hardware policy
- minimal BMW F13 Beta 1 software port policy

## Current control boundary

Defined domains:

- lateral steering
- longitudinal
- indicators
- parking steering
- parking longitudinal
- gear selection
- brake hold

Current allowed authority states:

- `DISABLED`
- `SHADOW`
- `HIL_ONLY`

Current live actuation authority:

`NONE`

The repository CI explicitly rejects premature control definitions in the research manifests.

## Beta 1 hardware baseline

Required:

1. Comma Four
2. independent passive CAN logger
3. protected removable power/breakout harness
4. ENET diagnostic access

Conditional:

5. passive FlexRay RX, only if CAN/ZGW evidence proves insufficient or ambiguous

Recommended when needed:

6. independent GNSS/IMU reference

Deferred from the Beta 1 critical path:

- KAFAS2 retrofit
- surround cameras
- LiDAR/depth
- Chestnut/eGPU
- Tesla HW4 benchmark hardware
- parking actuation hardware

## Beta 1 software baseline

Required:

- locked upstream openpilot baseline
- BMW transport-aware ingest
- core BMW ego-state decoders
- `BMWVehicleState`
- read-only `bmw_carstate`
- read-only `bmw_interface`
- `dashcamOnly = true`
- `BMWControlIntent` shadow output
- deterministic replay

Conditional:

- FRR `RadarData`
- SWW/HC2 blind-spot adapter
- FlexRay ingest

Explicitly absent:

- BMW `CarController`
- `sendcan`
- CAN TX encoder
- FlexRay TX encoder
- diagnostic writes
- EPS/DSC/DME actuation
- gear actuation
- parking actuation

## December 2026 real-car objective

First controlled observation run:

`F13 Observation Run 001`

Priority events:

- ACC ON/OFF
- set-speed changes
- following-gap changes
- lead acquire/loss
- lead opening/closing/steady
- blind-spot left/right enter/exit
- steering left/right/center
- gentle left/right curves
- steady speed
- controlled acceleration/deceleration
- brake press/release
- gear states where safe and stationary

Capture order:

1. CAN/ZGW/OBD inventory
2. ENET/HSFZ read-only corroboration
3. passive FlexRay only where CAN evidence is insufficient
4. synchronized Comma/model output
5. raw evidence correlation
6. cross-session evidence
7. transport availability classification
8. request/feedback topology analysis
9. decoder evidence gate
10. read-only openpilot adapter replay

## Biggest unresolved technical questions

### Steering

- exact F13 actuator topology
- hydraulic Active Steering vs retrofit EPS final architecture
- which steering request/state signals are CAN-visible
- which are FlexRay-only
- whether ICM/ZGW exposes sufficient state for a conventional openpilot port
- driver torque/override and rear-steer/IAS interaction

### Longitudinal

- how much ACC state and selected-lead/full-track data is exposed through CAN/ZGW
- whether the OEM ACC setpoint path can serve as the first controlled longitudinal strategy
- exact FRR/ICM/DSC/DME request/feedback topology

### FlexRay

- which functions are truly FlexRay-only
- whether a runtime FlexRay semantic adapter is required
- whether CAN representations are forwarded, derived, or independently produced

### Parking/body

- Parking High/PDC observation path
- indicator request/feedback path
- gear/EGS/GWS state topology
- later low-speed steering/brake control architecture

## Upstream contribution strategy

The project should not propose one large BMW/FlexRay pull request.

Preferred upstream sequence:

1. small generic offline tooling improvements where they benefit openpilot/opendbc generally
2. read-only BMW brand-port scaffolding only after real signal evidence exists
3. small, reviewable `CarState` changes
4. small radar/SWW additions
5. FlexRay transport discussion/prototype separately
6. no control/safety PR until the actuator protocol, replay and HIL evidence are mature

## Collaboration target

The highest-value external collaboration is currently:

- comma/openpilot car-interface developers
- openpilot community car-port maintainers
- BMW F-series CAN/FlexRay specialists
- passive FlexRay tooling developers

The strongest pitch is not “please support our BMW.”

It is:

> We are building a reproducible, read-only BMW F-series research corpus and transport-aware tooling that may reduce the technical cost of a future BMW/FlexRay openpilot brand port.

## Current project state

```text
architecture                 STRONG
offline/replay tooling       STRONG
BMW passive discovery        STRONG PRE-VEHICLE
CAN/FlexRay abstraction      IMPLEMENTED
FRR hypothesis tooling       IMPLEMENTED
control-intent architecture  IMPLEMENTED SHADOW-ONLY
Beta 1 scope                 DEFINED
real F13 signal validation   NOT STARTED
real BMW CarState            NOT VALIDATED
real BMW RadarData           NOT VALIDATED
BMW actuation                NOT IMPLEMENTED
HIL actuation                NOT IMPLEMENTED
closed-course actuation      NOT STARTED
```

The project is now ready for focused pre-vehicle preparation and external technical review rather than additional broad architecture expansion.
