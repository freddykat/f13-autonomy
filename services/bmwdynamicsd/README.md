# bmwdynamicsd

`bmwdynamicsd` is a read-only/shadow service that estimates the longitudinal capability and response characteristics of Prototype 001 in its current BMW drive mode and powertrain state.

It exists so the planner can answer questions such as:

- Is the current overtaking gap realistically achievable?
- How much delay should be expected before acceleration arrives?
- Is the car already in a suitable gear or is a downshift likely?
- Is the car traction-limited or in a degraded state?
- Does the current drive mode materially change expected response?

It does **not** directly command gears, torque, boost, xDrive or DSC.

## Inputs

Initial shadow inputs should come from logged/decoded BMW state where available:

```text
BMW chassis/powertrain state
  drive mode
  transmission mode
  current gear
  engine RPM
  vehicle speed
  measured longitudinal acceleration
  DSC/traction state
  shift state
  relevant thermal/degraded flags

Independent/context state
  road grade estimate
  GNSS speed
  IMU acceleration
```

## Output

The primary output is `BMWDynamicCapabilityState` as defined in `interfaces/bmw_dynamic_capability_state.md`.

## Architecture

```text
BMW CAN/FlexRay/state logs
          |
          v
     bmwstated
          |
          +-------> chassis state
          |
          v
     bmwdynamicsd
          |
          +-- physical baseline
          +-- mode/gear response model
          +-- learned calibration from logs
          |
          v
BMWDynamicCapabilityState
          |
          v
 planner feasibility checks
```

## Development approach

### D0 — synthetic profiles

Create transparent synthetic response profiles for representative states such as:

- Comfort, high gear, no downshift
- Comfort, downshift required
- Sport, prepared gear
- Sport, shift in progress
- traction-limited
- uphill
- downhill
- stale/unknown mode

These profiles are only for testing the software contract.

### D1 — passive data collection

Collect synchronized logs of:

- mode
- gear
- RPM
- speed
- longitudinal acceleration
- throttle/driver demand where legitimately observable
- DSC/traction state
- grade estimate
- shift events

No autonomy actuation is needed.

### D2 — system identification

Build empirical response surfaces such as:

```text
speed x gear x mode -> response delay
speed x gear x RPM  -> achievable acceleration envelope
mode x shift state  -> jerk / transient behaviour
```

Avoid pretending the exact engine power curve alone determines vehicle acceleration; transmission ratio, drag, grade, traction and shift timing matter.

### D3 — shadow planner integration

For each candidate manoeuvre, compare required motion with the capability state.

Example:

```text
merge requires +2.0 m/s^2 within 0.6 s
BMW estimate in current state:
  maxAccel       1.5 m/s^2
  responseDelay  0.8 s

result: candidate not feasible with required margin
```

### D4 — observed-vs-predicted learning

After a human-driven or later validated manoeuvre, compare predicted response with `motionvalidatord`/observed longitudinal motion and update calibration data offline.

## Drive modes

BMW drive modes are context for prediction, not a planner safety level.

A Sport-like mode may reduce expected delay or alter shift strategy. That can make a manoeuvre feasible sooner, but it must not shrink minimum time gaps, collision margins or uncertainty buffers.

## Comfort objective

Prototype 001 is a civilised daily-driver GT. The planner should therefore distinguish:

- `maxAccel`: what the vehicle appears capable of
- `comfortableMaxAccel`: what is appropriate for normal automated GT driving

The planner should normally prefer the comfortable envelope and reserve higher longitudinal demand for situations where it is justified and validated.

## Failure handling

If mode, gear, speed or other critical state is stale/unknown:

- lower confidence
- fall back to a conservative generic envelope
- do not assume Sport response
- do not assume a downshift will happen quickly

If traction or stability intervention is active, the capability estimate should be degraded and the planner should avoid demanding more simply because a nominal engine model says power is available.

## Relationship to BMW control authority

The boundary remains:

```text
openpilot/planner -> desired motion
BMW OEM domain    -> actual powertrain/chassis coordination
bmwdynamicsd      -> predicts capability
motionvalidatord  -> verifies what actually happened
```

This preserves BMW's own lower-level intelligence while giving the autonomy stack enough knowledge to make realistic high-level decisions.
