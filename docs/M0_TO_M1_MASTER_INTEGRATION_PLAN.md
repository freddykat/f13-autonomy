# M0 -> M1 Master Integration Plan

## Purpose

This document consolidates the first development sprint into one implementation path for Prototype 001.

The immediate goal is **not vehicle actuation**. The M1 target is a BMW F13 that can run the complete autonomy stack in **read-only / shadow-learning mode** using real synchronized vehicle and perception data, while producing explainable decisions, legality context, disagreement events, replayable learning episodes and regression scorecards.

## Current architecture

```text
BMW CAN / FlexRay / LIN
        |
        v
     bmwstated -------------------------+
        |                               |
        v                               |
 BMWVehicleState                        |
        |                               |
        +--> motionvalidatord           |
        +--> bmwdynamicsd               |
        +--> worldmodeld <--- cameras/radar/parking/KAFAS
                          |
                          +--> trafficcontrold
                          |        |
                          |        v
                          |    trafficlawd
                          |
                          v
                    shadowplannerd
                          |
                          +--> longitudinalshadowd
                          +--> actionquestiond
                          +--> driverpreferenced
                          |
                          v
                     disagreementd
                          |
                          v
                    learningepisoded
                          |
                          v
                    replayvalidatord
                          |
                          v
                    promotiongated
```

`degradationd` and `oddmanagerd` supervise which capabilities are currently trustworthy/eligible.

## M0 definition

M0 is the offline/synthetic phase.

M0 is considered complete when the repository contains deterministic tests for:

- BMW chassis/vehicle state handling
- motion validation
- longitudinal capability estimation
- dynamic traffic-control handling
- traffic-rule context
- explainable shadow decisions
- disagreement mining
- driver preference filtering
- action-question policy
- degradation handling
- ODD classification
- learning episode recording
- replay validation
- scenario exam scorecards
- promotion gates
- HIL and controlled-test contracts

M0 does not authorize vehicle control.

## M1 definition

M1 is the **real-car shadow-learning phase**.

M1 success means Prototype 001 can drive normally under human/OEM control while our stack passively records and interprets the real vehicle and road environment.

The M1 stack must be able to answer, after every relevant event:

1. What did the BMW know?
2. What did our cameras/radar/world model know?
3. Which traffic rules and dynamic controls were applicable?
4. What did openpilot propose?
5. What did our shadow planner propose?
6. What did the driver actually do?
7. What did the HW4/FSD benchmark propose, where a lawful benchmark observation is available?
8. What physically happened afterwards?
9. Was the outcome legal, safe and consistent with the BMW's measured motion?
10. Would the current software make the same decision in replay?

## Hardware minimum for M1

The first real-car learning rig should prioritize logging quality over actuator hardware.

Minimum domains:

### Vehicle-network acquisition

- passive CAN acquisition
- passive FlexRay acquisition where required for ICM/IAS/DSC state
- accurate monotonic timestamps
- electrical isolation appropriate for automotive buses
- no transmit path enabled during M1 logging

### Independent ego-motion

- synchronized IMU
- GNSS receiver
- system clock synchronization

### Perception

- forward camera set sufficient for initial highway perception
- additional cameras progressively added toward surround coverage
- BMW radar/KAFAS data where decodable and useful
- PDC/Parking High state for low-speed/near-field work

### Compute

- host capable of running the shadow stack and recording raw streams
- GPU acceleration may be added for perception/model inference
- storage sized for synchronized multi-camera and vehicle-bus logging

### Driver monitoring

- driver-facing camera or a validated equivalent driver-attention source before supervised autonomy work progresses beyond shadow

## Data clock requirement

All important sources must share a common timebase or be transformable into one.

Every normalized signal should include at least:

```text
value
timestamp
source
validity
stale
confidence
unit
```

Camera frame time, radar time, BMW bus time, IMU time and GNSS time must be correlatable.

A dataset with poor synchronization is not considered useful merely because it is large.

## Integration order

### M1.0 — Real BMW logging only

Connect passive bus interfaces and verify:

- wheel speeds
- steering state
- yaw rate
- lateral/longitudinal acceleration
- gear/RPM/drive mode
- DSC/ICM/EPS state
- IAS/rear-steer state where equipped and decodable

Compare BMW yaw against independent IMU.

No autonomy inference is required yet.

### M1.1 — Real motion reconstruction

Run `motionvalidatord` on real drives.

Validate:

- straight-line motion
- steady curves
- lane changes
- acceleration/deceleration
- low-speed turning
- rear-steer influence
- DSC intervention episodes

The objective is to understand the BMW's actual motion, not to control it.

### M1.2 — Real BMW dynamics learning

Run `bmwdynamicsd` read-only and build empirical response envelopes by:

- drive mode
- gear
- RPM
- speed
- grade
- traction state
- thermal/degraded state

Measure response delay and realized acceleration rather than assuming catalogue power curves.

### M1.3 — Forward world model

Add synchronized front perception and build real `WorldState` objects:

- lead vehicle
- adjacent vehicles
- lane geometry
- relative speed
- cut-in candidates
- stopped objects

Raw detections remain separate from normalized world state.

### M1.4 — Dynamic traffic controls

Run `trafficcontrold` on real video in shadow mode.

Target recognition/tracking includes:

- traffic lights
- directional traffic lights
- variable speed limits
- motorway matrix signs
- red X lane closure
- green lane arrows
- merge arrows
- temporary roadwork warnings

