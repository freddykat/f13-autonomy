# Vehicle Motion Validation — BMW-aware trajectory confirmation

## Core principle

The autonomy stack must **not assume that steering-wheel angle or front-road-wheel angle uniquely determines the BMW's trajectory**.

Prototype 001 may use BMW chassis systems that already calculate and coordinate vehicle motion internally, including ICM/DSC/EPS and, where equipped, Integral Active Steering / rear-axle steering.

Our system must therefore know that BMW is an active lower-level dynamics controller and validate the **actual resulting vehicle motion**, not merely the command sent to the front axle.

## Control hierarchy

Preferred architecture:

```text
OPENPILOT / META-PLANNER
        |
        | desired path / curvature / accel
        v
BMW CONTROL ADAPTER
        |
        | high-level OEM-compatible request
        v
BMW ICM / DSC / EPS / IAS
        |
        | BMW calculates actuator coordination
        | front steering
        | rear steering where equipped
        | stability corrections
        | brake/torque coordination
        v
ACTUAL VEHICLE MOTION
        |
        v
MOTION VALIDATOR
```

The autonomy stack requests a trajectory objective. BMW remains responsible for the detailed actuator coordination that its chassis systems already know how to perform.

## Why this matters

With rear-axle steering, the same front steering angle can correspond to different vehicle yaw/curvature depending on rear-steer angle, speed, BMW chassis mode and internal controller state.

At low speed, rear wheels may contribute in a way that reduces turning radius. At higher speed, their contribution can change vehicle response and stability. Therefore a simple bicycle model based only on front steering is insufficient as the sole truth source.

## What our system should know

The world/ego-state model should include, where observable:

- front steering angle / rack position
- steering-wheel angle
- driver steering torque
- rear-axle steering angle or IAS actuator state
- requested rear-steer state if exposed
- individual wheel speeds
- vehicle speed
- yaw rate
- lateral acceleration
- longitudinal acceleration
- sideslip estimate if exposed/derived
- ICM/DSC dynamics state
- DSC intervention state
- EPS/IAS fault and availability state
- drive/chassis mode where it changes dynamics
- GNSS heading/velocity
- IMU angular rate and acceleration
- visual odometry / lane-relative motion where available

Not every signal must be available initially. The architecture should explicitly allow UNKNOWN/unavailable signals rather than pretending they are zero.

## Command versus observed motion

The stack must distinguish three things:

```text
PLANNED TRAJECTORY
what openpilot/world planner wants

BMW REQUEST
what bmwcontrold asks the OEM chassis to achieve

OBSERVED TRAJECTORY
what the car physically does
```

Those three should be logged independently.

## Motion confirmation loop

A proposed `motionvalidatord` service should compare expected and observed motion continuously.

Inputs:

```text
planned curvature/path
BMW request
front steering state
rear steering/IAS state if available
yaw rate
wheel speeds
IMU
GNSS
visual ego motion
DSC/ICM state
```

Outputs might include:

```text
MotionValidationState {
  requested_curvature
  estimated_actual_curvature
  requested_yaw_rate
  measured_yaw_rate
  front_steer_angle
  rear_steer_angle
  rear_steer_available
  lateral_accel
  trajectory_error
  heading_error
  lateral_error
  dynamics_controller_active
  dsc_intervention
  motion_consistency
  confidence
  fault_reason
}
```

## Expected motion model

The project can maintain an approximate vehicle model for prediction, but that model is not the final authority.

It should be calibrated from real BMW response and can include speed-dependent behaviour and rear-steer contribution.

The final truth source is sensor-fused physical motion.

Conceptually:

```text
MODEL PREDICTION
front steer + rear steer + speed + dynamics state
                 |
                 v
            expected yaw
                 |
                 +------ compare ------+
                                       |
IMU / ICM / wheel speeds / GNSS -------+
                                       |
                                       v
                              motion consistency
```

## BMW owns the lower-level chassis coordination

Where BMW already coordinates front steering, rear steering, stability control and torque/braking, our preferred approach is to preserve that hierarchy.

We should avoid separately commanding front and rear steering from the autonomy GPU unless a future research result proves that the OEM abstraction cannot be used safely.

The cleaner objective is:

```text
planner says: follow curvature/path X
BMW says: I will coordinate my chassis to do that
our validator says: confirm that the physical car actually followed X
```

## Rear-axle steering / IAS awareness

If Integral Active Steering is fitted, `bmwstated` should expose rear-steering availability and measured/estimated rear-steer state to the rest of the stack.

The planner does not necessarily need to decide individual rear-wheel angle. It does need to know that the vehicle dynamics include that degree of freedom so that:

- predicted path is correct
- lateral-control tuning is correct
- low-speed parking/summon geometry is correct
- lane-centering response is not misinterpreted
- motion faults can be detected

## Summon and parking

Rear steering is particularly relevant at parking speed because it changes swept path, turning radius and clearance at the front/rear corners.

The parking world model should therefore use the observed/estimated full-vehicle kinematics rather than assuming a fixed front-steer-only wheelbase model.

Near-field collision checking should account for body swept volume, not only centreline trajectory.

## Runtime checks

Examples of checks that should exist before later actuation stages:

### Steering-to-yaw consistency

If BMW reports steering activity but measured yaw does not follow the expected sign/magnitude, reduce/disable lateral autonomy.

### Rear-steer consistency

If IAS reports a rear angle/state inconsistent with expected BMW dynamics or becomes unavailable, switch to the appropriate degraded vehicle model or disable functions that depend on it.

### Wheel-speed consistency

Cross-check individual wheel speeds for implausible differences not explained by cornering/slip.

### IMU vs ICM

Compare independent IMU yaw/lateral acceleration with BMW dynamics signals where possible.

### GNSS/visual long-horizon check

At suitable speeds/conditions, compare integrated ego pose against GNSS heading/position and visual road-relative motion to catch persistent bias.

### DSC intervention

If DSC is actively correcting the car, the autonomy planner should know the requested trajectory is not being followed nominally and should become conservative rather than fighting the OEM stability controller.

## Fault response philosophy

A disagreement is not automatically proof the BMW is wrong or the autonomy model is wrong. It is evidence that the commanded-motion model is no longer trustworthy.

Response order should be conservative:

1. flag degraded confidence
2. reduce aggressiveness / stop new manoeuvres
3. yield to OEM stability intervention
4. request driver takeover where needed
5. disable lateral/remote-parking authority if consistency cannot be restored

## Logging

Every motion-validation event should log a synchronized window of:

- planner trajectory
- BMW command
- front/rear steer state
- wheel speeds
- yaw/accelerations
- DSC/ICM state
- GNSS/IMU
- camera/world-model ego trajectory
- driver input

This will be essential for learning the real F13 dynamics and validating an approximate model.

## Development stages

### MV0 — Read-only signal inventory

Identify available front/rear steering, ICM, DSC, wheel-speed and dynamics signals. No actuation.

### MV1 — Passive model fitting

Record normal human driving and fit/validate speed-dependent relationships between steering state and actual yaw/curvature.

### MV2 — Shadow trajectory validation

Compare openpilot planned trajectory against human-driven actual motion without sending commands.

### MV3 — HIL consistency tests

Exercise signal loss, stale data and impossible combinations in simulation/HIL.

### MV4 — Closed-course low-authority validation

Only after prior stages, compare commanded versus observed motion under controlled actuation.

## Design rule

**The autonomy stack decides where the vehicle should go. BMW's OEM chassis systems decide how their available actuators achieve that motion. Our motion-validation layer continuously verifies that the real vehicle is actually going where requested.**
