# BMW F-series signal research matrix

Status: pre-vehicle research for Prototype 001. **Read-only. No actuation authority.**

The purpose of this matrix is to reduce December 2026 vehicle-test time by separating what is publicly documented for the F12/F13 family from what is merely plausible and what still requires evidence from Prototype 001.

## Confidence classes

- `DOCUMENTED_FAMILY`: a public BMW/EDIABAS-derived source explicitly associates the ECU/function with F12/F13 or exposes the semantic through the relevant ECU family.
- `COMMUNITY_CORROBORATED`: multiple credible community/reverse-engineering observations support the topology or behavior, but the exact Prototype 001 mapping is not yet proven.
- `SPECULATIVE`: useful research hypothesis only.
- `VEHICLE_VALIDATED`: reserved for December captures from Prototype 001 that pass capture-quality, provenance and cross-source gates. **Nothing in this document is VEHICLE_VALIDATED yet.**

Diagnostic ECU addresses below are **not CAN frame IDs**.

## Priority matrix

| Priority | Desired state | Candidate ECU/family | Diagnostic address | F12/F13 evidence | Candidate transport | openpilot/shadow target | Confidence |
|---|---|---|---:|---|---|---|---|
| P0 | front ACC radar identity/state/tracks | `FRR_10` | `0x21` | EDIABAS inventory explicitly lists F12/F13 | unknown; test ZGW-visible CAN first | `RadarData` / `radarTracks` | DOCUMENTED_FAMILY |
| P0 | blind-spot / lane-change warning L/R | `HC2_01` | `0x08` | EDIABAS inventory explicitly lists F12/F13 | HC2 network; exact gateway-visible path TBD | `leftBlindspot`, `rightBlindspot` | DOCUMENTED_FAMILY |
| P0 | chassis motion / yaw / lateral accel / steering semantics | `ICM_25` | `0x1C` | EDIABAS inventory explicitly lists F12/F13 | CAN/FlexRay TBD | `BMWChassisState` | DOCUMENTED_FAMILY |
| P0 | wheel speeds / DSC intervention / brake dynamics | DSC family | `0x29` family address | F-series DSC exists at this address family; exact Prototype 001 variant TBD | CAN/FlexRay TBD | `BMWVehicleState.chassis` | SPECULATIVE |
| P1 | KAFAS/TLC lane/sign/FCW observations | KAFAS/TLC family | `0x5D` family address | F-series diagnostic inventory uses 0x5D; exact 2012 F13 variant/options TBD | CAN/diagnostic/FlexRay TBD | corroboration into `WorldState` | SPECULATIVE |
| P1 | gear selector state | `GWS2` | `0x5E` | EDIABAS inventory explicitly lists F12/F13 | CAN likely; verify | `BMWVehicleState.powertrain` | DOCUMENTED_FAMILY |
| P1 | front/rear steering relationship / IAS state | ICM + steering ECU family | TBD | chassis architecture supports coordinated dynamics; exact signal path TBD | FlexRay/CAN TBD | `BMWChassisState.rear_steer` | SPECULATIVE |

## Evidence already strong enough to guide capture design

### FRR_10 — front full-range radar

The public EDIABAS inventory identifies `FRR_10` at diagnostic address `0x21` as a Full Range Radar and explicitly lists F12 and F13 among supported chassis.

This proves that `FRR_10` is a valid F13-family ECU target for investigation. It does **not** prove that full object tracks are available at the OBD/ZGW CAN capture point.

December questions:

1. Is `FRR_10` present in the actual vehicle ECU tree?
2. Which software/hardware variant is installed?
3. Which FRR-originated frames are visible through ZGW/OBD?
4. Do those frames expose only selected-lead/ACC state, or a fuller object list?
5. Can ENET/UDS measurements corroborate units/scaling without being used as a timing authority?

### HC2_01 — lane-change warning / blind spot

The EDIABAS inventory identifies `HC2_01` at diagnostic address `0x08` as `Spurwechselwarnung` and explicitly lists F12/F13.

The HC2 SGBD exposes initialization/calibration status DIDs, confirming that this is a distinct radar-based driver-assistance controller family rather than merely a cluster indication.