All detections require lane/movement association, timestamp and confidence.

### M1.5 — Traffic-rule context

Populate `trafficlawd` with reviewed, versioned rule packs.

Initial priority jurisdictions:

- Netherlands
- Germany
- Belgium
- Portugal

Rule packs must cite authoritative sources outside the runtime repository documentation process and include effective dates.

The runtime planner should consume structured rules, not free-form legal prose.

### M1.6 — Shadow decisions

Run `shadowplannerd` during normal human driving.

The planner remains advisory and stores:

- preferred action
- rejected alternatives
- legality gate result
- physical-safety gate result
- BMW-capability gate result
- route reason
- preference reason
- confidence

### M1.7 — Human/openpilot/benchmark comparison

Feed available independent proposals to `disagreementd`.

No source is treated as truth merely because it is prestigious or because multiple sources agree.

Priority remains:

```text
LEGALITY
  > PHYSICAL SAFETY
  > VEHICLE CAPABILITY
  > ROUTE INTENT
  > BEHAVIOURAL PREFERENCE
```

### M1.8 — Learning episodes

Record high-value events using `learningepisoded`.

Prioritize:

- cut-ins
- overtakes
- merge decisions
- exits
- lane closures
- VSL changes
- matrix-sign transitions
- traffic-light events when urban work begins
- driver corrections
- planner disagreements
- sensor dropouts
- BMW stability interventions

### M1.9 — Replay and regression

Every candidate planner/model change must run against:

- synthetic scenario exam suite
- accumulated real replay episodes

Any safety/legal regression blocks promotion.

## Learning-mode rules

M1 is fundamentally observational.

The vehicle remains under human/OEM control.

The system may learn:

- preferred overtaking timing
- preferred return-to-right timing
- comfortable following gap
- longitudinal style
- preferred route choices between already-valid options

The system must not learn as preference:

- illegal lane use
- unsafe following
- red-light violations
- ignoring lane closures
- unsafe gaps
- instability-inducing behaviour

An observed human action is evidence, not ground truth.

## Action Questions

Questions to the driver are intended only for **safe preference ambiguity**.

Valid example:

```text
Both KEEP and LEFT are legal and safe.
Route permits either.
Decision margin is small.

Ask: "Prefer to overtake?"
```

Invalid example:

```text
System is unsure whether LEFT is physically safe.

Do not ask driver to arbitrate sensor uncertainty.
Conservative result: WAIT / remain manual.
```

## BMW control-domain principle

The project retains the authority split already defined:

> The autonomy system decides where the vehicle should go. BMW decides how its chassis actuators cooperate to get there. The autonomy system verifies where the vehicle actually went.

For M1, the first and last clauses are evaluated only in shadow/reconstruction form. No request is transmitted.

The stack must nevertheless understand that the BMW may internally coordinate:

- front steering
- rear-axle steering / IAS
- DSC
- ICM
- EPS
- brake/drive torque

This is required for correct trajectory prediction and motion validation.

## M1 acceptance criteria

M1 should not be declared complete until the project has demonstrated all of the following on real recorded drives:

- reliable synchronized logging
- decoded core BMW ego-motion signals
- rear-steer awareness where fitted
- BMW yaw vs independent IMU agreement characterized
- real motion reconstruction
- real longitudinal response characterization
- forward world-model generation
- dynamic matrix/VSL recognition on representative footage
- explicit UNKNOWN/stale handling
- traffic-rule context for at least the primary test jurisdiction
- shadow planner explanations
- disagreement mining
- learning episode creation
- deterministic replay
- regression scorecard generation
- no vehicle-actuation path required for any M1 function

## Promotion beyond M1

Completion of M1 does not imply road autonomy readiness.

The next stages remain:

```text
M1 real-car shadow learning
    |
    v
M2 expanded perception + replay coverage
    |
    v
M3 HIL with vehicle-control interface emulation
    |
    v
M4 controlled private-area validation
    |
    v
M5 progressively validated supervised functions
```

Each stage requires a fresh promotion decision.

## First physical build priority

The first installation on Prototype 001 should therefore be designed as a **measurement car**, not an autonomous car.

Priority order:

1. power and protected compute installation
2. passive BMW network logging
3. synchronized IMU/GNSS
4. forward cameras
5. storage/logging
6. BMW state decoding
7. motion reconstruction
8. radar/KAFAS integration
9. surround perception
10. shadow learning stack

Actuator hardware is deliberately not on the critical path for the first useful version.

## What we should be able to show publicly at M1

A compelling early demonstration is not "the car drives itself".

It is a synchronized replay showing:

```text
real road video
+ BMW live chassis state
+ rear steering / yaw behaviour
+ detected traffic/matrix signs
+ world model
+ legal context
+ openpilot proposal
+ project shadow proposal
+ human action
+ disagreement explanation
+ observed outcome
```

That demonstrates the core intelligence and BMW integration while keeping early development safe and scientifically useful.

## Sprint conclusion

The first sprint established a complete development loop:

```text
OBSERVE
  -> NORMALIZE
  -> UNDERSTAND
  -> APPLY RULES
  -> PROPOSE
  -> COMPARE
  -> RECORD
  -> REPLAY
  -> REGRESSION TEST
  -> PROMOTION GATE
```

The next engineering objective is no longer to invent more architecture. It is to make this loop run against **real synchronized Prototype 001 data**.
