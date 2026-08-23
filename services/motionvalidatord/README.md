# motionvalidatord

`motionvalidatord` is a **read-only / shadow-mode** service that compares intended vehicle motion with the physical motion actually observed from the BMW chassis and independent sensors.

It does not transmit steering, braking, throttle, gear, FlexRay or CAN actuation commands.

## Purpose

The BMW chassis domain remains responsible for low-level actuation and coordination (ICM/DSC/EPS/IAS/HSR as applicable). `motionvalidatord` exists to answer one question:

> Did the car actually move in the way the planner expected?

## Inputs

### PlannedMotion
High-level intended path from the autonomy stack, for example:
- target curvature
- curvature rate
- target speed
- target acceleration
- short-horizon path / pose samples
- lane-change state

### BMWChassisState
Read-only OEM state from `bmwstated`, including where available:
- vehicle speed
- individual wheel speeds
- front steering state
- rear steering / IAS state
- yaw rate
- lateral acceleration
- longitudinal acceleration
- EPS state
- ICM state
- DSC intervention/state
- IAS/HSR availability/state
- source timestamps and validity

### IndependentMotionState
Independent observations where available:
- IMU yaw rate
- IMU accelerations
- GNSS speed/heading/pose
- visual ego-motion / visual odometry
- camera-based lane/path estimate

## Outputs

### ObservedMotion
A fused estimate of actual vehicle motion:

```text
ObservedMotion {
  timestamp
  speed_mps
  yaw_rate_rad_s
  lateral_accel_mps2
  longitudinal_accel_mps2
  curvature_1pm
  heading_rad
  pose_x_m
  pose_y_m
  confidence
  source_health
}
```

### MotionValidationState
Comparison between planned and observed motion:

```text
MotionValidationState {
  timestamp

  planned_curvature
  observed_curvature
  curvature_error

  planned_yaw_rate
  observed_yaw_rate
  yaw_rate_error

  planned_speed
  observed_speed
  speed_error

  planned_lateral_accel
  observed_lateral_accel

  path_cross_track_error
  heading_error

  bmw_chassis_intervention
  dsc_intervention
  rear_steer_active

  status: OK | DEGRADED | UNKNOWN
  reasons[]
}
```

## Important rule: UNKNOWN is not zero

If rear-steer angle, ICM state, yaw-rate source or another required input is stale/missing, it must be marked `UNKNOWN` or unhealthy.

Examples:

```text
rear_steer_angle = UNKNOWN
```

must never silently become:

```text
rear_steer_angle = 0.0
```

because that changes the assumed vehicle geometry.

## Rear-axle steering

The service must understand that front steering angle alone may not define the vehicle trajectory.

Rear steering is therefore used as a state-estimation and validation input, not as an independently commanded target.

At low speed it also matters for body swept-path prediction. At motorway speed it changes the relationship between front steering and measured yaw/curvature.

## BMW intervention handling

If DSC/ICM modifies vehicle behaviour, `motionvalidatord` should report that as a chassis intervention rather than automatically labelling it a controller fault.

Example:

```text
planned curvature: 0.0020 1/m
observed curvature: 0.0016 1/m
DSC intervention: active
status: DEGRADED
reason: OEM_STABILITY_INTERVENTION
```

The planner/supervisor may then reduce demand or cancel the manoeuvre, but the validator itself remains observational.

## Source cross-checks

Where independent sensors exist, the service should compare sources:

- BMW yaw vs independent IMU yaw
- BMW vehicle speed vs wheel-derived speed vs GNSS speed
- steering-derived curvature vs observed yaw/speed curvature
- GNSS/visual trajectory vs integrated chassis trajectory

Persistent disagreement becomes a diagnostic event and may lower confidence.

## Initial calculations

For the first shadow prototype, use simple transparent calculations rather than an opaque learned estimator.

Examples:

```text
observed_curvature ~= yaw_rate / max(speed, epsilon)
```

and windowed path/heading error from timestamp-aligned samples.

More advanced filtering can follow after real F13 logs exist.

## Shadow scenarios

The simulator should validate at least:

1. straight-line stable motion
2. constant-radius curve
3. motorway lane change
4. low-speed turn with rear steering active
5. rear-steer state stale
6. yaw sensor disagreement
7. one wheel-speed anomaly
8. DSC intervention
9. temporary GNSS loss
10. delayed/stale BMW bus state

## Safety scope

`motionvalidatord` must have no code path capable of transmitting vehicle commands.

Its outputs may later be consumed by a supervisory safety state machine, but this service itself is observational.

## Development stages

### MV0
Schema and deterministic fake inputs.

### MV1
Offline replay from synthetic logs.

### MV2
Passive F13 CAN/FlexRay + IMU/GNSS logging.

### MV3
Fit and validate the real F13 motion response, including IAS/rear-steer effects.

### MV4
Use as a live shadow monitor during manual driving.

Only later, after separate HIL/control validation, can the motion-validation output participate in supervisory decisions around experimental actuation.
