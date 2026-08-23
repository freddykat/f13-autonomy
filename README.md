# BMW F13 Autonomy

Experimental openpilot-based autonomy project for a BMW F13 using custom perception hardware, BMW CAN/FlexRay integration, and Tesla HW4/FSD as a behavioural teacher and benchmark.

> **The goal is not to put Tesla FSD into a BMW.** The goal is to use Tesla HW4/FSD as an evolving behavioural teacher and benchmark while developing an independent openpilot-based autonomy stack for the BMW F13.

## Project status

Research, architecture and hardware-planning phase. The first target is deliberately limited to **supervised motorway/highway autonomy**. Development begins with logging, replay, shadow mode and hardware-in-the-loop before experimental actuation.

## Background

We are **not professional autonomous-driving software developers**. Our background is practical engineering, automotive/mechanical/electrical work and hardware integration. Much of the research and architecture has been developed using AI-assisted research and development.

We intend to use AI for code generation and explanation, documentation, log analysis, tests, simulation, CAN/FlexRay analysis assistance and model/data tooling. Safety-critical changes must still pass review, simulation, replay, HIL and controlled validation.

We welcome collaboration from developers familiar with openpilot/comma/panda, Tesla HW4/DAS/FSD CAN, BMW CAN/FlexRay/ICM/DSC/EPS, computer vision, embedded safety, GPU inference and automotive cameras.

## Core idea

```text
openpilot
+ custom synchronized cameras
+ GPU compute
+ BMW OEM sensors
+ 360-degree perception
+ Tesla HW4/FSD behavioural benchmark
+ BMW CAN/FlexRay integration
```

The BMW should ultimately operate **without Tesla HW4**. HW4 is intended as a teacher, behavioural benchmark, disagreement source and validation reference — not the final required controller and never a direct BMW actuator controller.

## High-level architecture

```text
                   ROAD ENVIRONMENT
                          |
          +---------------+----------------+
          |               |                |
   Custom Cameras     BMW Sensors     Tesla Cameras
          |               |                |
          v               v                v
     GPU Compute      Radar/KAFAS       Tesla HW4
          |               |              + FSD
          +-------+-------+                |
                  |                        |
                  v                        v
             WORLD MODEL              FSD BENCHMARK
                  |                        |
                  +-----------+------------+
                              v
                         META-PLANNER
                              |
                              v
                         SAFETY LAYER
                              |
                              v
                     BMW CONTROL BRIDGE
                              |
                      CAN / CAN-FD / FlexRay
                              |
                    EPS / DSC / DME / ICM
```

## Operating modes

### OEM / Manual

The BMW must remain normally driveable if the autonomy computer is unavailable. The retrofit should fail toward normal OEM/manual operation wherever technically possible.

### Partial Autopilot

Default assisted-driving mode without requiring a navigation route. Initial targets include lane centering, adaptive cruise, following-distance management, curve adaptation, cut-in handling, collision awareness, blind-spot perception, driver monitoring and driver-confirmed lane changes.

### Highway Supervised Autonomy

When a valid route is active and the road is inside the supported ODD, the system may offer highway autonomy. Targets include route-based lane selection, overtaking, automatic lane changes, motorway merging, exits and route preparation. It remains supervised.

## Action Questions and uncertainty

The system should ask the driver only when human intent is genuinely useful, such as choosing between valid routes or semantic preferences. It should **not** outsource safety decisions such as whether a lane change is physically safe.

Perception or prediction uncertainty should produce conservative behaviour: wait, increase margin, avoid the manoeuvre, or request takeover when required.

## Tesla HW4/FSD as teacher

We want to compare the same scenario across:

```text
Tesla FSD
vs openpilot
vs our policy
vs human driver
```

The objective is not blind imitation. Tesla is a benchmark, not an absolute authority. Disagreements become high-value validation/training cases.

### teslaoracled

A proposed read-only bridge, `teslaoracled`, would normalize externally observable HW4/FSD behaviour into states such as autopilot state, desired speed, longitudinal/steering request where observable, lane-change state/direction, blind-spot state, FCW, speed-limit/navigation state and timestamps.

The project does **not** aim to extract or redistribute Tesla proprietary FSD software or model weights.

### HW4 bench research questions

