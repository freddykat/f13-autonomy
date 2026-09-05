# BMW F13 message semantic correlation map

Status: pre-vehicle research only. Read-only. No actuation authority.

This document converts public BMW F-series diagnostic semantics into a correlation plan for the December 2026 Prototype 001 capture campaign. It intentionally does not assign CAN/FlexRay frame IDs unless supported by vehicle evidence.

## Confidence model

- `DOCUMENTED_SEMANTIC`: message/signal name or ECU relationship appears in public BMW/EDIABAS-derived documentation.
- `FAMILY_ASSOCIATION`: ECU is explicitly associated with F12/F13, but exact transport/payload remains unknown.
- `CORRELATION_TARGET`: expected physical behavior to use when searching raw captures.
- `VEHICLE_VALIDATED`: reserved for Prototype 001 evidence. None below are vehicle validated.

## FRR / KAFAS / ICM interaction graph

Public SGBD fault semantics show a useful relationship between the front radar, camera and chassis domains:

```text
KAFAS
  ├─ DT_LNDT_*          lane-detection data
  └─ ST_OBJDT_KAFAS     KAFAS object-data status
          ↓
        FRR_10
          │
          └─ OBJDT_HDWOBS   front-surveillance/radar object data
                    ↓
                  ICM-family consumers
```

This is a semantic dependency graph, not proof of bus topology or CAN IDs.

### Documented semantics

| Semantic | Source ECU | Consumer/observer evidence | Meaning | December correlation |
|---|---|---|---|---|
| `DT_LNDT_*` | KAFAS | FRR_10 fault semantics | lane-detection data | lane markings appear/disappear, lane changes, curves |
| `ST_OBJDT_KAFAS` | KAFAS | FRR_10 fault semantics | KAFAS object-data status | camera object availability / degraded camera conditions |
| `OBJDT_HDWOBS` | FRR | ICM-family fault semantics | front-surveillance/radar object data | target acquire/loss, range change, closing/opening rate |

## P0 ACC / FRR correlation targets

The first goal is not a full radar DBC. It is to determine which observable semantics reach the capture point and which remain internal to FRR/FlexRay.

| Desired field | Expected physical behavior | Search/correlation strategy | Promotion requirement |
|---|---|---|---|
| ACC active/standby | toggle ACC, cancel/resume | low-entropy state changes exactly on driver event markers | repeatable across runs |
| set speed | change set speed in known increments | monotonic field with step changes matching cluster | unit/scaling cross-check |
| following gap | cycle gap setting | small discrete state space | exact state transition match |
| selected lead valid | lead enters/leaves lane | bit/enum transition near radar acquire/loss | cross-check cluster/ACC behavior |
| lead distance | stationary/steady lead at varied spacing | monotonic continuous field correlated with range | independent distance estimate where practical |
| relative velocity | closing/opening on lead | sign and magnitude correlate with range derivative | consistency with differentiated range |
| lateral offset | lead moves within lane / adjacent lane | smooth signed change around ego centerline | repeatability + plausible sign convention |
| track id | same lead persists | stable identifier until target switch | lifecycle consistency |
| object validity/age | target appears/disappears | counter/enum freshness behavior | stale semantics explicitly decoded |

Do not expose `radarTracks` unless evidence shows a genuine track list. A selected-lead-only message must remain selected-lead-only.

## P0 HC2 / SWW correlation targets

`HC2_01` is explicitly associated with F12/F13 in the public ECU inventory and represents lane-change warning / heading-control functionality.

| Desired field | Expected physical behavior | Search/correlation strategy |
|---|---|---|
| left warning | vehicle occupies left blind zone | bit/enum activates only on left-side event |
| right warning | vehicle occupies right blind zone | mirror of left test |
| warning stage | approach vs established blind-zone occupancy | look for multi-level state if present |
| system available | startup / fault / speed threshold | identify availability separate from clear/no-object |
| sensor health | diagnostic/fault condition | never infer healthy from missing warning |
| stale/invalid | loss of source / unavailable state | must remain UNKNOWN, not false |

The first useful openpilot adapter may use only `leftBlindspot` and `rightBlindspot`; full SRR object fusion is not required for M1.

## P0 ICM / DSC motion correlation targets

Public `ICM_25` diagnostic semantics include yaw-rate, lateral-acceleration and steering-angle related states and wheel-speed-derived yaw checks. These are semantic anchors, not bus mappings.

| Desired field | Physical test | Independent reference |
|---|---|---|
| steering angle | fixed left/right wheel positions and gentle sine steering | SZL/diagnostic observation where available |
| steering rate | slow vs faster steering sweeps | derivative of validated steering angle |
| yaw rate | constant-radius left/right turns | independent IMU |
| lateral acceleration | increasing/decreasing cornering | independent IMU |
| longitudinal acceleration | gentle accel/coast/brake | independent IMU/GNSS |
| wheel speeds FL/FR/RL/RR | straight drive then turns | speed + expected inner/outer wheel differential |
| DSC intervention | controlled low-traction/HIL only, not early road test | explicit DSC state / cluster indication |
| vehicle standstill | stop/start transitions | GNSS/wheel speed consensus |

## Candidate named semantics to search across public F-series artifacts

These names are useful grep/search targets in EDIABAS-derived docs and any future public DBC/log corpus:

- `OBJDT_HDWOBS`
- `ST_OBJDT_KAFAS`
- `DT_LNDT_*`
- `TAR_WSTA_FTAX_PMA`
- `TAR_VIB_STW_WARN_LNDP`
- `ST_VHSS`
- HC2/SWW-related status names
- ICM yaw/lateral-acceleration/steering-angle status labels

Their presence in another chassis or ECU generation is corroboration only; exact Prototype 001 transport and scaling still require capture evidence.

## December event-marker protocol

Every passive capture should include explicit human event markers. Recommended markers:

```text
ACC_ON
ACC_OFF
ACC_SET_UP
ACC_SET_DOWN
ACC_GAP_1 ... ACC_GAP_N
LEAD_ACQUIRE
LEAD_LOSS
LEAD_CLOSING
LEAD_OPENING
BLIND_LEFT_ENTER
BLIND_LEFT_EXIT
BLIND_RIGHT_ENTER
BLIND_RIGHT_EXIT
STEER_LEFT_SLOW
STEER_RIGHT_SLOW
STEER_CENTER
BRAKE_LIGHT
ACCEL_LIGHT
STOPPED
```

The offline analyzer should rank candidate bytes/bits by correlation with these markers, but must never automatically promote a decoder without human review and replay validation.

## Promotion boundary

A named semantic may be copied into the real decoder manifest only when:

1. source capture provenance passes quality gates;
2. the candidate changes at the expected physical event;
3. direction/sign/scaling are independently plausible;
4. timing and freshness are measured;
5. UNKNOWN/stale behavior is represented;
6. replay regression tests exist;
7. no transmit path is introduced.

## Source snapshot

Primary public evidence snapshot used for this map:

- `emdzej/ediabasx-docs-sgbd` @ `b644de8fbfbb4b207f57794e3c7894dc1dc58627`
  - `docs/sgbd/frr_10.md`
  - `docs/sgbd/icmql.md`
  - `docs/sgbd/icm_25.md`
  - `docs/sgbd/hc2_01.md`
  - `docs/sgbd/T_INPA.md`

No live-control or write-capable diagnostic procedures from these files are part of this research path.
