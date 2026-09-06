# BMW F13 Control Architecture — Research Boundary

## Goal

Prepare the project for future supervised BMW actuation without coupling planners to raw CAN/FlexRay framing and without enabling live control during the current pre-vehicle phase.

The project remains observation/shadow/HIL research only.

## Separation of concerns

```text
openpilot / parking planner
          ↓
   BMWControlIntent
          ↓
 domain actuator adapter
          ↓
 BMW semantic request
          ↓
 transport encoder
     CAN / FlexRay
          ↓
      BMW ECU
```

Only the first two layers are represented in the current software architecture.

There is no live actuator adapter or transport encoder.

## Control domains

### 1. Lateral steering

Primary questions:

- Which actuator can safely provide continuous steering authority on Prototype 001?
- Is the usable request path exposed on CAN, FlexRay, or both?
- Is the request torque-, angle-, curvature-, or state-machine-based?
- What independent feedback proves the requested motion actually occurred?
- How do xDrive packaging, EPS retrofit options, Active Steering and IAS/rear-steer affect the final actuator architecture?

Initial research path:

```text
driver steering action
      ↓
CAN + FlexRay observation
      ↓
request/feedback candidate discovery
      ↓
cross-session evidence
      ↓
ECU/topology corroboration
      ↓
bench/HIL only
```

No steering request is transmitted on the vehicle during discovery.

### 2. Longitudinal speed

Preferred first strategy:

`OEM_ACC_ORCHESTRATION_FIRST`

The first useful autonomous longitudinal path should, where feasible, reuse BMW's own ACC/DSC/DME control rather than immediately commanding throttle or brake actuators directly.

Research must distinguish:

- ACC state
- set speed
- following-gap request
- selected-lead state
- acceleration/deceleration request
- stop/resume behavior
- brake intervention
- DME torque intervention
- driver brake/accelerator override

Only after those relationships are validated should direct longitudinal authority be considered.

### 3. Indicators and hazards

Indicators are a separate body-control authority domain.

Research must distinguish:

```text
driver stalk request
      ↓
network request/state
      ↓
body controller
      ↓
actual lamp feedback
```

A future automated request must never suppress or override a direct driver stalk command.

### 4. Parking steering

Parking trajectory generation is not the normal highway planner.

Inputs should include:

- surround cameras
- Scene3D
- LiDAR/depth
- PDC/ultrasonics
- steering state
- wheel speeds
- gear
- obstacle envelope

Parking steering should reuse the same validated lateral actuator path rather than create an unrelated second steering controller.

### 5. Parking longitudinal

Low-speed longitudinal control must be independently validated because creep, stop accuracy and obstacle proximity impose different requirements from highway ACC.

Preferred first approach is reuse of an OEM low-speed brake/powertrain path if available.

### 6. Gear selection

Gear selection is intentionally isolated and initially disabled.

It should remain observation-only until late-stage bench/HIL work because incorrect R/D/P authority has a different and severe hazard profile.

### 7. Brake hold

Brake-hold/standstill authority remains disabled until DSC/parking-brake state and request behavior are understood.

## Per-domain authority

The project does not use a single `AUTONOMY=ON` state.

Current allowed states are:

- `DISABLED`
- `SHADOW`
- `HIL_ONLY`

Future states require explicit safety review.

A future vehicle might validly operate with different domains at different stages, for example:

```text
lateral       HIL_ONLY
longitudinal  SHADOW
indicators    SHADOW
parking       DISABLED
gear          DISABLED
```

## Required feedback before actuator work

### Steering

Minimum evidence set:

- steering wheel angle
- front steer angle where available
- steering torque / driver intervention
- yaw rate
- EPS state
- ICM state
- IAS/rear steer state if equipped

### Longitudinal

Minimum evidence set:

- vehicle speed
- four wheel speeds
- longitudinal acceleration
- brake pedal
- accelerator position
- DSC state/intervention
- ACC state
- selected lead/radar state where relevant

### Body / indicators

Minimum evidence set:

- stalk state
- requested state candidate
- actual lamp state

### Parking

Minimum evidence set:

- steering
- wheel speeds
- gear
- brake
- PDC/ultrasonic
- Scene3D / surround perception
- obstacle distance

## Research sequence

### Phase C0 — Observation

- identify state signals
- identify likely request/feedback pairs while the BMW itself performs the action
- no transmit

### Phase C1 — Cross-session evidence

- repeat the same maneuver in multiple sessions
- require stable transport/source identity
- reject one-off candidates

### Phase C2 — Request/feedback topology

- correlate likely request with resulting actuator feedback
- determine involved ECUs
- compare CAN and FlexRay paths
- do not infer ECU ownership from correlation alone

### Phase C3 — Bench/HIL

Only after explicit review:

- donor ECU/actuator or representative HIL
- bounded synthetic requests
- watchdog behavior
- timeout behavior
- counter/checksum behavior
- fault recovery
- driver override simulation

### Phase C4 — Closed-course proposal

Not implemented in this repo stage.

Requires a separate safety review before any vehicle transmission path exists.

## Why request and feedback must be separated

A field that moves when the driver steers is not necessarily the steering command.

It may be:

- steering-wheel position
- road-wheel position
- ICM estimate
- EPS feedback
- Active Steering output
- rear-steer feedback
- a forwarded/derived ZGW representation

Therefore:

```text
event correlation
≠
request identification
```

The actuator research pipeline must prove temporal directionality and topology before a request role is assigned.

## Transport policy

CAN and FlexRay remain first-class transports.

A future actuator implementation should encode a validated semantic request into the required transport. It should not use a generic bidirectional CAN↔FlexRay translator that blindly mirrors network traffic.

Preferred model:

```text
BMW semantic request
       ↓
validated domain adapter
       ↓
CAN encoder or FlexRay encoder
```

## Current invariant

There is no live steering, throttle, brake, indicator, parking, gear or brake-hold command path in the project.

The actuator research manifest is validated by CI to reject:

- live transmit enablement
- domain TX enablement
- raw CAN IDs
- FlexRay slot IDs
- payload definitions
- checksum/alive-counter definitions
- unreviewed ACTIVE states
- prematurely confirmed transports

That boundary stays in place until explicit human safety review and HIL readiness.
