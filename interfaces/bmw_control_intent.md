# BMWControlIntent

`BMWControlIntent` is the transport-independent control contract for future BMW actuation research.

It exists so planners never emit raw CAN or FlexRay messages directly.

Current project status is **SHADOW/HIL RESEARCH ONLY**. No consumer may translate this interface into live vehicle actuation.

## Top-level structure

```text
BMWControlIntent
├── lateral
├── longitudinal
├── indicators
├── parking
├── gear
├── brakeHold
├── authority
└── provenance
```

## lateral

Candidate fields:

- `targetCurvature`
- `targetCurvatureRate`
- `targetSteeringAngle` where a validated actuator requires angle control
- `targetSteeringTorque` where a validated actuator requires torque control
- `maxLateralAcceleration`
- `requestSource`
- `validUntil`

No field implies that the BMW actuator accepts that command form.

The eventual actuator adapter must convert only after the real F13 actuator protocol has been independently validated.

## longitudinal

Candidate fields:

- `targetSpeed`
- `targetAcceleration`
- `targetJerk`
- `stopRequest`
- `resumeRequest`
- `oemAccPreferred`

Initial strategy should prefer orchestration of the OEM ACC path over direct throttle/brake control whenever that path can safely provide the required behavior.

## indicators

Candidate fields:

- `NONE`
- `LEFT`
- `RIGHT`
- `HAZARD`

Driver stalk input always wins.

Indicator state feedback must be observed independently from any future request channel.

## parking

Candidate fields:

- `parkingMode`
- `targetPose`
- `targetCurvature`
- `targetSpeed`
- `stopDistance`
- `obstacleEnvelope`
- `directionIntent`

Parking trajectory generation is separate from highway/openpilot trajectory planning.

Gear automation remains a separate authority domain.

## gear

Candidate values:

- `P`
- `R`
- `N`
- `D`

This domain is intentionally isolated because a wrong gear request has substantially different hazards from a steering or indicator request.

Prototype 001 begins with gear authority disabled.

## brakeHold

Candidate fields:

- `holdRequested`
- `releaseRequested`
- `standstillRequired`

This domain may later map to DSC/parking-brake behavior, but no actuator mapping is assumed.

## authority

Authority is per-domain, never one global AUTONOMY switch.

Current allowed research states:

- `DISABLED`
- `SHADOW`
- `HIL_ONLY`

Future states may be introduced only after explicit safety review and staged validation.

Example:

```text
lateral:       SHADOW
longitudinal:  SHADOW
indicators:    SHADOW
parking:       SHADOW
gear:          DISABLED
brakeHold:     DISABLED
```

## Required driver overrides

Any future actuation implementation must treat these as higher priority than automation:

- steering-wheel torque / steering intervention
- brake pedal
- accelerator pedal where appropriate
- turn-signal stalk
- gear selector
- parking-brake input
- ignition/power state

## Required actuator feedback

A command path is not sufficient by itself.

Each domain requires independent feedback:

### lateral

- steering wheel angle
- front road-wheel angle where available
- steering torque / driver override
- yaw rate
- EPS/ICM/IAS health
- rear steer state where equipped

### longitudinal

- vehicle speed
- wheel speeds
- brake state / brake pressure where available
- accelerator state
- longitudinal acceleration
- DSC intervention
- ACC/DME/DSC health

### indicators

- actual left/right/hazard lamp state

### parking

- wheel speeds
- steering angle
- PDC/ultrasonic state
- surround/depth/Scene3D state
- obstacle distance
- gear state
- brake state

## Transport separation

The control intent never contains CAN arbitration IDs, FlexRay slots, checksums, alive counters or transport framing.

```text
planner
   ↓
BMWControlIntent
   ↓
domain actuator adapter
   ↓
validated BMW semantic request
   ↓
CAN or FlexRay encoder
```

This prevents planner logic from becoming coupled to BMW network details.

## Safety invariant

In M0/M1 development, `BMWControlIntent` is logged and replayed only.

There is no live encoder, `sendcan`, FlexRay TX, diagnostic write, Panda safety bypass, EPS command path, DSC command path, gear command path or body-control command path attached to this interface.