We want to determine the minimum viable genuine HW4 bench environment, which Tesla ECUs/states must remain, which signals can legitimately be replayed/emulated, calibration requirements, update behaviour and which DAS/FSD outputs can be externally observed.

Preferred concept:

```text
GENUINE TESLA HW4
       |
GENUINE FSD SOFTWARE
       |
READ-ONLY OBSERVATION
       |
teslaoracled
```

HW4 has no direct authority over BMW steering or braking.

## Custom openpilot hardware

The final system is not intended to require a comma device. We want openpilot on our own cost-effective compute platform, scaling GPU performance later as multi-camera perception, occupancy, BEV, world modelling and larger models demand it.

We want to preserve upstream interfaces wherever practical rather than maintaining a deep fork.

```text
custom cameras
     |
our_camerad
     |
VisionIPC
     |
modeld
```

## Camera/perception concept

Potential synchronized camera coverage includes front tele/main/wide, front-left/right, side-left/right and rear views. Exact count is not final; useful coverage, HDR, synchronization, low latency and image quality matter more than camera count.

Prototype capture may use development interfaces; the final target is automotive high-speed camera transport such as GMSL-class links into the compute system.

The perception stack may eventually include object/lane/free-space detection, depth/motion estimation, tracking, radar-camera fusion, BEV, occupancy, trajectory prediction, road topology and unknown-obstacle handling.

## World model

All sources should be transformed into a consistent BMW ego coordinate system. Inputs may include custom cameras, BMW radar, KAFAS, PDC/Parking High, GPS, IMU, wheel speeds, steering/yaw/dynamics state and the read-only Tesla benchmark.

We intentionally do not follow a vision-only ideology: useful BMW radar tracks should be fused with vision.

## BMW CAN/FlexRay integration

FlexRay is a major research area. We want to understand and preserve BMW F-series OEM control loops involving ICM, DSC and EPS rather than bypassing them with crude external actuators.

```text
openpilot
    |
VehicleCommand
    |
bmwcontrold
    |
Safety MCU
    |
CAN / FlexRay
    |
ICM / DSC / EPS
```

The planner should produce abstract commands such as target speed, acceleration and curvature. BMW-specific translation belongs below that abstraction. The GPU/neural model should never directly drive an EPS motor or brake actuator.

## Independent safety controller

A dedicated MCU layer should sit between Linux/GPU compute and the BMW. Responsibilities may include CAN/CAN-FD/FlexRay interfacing, watchdogs, command limits, plausibility checks, driver override, communication-loss handling and hardware autonomy disable.

Driver brake/steering override remains authoritative. EPS/DSC/communication faults must degrade or disable automation safely.

## Meta-planner

The final planner should not blindly majority-vote between models. Inputs can include openpilot, our policy, Tesla benchmark, navigation and the world-model safety layer. Physics and safety constraints must be able to veto learned behaviour.

## Disagreement mining and human review

One central idea is automatically saving cases where Tesla, openpilot, our policy and/or the human disagree. These are more informative than long stretches of easy driving where every system agrees.

A simple graphical review tool should show video/world state and each proposed action, allowing a human to label which behaviour was preferable, unsafe or uncertain without needing to edit training code.

## Black-box logger

Maintain a rolling synchronized buffer of cameras, radar, CAN, FlexRay, GPS/IMU, world model, openpilot output, Tesla benchmark, planner output, BMW state, driver inputs and confidence. Preserve event windows around takeovers, hard braking, FCW, disagreements, cut-ins, faults and unexpected interventions.

## GPS/navigation behaviour

GPS position alone does not enable route autonomy. Partial Autopilot should remain available without navigation. Highway mode requires a valid route, supported road/ODD, healthy sensors, sufficient confidence and explicit driver activation.

## Modular software strategy

Because this is a small AI-assisted project rather than a large professional autonomy team, modularity is essential. Proposed services include:

```text
our_camerad
teslaoracled
bmwstated
worldmodeld
metaplannerd
bmwcontrold
```

The aim is to keep upstream openpilot changes as small and reviewable as possible.

## Planned repository structure

