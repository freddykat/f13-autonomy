# Controlled Vehicle Test Protocol

## Purpose

This protocol defines the staged progression from bench/HIL validation to controlled Prototype 001 vehicle testing.

It is intentionally conservative. The objective is to validate sensing, state reconstruction, BMW chassis awareness and fault handling before introducing any live vehicle-motion request.

## Preconditions

A build may enter this protocol only if:

- the current HIL gate reports `eligible_for_controlled_vehicle_test`
- exam/replay promotion gates are passing
- no unresolved critical regression exists
- the vehicle mechanical/electrical baseline is healthy
- BMW EPS/ICM/DSC/IAS state can be observed reliably
- an independent emergency-stop path is available for any stage involving motion authority
- test area is private/controlled and free of uninvolved road users

## Stage CV0 — Static read-only validation

Vehicle stationary, ignition on where required.

Validate:

- bus discovery and timestamping
- BMWVehicleState freshness/validity
- EPS/ICM/DSC/IAS state transitions
- steering-angle consistency
- gear/brake/accelerator state observation
- driver input detection
- watchdog and stale-signal handling

No motion commands are permitted.

### Pass criteria

- no unknown signal is silently interpreted as zero/healthy
- all required state has bounded latency
- logger/replay output is deterministic

## Stage CV1 — Passive rolling logging

Human drives at very low speed in the controlled area. Autonomy stack remains read-only.

Validate:

- wheel-speed agreement
- yaw-rate agreement
- front steering state
- rear-steer/IAS behaviour where fitted
- IMU/GNSS/visual ego-motion consistency
- motionvalidatord reconstruction
- BMW mode changes

### Abort criteria

- unexpected bus faults
- required chassis state becomes stale
- unexplained large disagreement between OEM and independent motion estimate
- logging/timestamp synchronization failure

## Stage CV2 — Rear-steer and swept-path characterization

Human-controlled low-speed manoeuvres only.

Test:

- constant-radius turns
- figure-eight
- forward/reverse parking paths
- low-speed left/right transitions
- speed-dependent rear-steer contribution

Goal: validate that predicted vehicle body/swept path accounts for BMW rear-steer behaviour.

No autonomy actuation.

## Stage CV3 — Shadow trajectory comparison

Human continues to drive. Planner produces `PlannedMotion` and hypothetical `BMWMotionRequest`, but nothing is transmitted.

Compare:

- planned curvature vs observed curvature
- planned acceleration vs observed acceleration
- lane-change intent vs actual human trajectory
- BMW dynamics model prediction vs actual response

Use disagreement mining for review.

## Stage CV4 — Fault injection without actuation

Still read-only.

Inject or simulate:

- camera dropout
- radar dropout
- GNSS dropout
- stale rear-steer state
- stale yaw state
- traffic-control uncertainty
- BMW capability uncertainty

Verify degradationd/oddmanagerd response.

## Stage CV5 — Stationary authority-path validation

Vehicle secured so unintended motion cannot occur.

Validate only the control plumbing/safety gate while the vehicle is stationary:

- command authorization state
- watchdog expiry
- driver override priority
- emergency-stop path
- rejection of stale/unknown state
- rejection of commands outside configured envelope

No dynamic vehicle response is requested.

## Stage CV6 — Very-low-speed, low-authority research

Only after all previous stages pass and with explicit human review.

Constraints:

- private controlled area
- walking-speed envelope
- clear runoff/space
- dedicated safety driver
- independent observer where practical
- physical emergency stop
- minimal request duration
- low authority only

Initial goals should be limited to verifying that an accepted high-level request is interpreted by the BMW control domain as expected, not to demonstrate autonomy capability.

## Stage CV7 — Motion validation under low authority

For each low-authority request record:

`PlannedMotion -> BMWMotionRequest -> ObservedMotion`

Require:

- measured response within predeclared envelope
- no fight with DSC/ICM/IAS
- immediate driver override
- immediate stop on watchdog/sensor fault
- no unexplained oscillation or divergence

Any unexplained intervention returns the build to HIL/replay analysis.

## Stage CV8 — Controlled manoeuvre library

Only after repeatable CV6/CV7 success.

Candidate low-speed controlled manoeuvres:

- straight creep
- gentle constant-radius turn
- stop at marker
- short forward/reverse parking move
- supervised remote-parking research in the previously defined Summon envelope

Higher-speed road behaviour is explicitly out of scope for this stage.

## Rollback rule

Any critical anomaly causes immediate rollback to the last fully passed stage.

A new software build does not inherit vehicle-test eligibility automatically; it must pass the applicable promotion and HIL gates again.

## Evidence package

Every controlled session should retain:

- build/commit identity
- vehicle configuration
- test stage
- operator(s)
- weather/surface notes
- synchronized BMW/raw/normalized state logs
- planned/requested/observed motion
- faults/interventions
- emergency-stop events
- result and review notes

## Core rule

> Vehicle testing exists to validate assumptions already demonstrated in simulation/HIL, not to discover safety behaviour by trial and error on the road.
