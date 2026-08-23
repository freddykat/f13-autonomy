# BMWDynamicCapabilityState

Read-only/shadow interface describing the longitudinal capability the BMW is likely to deliver in its current mode and state.

This is a prediction interface for planning. It does **not** command gearbox, engine torque, boost, xDrive, DSC or any other actuator.

## Fields

```text
BMWDynamicCapabilityState {
    timestamp
    validity
    confidence

    driveMode
    transmissionMode
    gear
    engineRpm
    vehicleSpeed

    minAccel
    maxAccel
    comfortableMaxAccel
    maxJerk
    responseDelay

    downshiftLikely
    shiftInProgress
    tractionLimited
    thermalLimited
    dscIntervention

    roadGrade
    gradeValid

    sourceFreshness
}
```

## Semantics

- `minAccel`: estimated most negative longitudinal acceleration available under current conditions when the normal BMW brake/control domain is healthy. For early shadow work this can remain UNKNOWN rather than inferred.
- `maxAccel`: estimated achievable positive acceleration in the current state.
- `comfortableMaxAccel`: a softer planning envelope for normal GT driving. This is a comfort target, not a safety limit.
- `maxJerk`: estimated acceptable/observed longitudinal jerk envelope for planning.
- `responseDelay`: expected delay between a high-level acceleration request and meaningful vehicle response. Includes effects such as current gear and likely downshift latency.
- `downshiftLikely`: predicted from current mode/gear/speed and observed historical response. It is not a command.
- `shiftInProgress`: observed gearbox state where available.
- `tractionLimited`: observed or inferred limitation from DSC/traction state.
- `thermalLimited`: only VALID when supported by real BMW state or a validated estimator; otherwise UNKNOWN.

## UNKNOWN vs zero

UNKNOWN data must never be silently represented as zero. A missing grade, missing thermal state or unavailable drive-mode signal must reduce confidence or mark the relevant field invalid.

## Planner use

Typical use:

```text
candidate manoeuvre
      |
required acceleration/time/distance
      |
BMWDynamicCapabilityState
      |
feasible with margin?
      |
YES -> candidate remains eligible
NO  -> wait / choose different gap / stay in lane
```

A more aggressive BMW mode may improve predicted response but must not reduce the planner's safety margins.

## Learning/calibration

The state should eventually be calibrated from passive logs grouped by mode, gear, RPM, speed, road grade and relevant limitation states. Learned corrections sit on top of a transparent physical baseline rather than replacing it with an opaque end-to-end actuator model.
