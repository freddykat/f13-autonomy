# BMW Chassis Control Authority

## Principle

The autonomy stack does **not** directly coordinate the F13's individual chassis actuators.

Prototype 001 must treat the BMW chassis-control system as an intelligent lower-level controller. The autonomy side defines the desired vehicle motion at a higher level; BMW's OEM systems remain responsible for translating an accepted request into coordinated physical vehicle behaviour.

This is especially important on vehicles equipped with systems such as Integral Active Steering / rear-axle steering and DSC/ICM coordination.

## Authority hierarchy

```text
WORLD MODEL / NAVIGATION
          |
          v
OPENPILOT + META-PLANNER
          |
 desired path / curvature / longitudinal objective
          |
          v
BMW ADAPTER
          |
 OEM-compatible high-level request
          |
          v
BMW CHASSIS DOMAIN
 ICM / DSC / EPS / IAS-HSR / drivetrain
          |
          +-- front steering coordination
          +-- rear steering coordination
          +-- yaw/stability control
          +-- torque/brake coordination
          |
          v
ACTUAL VEHICLE MOTION
          |
          v
MOTION VALIDATION / FEEDBACK
          |
          +------> autonomy state estimator
```

## What the autonomy stack owns

The high-level system may determine concepts such as:

- desired path
- desired curvature / curvature evolution
- desired speed
- desired acceleration/deceleration
- lane-change intent
- route/lane objective
- safe motion envelope

The exact interface exposed by the BMW must be discovered and validated; the project must not assume that every desired abstraction maps directly to an OEM command.

## What BMW owns

Where the OEM architecture provides the capability, BMW remains responsible for lower-level chassis coordination, including:

- front steering actuator control
- rear-axle steering contribution
- speed-dependent front/rear steering relationship
- stability/yaw corrections
- DSC intervention
- brake/drive torque coordination
- actuator limits and local diagnostics

The autonomy computer should not calculate a rear-wheel steering angle and attempt to command it independently merely because that signal can be observed.

## Read everything useful; command as little as necessary

The preferred architecture is asymmetric:

```text
OBSERVATION: rich
COMMAND:     minimal / high-level
```

We want to observe as much OEM chassis state as reasonably available while sending the smallest validated request needed to express the intended motion.

Potential observations include:

- steering-wheel angle
- front steering/rack state
- rear-steer angle/state/availability
- yaw rate
- lateral acceleration
- longitudinal acceleration
- individual wheel speeds
- ICM state
- DSC state/intervention
- EPS state
- IAS/HSR state
- requested/actual states where available
- fault/degraded states

Observation of an actuator state does not imply authority to command that actuator.

## Closed-loop responsibility

The autonomy system must verify the physical result of its request.

It therefore distinguishes:

1. `PlannedMotion` — where the autonomy system intends the vehicle to go.
2. `BMWMotionRequest` — the validated request handed to the OEM control domain.
3. `ObservedMotion` — what the vehicle actually did.

The validator compares planned/requested motion with measured yaw, curvature, pose and acceleration.

If BMW uses rear steering, DSC or another chassis function to achieve the requested motion, that is normal OEM behaviour rather than an error to be cancelled by the autonomy stack.

## Rear-axle steering

Rear steering must be represented in `bmwstated` and the world/vehicle-motion estimator because it changes the relationship between front steering angle and vehicle trajectory.

However, its role is primarily:

- state estimation
- prediction
- swept-path calculation
- diagnostics
- validation of actual motion

not independent autonomy actuation.

For example, at parking speed the path estimator must account for rear-steer geometry when predicting body/corner clearance. At motorway speed it must account for the resulting yaw/curvature response when validating a lane-change trajectory.

## Stability intervention

DSC/ICM intervention has higher authority than the autonomy planner at the actuator-coordination level.

The autonomy stack should recognize intervention and respond by reducing demand, increasing margins, cancelling the manoeuvre where appropriate, or handing control back — not by trying to counteract the stability controller.

## Sensor disagreement

The system should compare OEM state with independent observations such as IMU, GNSS and visual ego-motion where available.

Examples:

```text
BMW yaw rate vs independent IMU yaw
wheel-speed motion vs GNSS speed
BMW steering state vs visual curvature
predicted trajectory vs observed trajectory
```

Disagreement should create a diagnostic/confidence event rather than silently selecting whichever source is convenient.

## Failure philosophy

If the BMW chassis domain reports a fault, degraded state or unavailable capability required by the current autonomy mode, the high-level system must degrade or disengage appropriately.

Unknown/stale IAS, ICM, DSC or EPS state must not be silently treated as a normal zero value.

## Development sequence

### CA0 — Passive mapping

Identify and timestamp relevant BMW chassis states. No command transmission.

### CA1 — Motion reconstruction

Reconstruct actual path from BMW states plus independent IMU/GNSS/vision and verify rear-steer effects.

### CA2 — Shadow request model

Calculate what high-level BMW request would have been desired but do not transmit it.

### CA3 — HIL

Validate request semantics, limits, faults and OEM arbitration on a bench.

### CA4 — Controlled vehicle validation

Only after the interface and safety gate are understood, validate low-authority requests in a controlled environment.

## Design rule

> **The autonomy system decides where the vehicle should go. BMW decides how its chassis actuators cooperate to get there. The autonomy system then verifies where the vehicle actually went.**
