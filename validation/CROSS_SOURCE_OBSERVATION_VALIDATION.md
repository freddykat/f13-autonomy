# Cross-source observation validation

Purpose: validate read-only vehicle state by comparing independent observation paths before a signal is trusted by `BMWVehicleState`, `motionvalidatord`, or replay analysis.

This document does **not** define or authorize any actuation path.

## Why this exists

A plausible decoded CAN/FlexRay value can still be wrong because of:

- incorrect signal decoding
- wrong vehicle/firmware variant
- logger drops
- batch rather than per-sample timestamps
- stale diagnostic responses
- unit/scaling mistakes
- sensor faults
- gateway/replay artefacts

The M1 stack should therefore distinguish **observed** from **independently corroborated**.

## Candidate independent paths

For motion-state work:

```text
BMW CAN/FlexRay passive capture
           |
           +----> normalized candidate signal
           |
BMW ENET/HSFZ/UDS read-only diagnostics
           |
           +----> normalized candidate signal
           |
Independent GNSS/IMU / visual odometry
           |
           +----> normalized candidate signal
                         |
                         v
             cross-source validator
                         |
                AGREE / DISAGREE /
                SINGLE_SOURCE / UNKNOWN
```

ENET diagnostics are a useful semantic/reference path, but diagnostic cadence and response time are not assumed to equal bus-sample timing. Each response needs explicit timing provenance and age.

## Observation contract

Every candidate observation carries:

- semantic signal name
- source identifier
- value or explicit missing value
- unit
- source/sample timestamp where actually available
- receive timestamp
- validity: `VALID / UNKNOWN / INVALID / STALE`
- confidence
- timing provenance

Unknown/stale values are never converted to zero.

## Comparison rules

1. Convert to a common semantic signal and unit before comparison.
2. Exclude invalid, stale, missing, or untrusted-timing observations from time-sensitive agreement checks.
3. One trustworthy source produces `SINGLE_SOURCE`, not `AGREE`.
4. Two or more independent trustworthy sources within a signal-specific threshold produce `AGREE`.
5. Excess disagreement produces `DISAGREE`; do not average it away and publish a falsely precise value.
6. Mixed units/signals are rejected before numerical comparison.
7. Thresholds are signal-specific and must be justified from sensor accuracy, calibration and expected dynamics.

## Initial M1 targets

### Yaw rate
Compare passive BMW dynamics state with independent IMU. ENET can be a slower semantic cross-check if an appropriate read-only measurement is available.

### Vehicle speed
Compare BMW vehicle/wheel-derived speed with GNSS speed where conditions permit. Wheel-speed disagreement is retained separately rather than collapsed immediately.

### Steering / vehicle curvature
Compare any decoded steering/rear-steer state with observed yaw/trajectory. The validator must not infer steering actuation authority from correlation.

### Longitudinal/lateral acceleration
Compare BMW/ICM-derived state with an independently mounted IMU after frame alignment and calibration.

## Provenance classes

Examples:

- `per_frame_monotonic`
- `per_sample_monotonic`
- `diagnostic_response_timestamp`
- `usb_batch_wall_clock`
- `unknown`

Only explicitly per-frame/per-sample monotonic timing is accepted by the initial implementation for tight temporal agreement. Diagnostic responses can still be used for semantic/range validation under a separate slower-cadence policy once response timing is characterized.

## Integration boundary

The validator is observational only:

```text
raw capture / diagnostics / independent sensors
        -> normalization
        -> cross-source validation
        -> trust metadata
        -> BMWVehicleState / motionvalidatord / replay
```

There is no reverse path from this validator to EPS, DSC, ICM, FlexRay transmission, torque, brake, or steering commands.

## Promotion requirement

A decoded safety-relevant motion signal should not become an authoritative normalized source merely because it looks plausible in one drive. Promotion should require repeatable agreement over a recorded corpus, explicit stale/loss behavior, known units/scaling, provenance, and regression coverage.
