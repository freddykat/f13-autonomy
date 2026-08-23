# BMW Chassis State Interface

This interface is **read-only**. It represents the BMW chassis domain as observed by the autonomy stack.

The autonomy stack must not assume that reading a signal implies authority to command the corresponding actuator.

## Proposed state

```text
BMWChassisState {
    timestamp

    vehicleSpeed
    wheelSpeedFL
    wheelSpeedFR
    wheelSpeedRL
    wheelSpeedRR

    steeringWheelAngle
    frontSteerAngle
    frontSteerRate

    rearSteerAvailable
    rearSteerActive
    rearSteerAngle
    rearSteerRate

    yawRateBMW
    lateralAccelerationBMW
    longitudinalAccelerationBMW

    epsState
    icmState
    dscState
    dscInterventionActive
    iasState

    brakePressed
    acceleratorPressed
    gear

    validity {
        frontSteer
        rearSteer
        yawRate
        lateralAcceleration
        wheelSpeeds
        eps
        icm
        dsc
        ias
    }
}
```

## Validity rules

- Unknown or stale values must remain explicitly invalid/unknown.
- Never silently convert missing rear-steer data to `0.0`.
- Every signal group should carry a timestamp or freshness state.
- The motion estimator should refuse to treat stale chassis states as current measurements.

## Purpose

This state feeds:

- vehicle-motion reconstruction
- requested-vs-observed trajectory validation
- rear-steer-aware swept-path prediction
- DSC/ICM intervention detection
- diagnostics
- logging and disagreement analysis

It does **not** directly feed actuator commands.