Community retrofit evidence for F10-family cars further reports a master/slave rear-radar arrangement, with the master connected into the vehicle's FlexRay/ZGW path and the slave linked to the master. That topology remains `COMMUNITY_CORROBORATED` until confirmed on Prototype 001.

December questions:

1. Is `HC2_01` present and which radar is master/slave?
2. Can a simple left/right hazard state be seen on gateway-visible CAN?
3. If not, is a usable observation exposed on FlexRay?
4. Which state distinguishes unavailable/stale from clear?
5. Can mirror-warning activity be independently correlated with the decoded state?

### ICM_25 — integrated chassis management

The EDIABAS inventory explicitly includes F12/F13 for `ICM_25` at diagnostic address `0x1C`.

The public `icm_25` SGBD contains semantics for yaw-rate sensor calibration/monitoring, lateral acceleration, steering-angle calibration and wheel-speed-derived yaw checks. These are useful semantic anchors for cross-source validation, but they are **not yet bus-frame mappings**.

December questions:

1. Which motion states are present on ZGW-visible CAN?
2. Which remain on FlexRay?
3. What are the update periods and freshness counters?
4. Can yaw/lateral acceleration be cross-checked against an independent IMU?
5. Can steering angle be cross-checked against SZL/diagnostic values?

## Candidate research fields

### P0 — ACC / FRR

Search for evidence of:

- ACC enabled/available/active
- set speed
- selected following gap
- selected lead valid
- lead longitudinal distance
- relative longitudinal velocity
- relative acceleration if available
- lateral offset if available
- object/track identifier
- object validity/age
- stationary/moving classification
- FCW or braking-request state where observable

A decoder must not label selected-lead state as a full radar track list.

### P0 — SWW / HC2

Search for:

- left warning
- right warning
- warning intensity/stage
- sensor availability
- initialization/calibration state
- left/right radar health
- trailer/suppression state where applicable
- stale/invalid semantics

The first useful openpilot mapping is binary/tri-state blind-spot occupancy, not full short-range-radar fusion.

### P0 — chassis / ICM / DSC

Search for:

- vehicle speed
- four individual wheel speeds
- steering wheel angle
- steering angle rate
- yaw rate
- lateral acceleration
- longitudinal acceleration
- brake pedal / brake pressure semantics
- DSC intervention
- ABS intervention
- traction-control intervention
- drive-mode/chassis-mode state
- front steering state
- rear-steer/IAS availability and angle if fitted

## Source provenance

Primary public research source used for the family-level claims above:

- `emdzej/ediabasx-docs-sgbd`, generated documentation of BMW EDIABAS SGBDs:
  - `docs/sgbd/T_INPA.md` — ECU/chassis inventory, including FRR_10, HC2_01 and ICM_25 F12/F13 associations.
  - `docs/sgbd/icm_25.md` — ICM status/diagnostic semantics.
  - `docs/sgbd/hc2_01.md` — HC2 status/calibration semantics.
  - `docs/sgbd/frr_10.md` — FRR ECU diagnostic definitions and KAFAS interaction fault semantics.
  - `docs/sgbd/zgw_01.md` — F-series ZGW diagnostic CAN receive functionality.

Pinned research snapshot:
`https://github.com/emdzej/ediabasx-docs-sgbd/tree/b644de8fbfbb4b207f57794e3c7894dc1dc58627`

Community topology corroboration only:
- F10 LCW retrofit reports describing HC2 master/slave and ZGW/FlexRay wiring. Treat as topology hints, never decoder truth.

## December promotion rule

A candidate may enter `validation/manifests/prototype_001_bmw_decoders.json` only when all applicable conditions are met:

1. raw capture provenance passes the existing capture-quality gate;
2. the signal changes in a controlled, expected scenario;
3. units/scaling are supported by an independent source where practical;
4. timing/freshness are measured rather than inferred;
5. stale/UNKNOWN behavior is defined;
6. source ECU/bus attribution is supported;
7. at least one replay regression test is added;
8. no transmission path is introduced.

Until then, candidate research belongs only in the candidate manifest and this document.