```text
f13-autonomy/
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── HARDWARE.md
│   ├── BMW_FLEXRAY.md
│   ├── TESLA_HW4.md
│   ├── CAMERA_SYSTEM.md
│   ├── SAFETY.md
│   └── ROADMAP.md
├── services/
│   ├── teslaoracled/
│   ├── bmwstated/
│   ├── worldmodeld/
│   ├── metaplannerd/
│   └── bmwcontrold/
├── interfaces/
├── hardware/
│   ├── camera_board/
│   ├── safety_board/
│   └── flexray/
├── simulation/
│   ├── fake_tesla/
│   ├── fake_bmw/
│   └── scenarios/
├── tools/
│   ├── log_viewer/
│   ├── disagreement_viewer/
│   └── dataset_builder/
└── tests/
```

## Development milestones

**M0 — Shadow Lab:** cameras + BMW CAN/FlexRay logging, openpilot execution, fake Tesla oracle, decision visualization and disagreement storage. No actuation.

**M1 — Tesla Teacher:** genuine HW4/FSD read-only observation while the BMW is manually driven.

**M2 — BMW Shadow:** `bmwcontrold` calculates but does not transmit commands; compare proposed steering/acceleration with human action.

**M3 — HIL:** BMW donor ECUs on a bench with the safety/control stack.

**M4 — Closed Course:** first controlled physical actuation.

**M5 — Partial Autopilot:** lane centering, ACC, cut-in/collision handling and supervised lane changes.

**M6 — Highway Supervised:** route-aware highway lane management, overtaking, merging and exits within a validated ODD.

## AI-assisted development workflow

```text
AI-assisted proposal
        |
code/human review
        |
simulation + unit tests
        |
recorded-data replay
        |
hardware-in-the-loop
        |
controlled validation
```

Not: generated code directly to public-road safety-critical testing.

## Collaboration wanted

We especially want to hear from people experienced with:

- Tesla HW4 bench setups, DAS/FSD CAN, gateway/networking, calibration and observable outputs
- openpilot custom hardware, VisionIPC, modeld, cereal, Panda/safety and external GPU inference
- BMW F-series CAN/FlexRay, ICM, DSC, EPS, ACC radar, KAFAS and steering retrofits
- multi-camera BEV/occupancy, tracking, prediction, imitation/teacher-student learning and uncertainty estimation

### Questions for HW4 developers

1. What is the minimum HW4 bench configuration required to keep useful DAS/FSD functions operating?
2. Which genuine ECUs need to remain present?
3. Which vehicle states can be replayed/emulated for legitimate research?
4. Can an entitled HW4 remain useful outside its donor vehicle?
5. Which FSD outputs are externally observable?
6. Can steering/longitudinal/lane-change intent be decoded reliably?
7. Can recorded state traffic reproduce useful development conditions?
8. What changes across OTA versions?
9. Can a stable abstraction layer be built above observable Tesla messages?
10. Has anyone already built a complete HW4 bench with active perception/planning?

## What this project is not

This project is not intended to redistribute Tesla proprietary software/model weights, bypass safety systems, directly connect neural-network output to actuators, remove driver responsibility during development, or test unvalidated safety-critical code on public roads.

## Long-term objective

```text
Tesla FSD quality benchmark
           |
continuous comparison
           |
disagreement dataset
           |
training + validation
           |
independent openpilot-based BMW stack
```

As the benchmark improves, our validation target moves forward too.

## Final vision

A BMW F13 retaining OEM/manual driving while gaining a modular path toward Partial Autopilot and supervised highway autonomy, with 360-degree perception, radar fusion, openpilot big models, Tesla HW4 as a read-only behavioural benchmark, BMW CAN/FlexRay integration, OEM-style EPS/DSC control and an independent safety MCU.

## Current priorities

- map BMW CAN/FlexRay architecture
- identify the EPS retrofit/integration strategy
- prototype openpilot on custom compute
- design the synchronized camera system
- build CAN/FlexRay logging
- contact Tesla HW4 developers
- investigate minimum viable HW4/FSD bench
- build the Shadow Lab software
- create the disagreement-review dashboard

## Contributions

Technical criticism and collaboration are welcome. In particular, if you have worked with **Tesla HW4 bench testing, FSD/DAS CAN, openpilot hardware ports or BMW FlexRay**, we would like to hear from you.

This project is intentionally ambitious. The approach is to break that ambition into small, testable and independently verifiable engineering problems.
