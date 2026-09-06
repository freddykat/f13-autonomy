# Comma Four vs BMW F13 — Capability Gap Matrix

Status: planning baseline for Prototype 001 Beta 1.

This document separates what the Comma Four/openpilot stack already provides from what must be added specifically for the unsupported BMW F13 platform.

As of 2026-09-06, the official comma shop lists the Comma Four at USD 899. The device provides the current openpilot runtime platform, three cameras, GPS/IMU, CAN-FD capability and 128 GB on-device storage. BMW is not listed in the official supported-vehicle catalog.

## Principle

The Comma Four should remain the primary front-vision/openpilot computer.

The F13 project should add only the minimum BMW-specific layers needed to make that software useful on the car.

```text
Comma Four / openpilot
        |
        +--> road vision
        +--> driver monitoring
        +--> planner/model runtime
        +--> GPS/IMU
        +--> logging
        |
        v
BMW compatibility gap
        |
        +--> vehicle-state decoding
        +--> BMW radar/blindspot integration
        +--> CAN/FlexRay transport understanding
        +--> future validated actuator path
```

## Gap matrix

| Capability | Comma Four hardware/runtime provides | Supported-car openpilot normally provides | F13 current state | F13 subsystem needed |
|---|---|---|---|---|
| Front road vision | YES | YES | available immediately | none |
| Driver monitoring | YES | YES | available immediately | custom OEM-style housing only |
| GPS/IMU | YES | YES | available immediately | independent reference optional |
| openpilot model/planner | YES | YES | runs, but vehicle unsupported | BMW interface required |
| CAN/CAN-FD hardware capability | YES | YES | physical access possible | BMW transport/harness validation |
| Vehicle speed / steering / pedals | hardware can receive data | decoded by car port | not validated | BMW CarState decoder |
| Steering actuation | no generic vehicle authority | provided by supported car port | unavailable | validated BMW actuator adapter later |
| Longitudinal actuation | no generic vehicle authority | provided by supported car port | unavailable | OEM ACC-first BMW adapter later |
| BMW ACC radar | no BMW decoder | radar interface where supported | not validated | BMW FRR decoder/RadarData adapter |
| BMW blind spot | no BMW decoder | CarState where supported | not validated | HC2/SWW decoder |
| FlexRay | not a stock openpilot vehicle transport path | generally unnecessary on supported CAN ports | potentially required | passive FlexRay receiver + semantic decoder |
| KAFAS2 | not required | OEM-specific | not fitted currently | optional later corroboration retrofit |
| Surround cameras | not generic multi-camera vehicle coverage | not required | absent from OP path | optional later Scene3D |
| LiDAR/depth | no | no | absent | optional later Scene3D |
| Parking autonomy | no generic parking stack | no | absent | later parkingd + BMW actuator path |
| Automated indicators | vehicle-port dependent | vehicle-specific | unavailable | later BMW body-control adapter |
| Gear selection | no generic authority | generally outside OP | unavailable | late-stage BMW GWS/EGS research |
| Rear-steer awareness | not generic | car-specific if port exposes it | not validated | ICM/IAS state integration |
| BMW diagnostics | no | not required for normal port | useful for research | ENET/EDIABAS read-only corroboration |
| Tesla benchmark | no | no | optional | external benchmark only |
| Desktop GPU / Chestnut | optional | optional | not required for Beta 1 | defer unless measured need |

## What the USD 899 device actually buys us

For Prototype 001 the Comma Four immediately gives us:

- production openpilot compute platform;
- native road-camera system;
- driver-monitoring camera and IR illumination;
- GPS and inertial sensors;
- on-device storage;
- CAN-FD-capable vehicle interface hardware;
- the upstream model/planner/runtime ecosystem;
- replay/logging compatibility with the openpilot architecture.

It does **not** make an unsupported F13 drive itself merely by being connected.

The missing work is the BMW-specific compatibility layer.

## F13 compatibility layers

### Layer 1 — observation

```text
BMW CAN / FlexRay
       |
       v
BMW transport-aware decoders
       |
       +--> BMWVehicleState
       +--> CarState
       +--> RadarData
```

This is the first useful target.

### Layer 2 — shadow control intent

```text
openpilot proposal
       |
       v
BMWControlIntent
       |
       v
logged / replayed only
```

Already defined in the repository.

### Layer 3 — future control

Only after replay/HIL/closed-course validation:

```text
BMWControlIntent
       |
       v
validated domain actuator adapter
       |
       v
BMW semantic request
       |
       v
CAN or FlexRay encoder
```

No such live encoder exists in the current project.

## Beta 1 objective

Beta 1 should prove that the Comma Four can remain essentially stock while an external BMW integration layer supplies enough validated F13 state for meaningful openpilot replay/shadow operation.

Beta 1 does **not** require:

- KAFAS2;
- LiDAR;
- upgraded surround cameras;
- Chestnut/eGPU;
- Tesla HW4;
- automated parking;
- automated gear selection;
- live steering or brake commands.

Those additions must justify themselves with measured evidence after the minimal system works.

## Decision rule

Whenever a proposed hardware addition appears, ask:

> Does this solve a measured Beta 1 blocker that the Comma Four + BMW OEM sensors cannot already solve?

If not, defer it.
