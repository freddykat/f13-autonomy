# fake_bmw

`fake_bmw` is a **read-only state simulator** for the Shadow Lab.

It generates synthetic `BMWChassisState` data for testing state estimation and trajectory validation without controlling any vehicle hardware.

Planned scenarios:

- steady curve
- lane-change observation
- rear-steer available/unavailable
- stale rear-steer signal
- DSC intervention flag
- wheel-speed disagreement
- BMW yaw vs independent IMU disagreement
- low-speed parking geometry with rear steering

Example synthetic state:

```text
vehicleSpeed = 80 km/h
frontSteerAngle = +1.2 deg
rearSteerAngle = +0.25 deg
yawRateBMW = +2.8 deg/s
dscInterventionActive = false
```

The module should support deterministic replay and explicit UNKNOWN/stale values.

No actuator commands or vehicle-control outputs belong in this module.
