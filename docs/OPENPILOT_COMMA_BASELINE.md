# Openpilot + Comma Four baseline for Prototype 001

Status: architecture baseline for M0/M1 shadow development. **No vehicle actuation authority.**

## Decision

Prototype 001 should use a stock/current **Comma Four + official openpilot release** as the reference runtime before attempting a deep custom-compute fork.

As of 2026-09-05 the latest published `commaai/openpilot` GitHub release is **v0.11.1** (published 2026-06-05). Development work such as Chestnut/external-GPU support may be evaluated separately against upstream `master`, but it must not silently change the validated vehicle baseline.

Record for every replay/benchmark:

- openpilot release/tag and exact commit
- opendbc commit
- Panda/safety commit or firmware identity
- Comma hardware identity
- model artifact/version
- route/capture ID
- calibration identity

## M0/M1 architecture

```text
                  COMMA FOUR
          +------------------------+
road ---> | native road cameras    | ---> upstream modeld / openpilot
cabin --> | driver monitoring cam  |
          +-----------+------------+
                      |
                      | openpilot state / proposals
                      v
              F13 shadow integration
                      ^
                      |
     +----------------+-----------------------------+
     |                |                |             |
 BMW ACC radar     BMW SWW         BMW KAFAS     DSC / ICM
  front lead      blind spot       observation    vehicle state
     |                |                |             |
     +----------------+----------------+-------------+
                      |
           passive BMW observation layer
             CAN first / ENET support
             FlexRay listen-only fallback
```

The native Comma road-camera streams remain the reference input for upstream `modeld` during M0/M1. External surround cameras are not injected into the driving model merely because they exist.

## BMW OEM sensor adapters

### Front ACC radar

Preferred path:

1. discover whether useful ACC radar traffic/state is already available on a CAN path visible through the BMW gateway;
2. decode offline from passive captures;
3. normalize validated radar targets into the openpilot/opendbc `RadarData`/`RadarInterface` contract for replay/shadow comparison;
4. use direct FlexRay capture only if required information is absent from the accessible CAN path.

Do not assume that an ACC status bit, selected lead, or diagnostic measurement is equivalent to the radar's complete track list.

### Blind-spot / SWW

Validated left/right SWW state may feed the BMW `CarState` adapter using the standard blind-spot semantics (`leftBlindspot`, `rightBlindspot`) in replay/shadow mode.

Missing, stale, contradictory, or unqualified observations remain UNKNOWN/unavailable; they must not be converted to `false` merely because a frame was missed.

### KAFAS

KAFAS is an independent OEM observation source for lane/sign/FCW semantics where those signals can be validated. During M0/M1 it is a corroboration source, not a replacement for the Comma camera model and not an actuator authority.

### DSC / ICM

Wheel speed, yaw, acceleration, steering/chassis state and stability-intervention state should be normalized through `bmwstated` only after decoder evidence and freshness rules pass the existing cross-source gates.

### ENET / HSFZ / diagnostics

ENET is useful for ECU identity, units, scaling, slow state and semantic corroboration. Diagnostic response time is **not ECU sample time** and cannot satisfy tight motion-timing validation unless the source explicitly exposes measurement timing.

### FlexRay

FlexRay remains a fallback observation path for signals that cannot be obtained with adequate quality through accessible CAN/gateway data. M0/M1 permits listen-only capture/replay work only. FlexRay TX, MITM mutation, EPS/DSC requests and control translation are outside this baseline.

## External 360-degree cameras

The desired surround-camera system remains part of the project, but it is separated from upstream openpilot compatibility:

```text
external synchronized cameras
          |
    surround compute
          |
 detections / occupancy /
 free-space / provenance
          |
      WorldState
```

Initial uses:

- parking/surround visualization
- blind-zone corroboration
- rear/side approaching-object observations
- black-box recording
- offline perception development

Do not modify `modeld` to ingest arbitrary additional camera streams until the stock Comma/openpilot reference has deterministic replay coverage and there is a measured reason to change the upstream camera contract.

## Tesla HW4 verification lane

Tesla HW4 remains a **read-only behavioural benchmark**, not part of the F13 control chain.

A Tesla comparison episode should contain only externally observable/legitimately decoded state plus provenance, for example:

```text
scenario_id
source_software_version
source_hardware_variant
clock/timestamp provenance
vehicle speed
lead / relevant-object state where observable
lane-change state or intent where observable
desired speed / longitudinal state where observable
curvature / steering intent where observable
FCW / warning state
navigation/route state where observable
unknown/stale flags
```

For each synchronized scenario compare:

```text
Tesla observed behaviour
vs
openpilot proposal
vs
F13 shadow-planner proposal
vs
human action
```

Differences become review events. Tesla behaviour never automatically overwrites F13 safety/legal rules and no Tesla CAN modification/injection project is copied into the BMW actuation path.

## Safety invariants for this baseline

M0/M1 integration artifacts must satisfy all of the following:

- `actuation_authority = NONE`
- no `CarController` implementation that emits BMW actuator commands
- no `sendcan` path for BMW control
- no FlexRay TX or MITM mutation
- no EPS/DSC/DME actuation
- no diagnostic coding/routine-control API in observation adapters
- stale/UNKNOWN never silently becomes zero/false
- signal provenance and timing class are preserved through replay
- a faster GPU or additional sensor does not relax replay/HIL gates

## Promotion sequence

1. Official openpilot + Comma Four baseline recorded and reproducible.
2. Passive OBD/gateway CAN inventory.
3. Offline BMW decoder manifest entries with evidence.
4. ACC radar and SWW replay adapters.
5. KAFAS/DSC/ICM shadow corroboration.
6. External 360 perception into `WorldState`, not actuator interfaces.
7. Tesla/openpilot/F13 synchronized disagreement corpus.
8. Only after replay and HIL: separately reviewed control-interface research.

## Current concrete target

Produce one synchronized, read-only F13 capture where the driver deliberately exercises:

- ACC lead acquisition/loss and gap-selection changes;
- a vehicle entering/leaving each SWW blind zone;
- steady speed and controlled acceleration/deceleration;
- several gentle steering/yaw changes.

Use the existing CAN evidence pipeline to establish capture integrity before proposing any decoder mapping. The output of this milestone is a trustworthy observation corpus, not a vehicle command.