# BMW Drive-Mode Dynamics for Openpilot Prediction

## Objective

Prototype 001 should make the openpilot-based planner aware that the BMW's longitudinal response is not fixed.

The same throttle/torque request can produce different real-world acceleration, shift behaviour, engine response, coasting and stability behaviour depending on the active BMW driving mode and current powertrain state.

The autonomy stack should therefore maintain a **mode-aware dynamic capability model**.

This model is for **prediction and request shaping**, not for replacing BMW DME/EGS/xDrive control.

## Core principle

```text
openpilot / meta-planner
        |
 desired speed / accel / jerk
        |
        v
BMW Dynamic Capability Model
        |
 feasible accel envelope
 expected response delay
 expected power/torque availability
 expected shift behaviour
 expected coast/decel behaviour
        |
        v
BMW adapter
        |
 high-level request
        |
        v
BMW DME / EGS / xDrive / DSC
        |
        v
actual longitudinal motion
        |
        v
motionvalidatord
```

The BMW remains responsible for torque production, gearbox shifts, xDrive torque distribution and stability intervention.

## Why this matters

A planner that assumes a fixed acceleration response can make poor decisions in situations such as:

- motorway overtaking
- short merge gaps
- uphill acceleration
- kickdown delay
- low-RPM turbo response
- high-gear cruising
- wet/low-grip conditions
- Comfort vs Sport/Sport+ response

For example, the planner should know that a 100->130 km/h manoeuvre in a relaxed high gear may have a different initial response from the same manoeuvre with the gearbox already in a lower gear and the drivetrain in a sport-oriented mode.

## Inputs

Potential inputs to a future `bmwdynamicsd` service include:

- BMW drive mode / Driving Experience Control state
- gearbox mode and current gear
- engine RPM
- vehicle speed
- accelerator/throttle state where available
- requested/actual engine torque where available
- boost/load proxies where safely observable
- transmission shift state
- xDrive/DSC state
- longitudinal acceleration
- road grade estimate
- vehicle mass estimate / learned effective mass
- engine/coolant/oil/gearbox thermal state where useful
- traction/stability intervention
- current faults/degraded states

Exact signals must be discovered and validated from the BMW buses; no field should be assumed available until confirmed.

## Drive modes

The exact F13 configuration and coding must be mapped, but the estimator should be able to represent modes such as:

- ECO PRO, where present
- COMFORT / COMFORT+
- SPORT
- SPORT+
- manual/DS gearbox state
- custom chassis/powertrain combinations where the BMW exposes them

The model should use the **actual active subsystem states** where possible rather than relying only on the name shown to the driver.

For example, a driver may configure a sport chassis response while retaining a different powertrain response. The predictor should model the real powertrain state, not just a UI label.

## Capability representation

The planner does not need a dyno graph as its primary interface.

A more useful real-time representation is a dynamic envelope:

```text
BMWLongitudinalCapability {
  minAccelMps2
  maxAccelMps2
  comfortableMaxAccelMps2
  maxJerkMps3
  responseDelayMs
  downshiftLikely
  shiftInProgress
  tractionLimited
  thermalLimited
  confidence
  timestamp
}
```

Optionally, the estimator can expose predicted acceleration as a function of speed and horizon:

```text
PredictedAccel(speed, horizon, mode, gear, rpm)
```

## Power-curve knowledge

A calibrated engine torque/power model can improve the estimator.

Conceptually:

```text
engine speed
   +
mode/powertrain state
   +
gear ratio
   +
vehicle speed
   +
drivetrain losses
        |
        v
available wheel force
        |
        v
predicted acceleration
```

However, a static published power curve is insufficient because real response also depends on:

- gear
- boost/load state
- torque limits
- thermal limits
- traction
- shift delay
- road grade
- vehicle mass

The preferred long-term approach is a hybrid model:

1. baseline physical torque/power model;
2. mode/gear response parameters;
3. online calibration from observed BMW acceleration.

## Learned response model

During read-only development, manually driven logs can be used to fit the real response of Prototype 001.

Examples of calibration events:

- steady acceleration in each drive mode
- 60->100 km/h
- 80->120 km/h
- 100->130 km/h
- moderate throttle without kickdown
- kickdown events
- uphill/downhill segments

The system records inputs and actual longitudinal acceleration, then estimates response delay and feasible acceleration.

This is **system identification**, not autonomous actuation.

## Planner use

The planner can use capability prediction to answer questions such as:

### Overtake feasibility

```text
required acceleration/time to clear slower vehicle
vs
BMW predicted acceleration envelope
```

If the available margin is poor, the planner waits rather than starting a manoeuvre that assumes unrealistic acceleration.

### Merge feasibility

Estimate whether the car can reach a safe target speed before the merge point with current powertrain response.

### Comfort

In COMFORT, the planner may prefer lower jerk and earlier acceleration requests rather than forcing the BMW to react late and aggressively.

### Sport modes

A sharper mode can reduce predicted response delay, but it does **not** justify smaller safety gaps. Faster response improves feasibility estimates; it does not weaken safety constraints.

## Mode changes

A mode change should invalidate or transition the current response model smoothly.

Example:

```text
COMFORT -> SPORT

old capability estimate
      |
transition state
      |
new calibrated SPORT estimate
```

The planner should not assume an instantaneous fully calibrated response if the underlying subsystem state is uncertain.

## BMW authority boundary

The autonomy system should not request a particular gear, boost level, turbo state or xDrive torque split unless a future OEM-compatible interface is explicitly understood and justified.

The preferred responsibility split remains:

```text
openpilot: desired motion
BMW:       powertrain execution
validator: confirm actual motion
```

## Relationship to motionvalidatord

`motionvalidatord` closes the learning loop.

```text
predicted accel
vs
observed accel
```

Persistent error can update the model confidence and later recalibrate parameters offline or through a bounded adaptive estimator.

Example:

```text
predicted: +1.8 m/s²
observed:  +1.2 m/s²

possible reasons:
- uphill grade
- high gear
- thermal/torque limit
- traction intervention
- model calibration error
```

The system should diagnose uncertainty rather than immediately interpreting the difference as a vehicle fault.

## Safety rules

- Unknown drive mode/powertrain state -> conservative capability estimate.
- Stale gearbox/engine state must not silently reuse an old aggressive estimate.
- DSC/traction intervention -> reduce available acceleration estimate.
- Fault/degraded powertrain -> invalidate aggressive predictions.
- The planner must retain safety margin beyond the nominal predicted maximum acceleration.
- Capability knowledge must never be used to justify unsafe gaps.

## Development stages

### DM0 — Passive signal discovery

Identify active mode, gear, RPM, speed, acceleration and relevant powertrain states.

### DM1 — Offline powertrain model

Build baseline physical/empirical acceleration curves from recorded driving.

### DM2 — Mode-specific calibration

Compare Comfort/Sport/etc. response delay, shift behaviour and acceleration envelope.

### DM3 — Shadow planner integration

Let openpilot use the capability estimate only for prediction while logging what decisions would change.

### DM4 — HIL/replay validation

Inject recorded mode/gear transitions and verify deterministic planner behaviour.

### DM5 — Closed-course validation

Only after the BMW control interface is validated, compare predicted vs actual longitudinal response under controlled requests.

## Proposed service

A future service may be named:

`bmwdynamicsd`

with an output such as `BMWDynamicCapabilityState` for consumption by the planner and motion validator.

## Design rule

> **Openpilot should know the BMW's current dynamic capability, but BMW remains responsible for producing that capability.**
