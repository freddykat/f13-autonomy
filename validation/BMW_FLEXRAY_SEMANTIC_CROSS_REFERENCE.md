# BMW FlexRay semantic cross-reference

Status: **read-only research artifact**. This document does not define or authorize any live BMW command, FlexRay transmit path, restbus emulation, EPS/DSC/HSR actuation, powertrain actuation, coding, or diagnostic write.

## Purpose

Use publicly documented BMW F-series architecture as a semantic Rosetta Stone for the F13. Cross-series evidence may narrow the search space, but it never proves F13 slot, cycle, payload, scaling, timing, or control authority.

Evidence promotion is intentionally one-way:

`CROSS_SERIES_REFERENCE -> F13_FRAME_CANDIDATE -> F13_EVENT_CORRELATED -> F13_DIAGNOSTICALLY_CORROBORATED -> F13_CROSS_SOURCE_VALIDATED -> F13_REPLAY_STABLE -> F13_STATE_SOURCE_CANDIDATE`

## Architecture observations worth carrying forward

| Reference platform | Public architectural observation | Project use | F13 status |
|---|---|---|---|
| F01/F02 | FlexRay networks dynamic-driving controllers and engine management; simplified BMW training topology shows ZGM, DME, DSC, SZL, HSR, AL, SWW, ICM, VDM and EDC nodes. | Establishes BMW's chassis/powertrain FlexRay separation and reusable controller roles. | `CROSS_SERIES_REFERENCE` |
| F12/F13 | BMW training topology explicitly identifies EPS, DSC, VTG, DME, VDM, HSR, PMA, ICM, ZGM, SZL and Active Steering in the F12/F13 electrical architecture. | Primary authority for which controller families are relevant to Prototype 001. | `F13_ARCHITECTURE_EVIDENCED` only; no signal IDs inferred. |
| F30 | BMW training material describes FlexRay as the system bus for dynamic-handling and engine-control systems; DSC, DME/DDE, EPS, VDM, SWW and ICM are FlexRay participants through the ZGM/FEM star coupler. | Useful donor vocabulary for ICM/DSC/EPS state and network behavior. | `CROSS_SERIES_REFERENCE` |
| F30 PHEV | Public BMW bus overview keeps DSC, VDM, EPS and ICM on FlexRay while hybrid powertrain modules including DME, EME and SME occupy powertrain networks. | Strong architecture clue for keeping a stable BMW chassis contract while replacing propulsion backend. | `CROSS_SERIES_REFERENCE`; do not assume F13-compatible EME messages. |
| F01 ACC Stop & Go | BMW training material shows ZGM, DSC, radar, DME and ICM around a FlexRay-based ACC interface. | Supports studying OEM longitudinal semantics at the chassis/powertrain boundary without replacing BMW actuator ownership. | `CROSS_SERIES_REFERENCE` |

## First semantic families

The machine-readable companion manifest tracks these families without assigning guessed F13 frame identities:

### Chassis core
- vehicle and individual wheel speed
- yaw rate
- lateral / longitudinal acceleration
- steering-wheel angle
- front rack / road-wheel actual angle
- driver steering torque
- steering actuator torque
- ICM chassis/motion state
- DSC intervention/state
- EPS availability/fault state
- HSR/IAS rear-steer actual state/angle
- PMA manoeuvre / trajectory / steering-request candidates

### Powertrain/chassis boundary
- propulsion-ready / engine-running equivalent
- current and available drive torque
- torque limits and torque-reduction state
- direction / gear state
- drivetrain availability/fault
- traction-limited state
- brake/regen interaction state
- VTG/xDrive state where relevant

### Hybrid/BEV donor vocabulary
- EME/electric-drive state
- motor torque actual/available
- recuperation/regen limits
- HV ready/fault state
- interaction with ICM/DSC

These are semantic hypotheses only. No cross-series message identity may be copied into an F13 decoder.

## Capture contract

Because FlexRay now serves both autonomy research and future OEM-like ICE-to-BEV compatibility work, the passive recorder must preserve at least:

- physical/logical channel;
- cycle identity;
- slot/frame identity;
- payload length and payload bytes;
- receive timestamp and clock provenance;
- adapter identity and firmware version;
- listen-only declaration;
- drop/overflow/loss observability;
- capture/session identity.

A USB batch timestamp is not ECU sample timing. Missing cycle/slot/timing metadata must remain explicit rather than synthesized.

## Promotion rules

1. Cross-series documentation creates hypotheses, never F13 truth.
2. The F13 remains the authority for frame identity, scaling, freshness and timing.
3. Read-only ENET/SGBD diagnostics may corroborate names, units and ownership, but diagnostic response time is not realtime bus timing.
4. Motion semantics require independent physical corroboration where practical (IMU/GNSS/video/observed steering).
5. UNKNOWN or stale data never becomes zero.
6. Request/target and physical feedback remain distinct.
7. Deterministic replay is required before state-source candidacy.
8. Observation authority never grants actuation authority.

## ICE / BEV compatibility principle

OpenPilot-facing chassis semantics should not depend on whether propulsion is N63/EGS or a future VCU/inverter backend. The research target is a normalized observed chassis contract and a separately characterized powertrain boundary.

No live BEV restbus implementation is authorized by this document. Any future transmitting compatibility layer requires separate human review plus simulation/HIL validation.

## Public-source provenance

Initial architecture references reviewed 2026-09-13:

- BMW Technical Training, `ST1109 F12/F13 Complete Vehicle` — F12/F13 vehicle-electronics topology.
- BMW Technical Training, `ST401 Body Electronics II` — FlexRay application in F0x vehicles.
- BMW Technical Training, `ST1113 F30 Complete Vehicle` — F30 FlexRay system-bus description.
- BMW Technical Training, `ST401b Bus System Overview` — F30 PHEV bus overview.
- BMW Technical Training, `ST055 Engine Electronics` — F01 ACC Stop & Go bus interface.

URLs and exact evidence notes belong in the companion manifest so future rows remain auditable.
