# HIL Validation Contract

## Purpose

This document defines the minimum bench/HIL evidence required before any build may be considered for controlled vehicle testing on Prototype 001.

Passing this contract does **not** authorize public-road testing or live autonomy actuation. It only means the build is eligible for the next validation stage.

## Preconditions

A candidate build must already have:

- passed the M0 exam suite at the required threshold
- passed replay validation with zero critical regressions
- passed `promotiongated`
- a reproducible build identifier
- deterministic logs for the tested configuration
- documented interfaces and signal provenance

## Required HIL domains

### 1. Timing and latency

Measure end-to-end timing for:

- sensor ingest
- BMW state decode
- world-state update
- planner decision
- safety-gate evaluation
- command-path simulation
- feedback observation

Requirements:

- timestamps must be monotonic and source-tagged
- stale data must be detected explicitly
- latency spikes must be logged
- a delayed critical input must never be silently treated as fresh

### 2. Watchdogs

Inject failures for:

- planner freeze
- world-model freeze
- BMW-state freeze
- sensor-health freeze
- main-compute restart
- safety-layer restart

Expected result:

- the system transitions to the defined degraded state
- command simulation is inhibited when required
- fault state is explicit and logged

### 3. BMW arbitration awareness

The HIL environment must emulate BMW lower-level control ownership.

The autonomy stack must demonstrate that it does not attempt to independently coordinate front steering, rear steering, DSC or individual chassis actuators.

Required cases:

- normal BMW acceptance of a high-level request
- BMW refusal/rejection
- BMW degraded state
- BMW stability intervention
- request saturation/limit condition

### 4. Rear-steer awareness

The motion estimator must be tested with:

- rear steer active
- rear steer unavailable
- rear steer stale
- rear steer disagreement versus measured yaw
- low-speed opposite-phase steering behaviour
- higher-speed same-phase steering behaviour

Unknown rear-steer state must never be coerced to zero.

### 5. DSC/ICM intervention

Inject synthetic stability interventions.

Expected behaviour:

- intervention is recognized
- planner demand is not increased in opposition to DSC/ICM
- event is logged as OEM stability intervention
- the build follows the configured degrade/cancel policy

### 6. Sensor-loss matrix

At minimum test loss/staleness of:

- front camera
- side/rear camera set
- radar
- BMW CAN/FlexRay state
- IMU
- GNSS
- traffic-control perception
- driver monitoring

The resulting autonomy capability must match `degradationd` / `oddmanagerd` policy.

### 7. Traffic-control failure injection

Test:

- red light -> green mismatch
- red X -> open-lane mismatch
- variable-speed-sign disagreement
- stale matrix sign
- low-confidence traffic light
- lane association error

Unknown or conflicting control state must not be promoted to permissive state.

### 8. Longitudinal capability errors

Inject incorrect powertrain capability estimates:

- underestimated response delay
- overestimated available acceleration
- traction-limited state
- shift-in-progress
- thermal/degraded state

Expected behaviour:

- planner rejects or downgrades manoeuvres when confidence/capability becomes insufficient
- no safety margin is reduced because Sport mode is selected

### 9. Emergency stop path

The HIL bench must include an independent emergency-stop concept for later controlled vehicle tests.

The test shall verify:

- emergency-stop input is detected independently of high-level planner state
- simulated motion authority is removed immediately according to the safety design
- recovery requires an explicit reset sequence
- the event is permanently logged

### 10. Driver override priority

Simulate:

- steering override
- brake override
- accelerator override where applicable to mode semantics
- gear change
- door opening

Human/vehicle-owner input must dominate the autonomy request according to the defined authority hierarchy.

## Required evidence per test

Every HIL case should produce:

- test ID
- build ID / commit
- configuration ID
- start/end timestamps
- injected fault or scenario
- expected outcome
- observed outcome
- pass/fail
- relevant logs
- reason codes

## HIL release gate

A build is not eligible for controlled vehicle testing if any of the following is true:

- critical HIL test failed
- stale data was treated as valid
- BMW lower-level arbitration was bypassed in simulation
- rear-steer UNKNOWN was interpreted as zero
- DSC/ICM intervention was counter-commanded
- emergency-stop path failed
- driver override did not dominate
- a critical fault produced no deterministic logged state

## Design rule

> A build must prove how it fails on the bench before it is allowed to demonstrate how it works in the car.
