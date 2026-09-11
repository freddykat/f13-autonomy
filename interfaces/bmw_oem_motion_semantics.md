# BMW OEM Motion Semantic Boundary

## Purpose
Define the non-actuating semantic boundary between openpilot planning, BMW OEM controller intent, and observed vehicle motion for the F12/F13 integration.

The project architecture is deliberately high level:

```text
openpilot planner
  -> desired trajectory + desired speed
  -> BMW OEM semantic bridge (research/shadow until separately approved)
  -> BMW PMA/ICM/EPS/DSC/IAS and OEM ACC controllers
  -> observed chassis motion
```

This document does **not** define any wire-level transmit message. It exists so replay, discovery and future HIL work cannot conflate a planner reference with an observation or an OEM request with actuator authority.

## Three lateral domains

### 1. `OP_PLANNED_LATERAL`
Planner/reference only.

Candidate fields:
- `timestamp`
- `desiredPath`
- `desiredCurvature`
- `desiredYawRate` where available
- `plannerProvenance`

It is never an observed-motion source.

### 2. `BMW_OEM_LATERAL_INTENT`
Read-only representation of a BMW OEM request/target if one is discovered in PMA/ICM/EPS/related traffic or diagnostics.

Candidate fields:
- `timestamp`
- `sourceController` (`PMA`, `ICM`, `EPS`, other proven owner)
- `semanticType` (`PATH`, `CURVATURE`, `STEERING_TARGET`, `STEERING_RATE`, `MANOEUVRE_STATE`, `UNKNOWN`)
- `value`
- `unit`
- `coordinateFrame`
- `freshness`
- `evidenceState`
- `provenance`

Until a field reaches the project evidence gate, it remains a candidate and must not be used as an authoritative control input.

### 3. `BMW_OBSERVED_LATERAL_MOTION`
Physical-result observation only.

Candidate sources:
- BMW yaw rate / speed
- independent IMU/GNSS/vision motion
- front steer state
- rear steer / HSR state
- geometric 4WS reconstruction as a model/corroborator

Observed motion is what `motionvalidatord` uses to determine what the car actually did.

## Three longitudinal domains

### 1. `OP_PLANNED_LONGITUDINAL`
Planner/reference only:
- desired speed
- desired gap / time headway intent where supported by the planner

### 2. `BMW_OEM_ACC_INTENT`
Read-only representation of OEM ACC state/accepted target:
- ACC availability/state
- set speed / accepted target speed
- gap setting
- lead state where exposed
- resume/cancel state transitions

BMW ACC remains the longitudinal execution owner. This interface does not authorize direct brake, throttle, DME, DSC or gearbox commands.

### 3. `BMW_OBSERVED_LONGITUDINAL_MOTION`
Physical-result observation:
- actual speed
- longitudinal acceleration
- brake/accelerator driver state
- DSC intervention
- drivetrain state as observation

## Comparison contract

Replay and validation should preserve these comparisons explicitly:

```text
lateralPlanningResidual = OP_PLANNED_LATERAL - BMW_OEM_LATERAL_INTENT
lateralExecutionResidual = BMW_OEM_LATERAL_INTENT - BMW_OBSERVED_LATERAL_MOTION
lateralEndToEndResidual = OP_PLANNED_LATERAL - BMW_OBSERVED_LATERAL_MOTION

longitudinalPlanningResidual = OP_PLANNED_LONGITUDINAL - BMW_OEM_ACC_INTENT
longitudinalExecutionResidual = BMW_OEM_ACC_INTENT - BMW_OBSERVED_LONGITUDINAL_MOTION
longitudinalEndToEndResidual = OP_PLANNED_LONGITUDINAL - BMW_OBSERVED_LONGITUDINAL_MOTION
```

Only compute a residual when the compared values share known compatible units, coordinate frame, semantics and adequate timestamp alignment. Otherwise report it unavailable; never coerce UNKNOWN into zero.

## F13 PMA discovery rule

A PMA/ICM/EPS/HSR candidate found during B1-1 may populate `BMW_OEM_LATERAL_INTENT` only after its semantic role is classified as request/target rather than feedback/actual state.

Evidence should include, where possible:
- read-only diagnostic name/unit corroboration;
- synchronized passive CAN/FlexRay observation;
- repeatable event correlation;
- request-before-response ordering where timing provenance permits;
- physical corroboration from steering/yaw/IMU;
- replay stability.

A field that merely changes during parking is not enough.

## IAS / rear-steer rule

Rear steering remains BMW-owned. A discovered BMW high-level path/curvature request is valuable precisely because it may allow the chassis stack to coordinate front steering, rear steering and DSC internally.

The project therefore keeps:

```text
rearSteerActuationAllowed = false
```

at every observation/replay stage.

## Authority invariants

- openpilot planner output is a reference, not direct actuator authority;
- BMW OEM semantic observations are read-only during B1-0/B1-1;
- no EPS/DSC/IAS/DME/brake/throttle/gear transmit path is defined here;
- no diagnostic write, coding or routine-control path is defined here;
- planner values may never be used as evidence that the vehicle actually moved as requested;
- OEM target values may never be silently substituted for observed physical motion;
- UNKNOWN/stale values remain unavailable, never zero.

Related: #13, #20, #45, #46, #47, #48.
