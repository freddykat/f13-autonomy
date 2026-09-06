# SAS-in-the-Loop Semantic Bridge

Status: research architecture only. No direct F13 actuation.

## Core hypothesis

A modern BMW SAS can potentially be operated in an isolated bench environment by reproducing enough of the vehicle context it expects.

The goal is not to transplant a G-series SAS into the F13 as a plug-and-play controller.

The goal is to let the SAS run as a **teacher ECU** and observe:

- what information it expects;
- what states it publishes;
- what requests it produces;
- how it reacts to missing, stale or contradictory inputs;
- how BMW separates enable/state/request/feedback/fault semantics.

## Why the hypothesis is plausible

BMW G-series architecture places SAS on the vehicle network as a coordination ECU rather than as a sensor module.

Public BMW technical material indicates that SAS:
- has no primary sensors of its own;
- receives information from other control units and sensors;
- activates/coordinates control units required for driver-assistance functions;
- participates in FlexRay-based vehicle architecture;
- coexists with KAFAS, ACC, EPS, DSC/VDP and gateway/network-management functions.

This makes it a strong candidate for an isolated “virtual vehicle around SAS” experiment.

## Intended role: ADAS domain coordinator

The SAS should be thought of as the **central ADAS coordinator above the perception ECUs**, not as a replacement for KAFAS.

In a modern BMW-style architecture:

```text
KAFAS / front camera ─┐
ACC/front radar ──────┤
side radars ──────────┤
parking/PDC ──────────┤
ICM/DSC/EPS state ────┤
gear/driver inputs ───┤
                      ▼
                     SAS
                      │
            unified ADAS state / requests
                      │
             chassis / body domains
```

For the F13 concept, the equivalent long-term research architecture is:

```text
KAFAS2 retrofit ──────┐
OEM FRR radar ────────┤
OEM SWW/HC2 radars ───┤
Parking High / PDC ───┤
ICM / DSC / IAS ──────┤
BMWVehicleState ──────┤
                      ▼
        F-series compatibility layer
                      │
                      ▼
                SAS teacher/shadow
                      │
             semantic ADAS state
                      │
            Comma/openpilot comparison
```

The compatibility layer is essential because F-series modules cannot be assumed to publish the exact G-series protocol expected by SAS.

Therefore the hypothesis is not:

```text
F13 KAFAS → SAS → F13 actuators
```

but initially:

```text
F13 OEM systems
      ↓
semantic normalization
      ↓
SAS-compatible virtual context
      ↓
SAS shadow behavior
      ↓
compare with openpilot / human / F13 response
```

If later HIL evidence shows that some BMW semantics are truly compatible across generations, that compatibility must still be validated per signal and per actuator domain.

## Architecture

```text
                  VIRTUAL G-SERIES ENVIRONMENT

      ┌──────────────────────────────────────────────┐
      │                                              │
      │  emulated / replayed vehicle state           │
      │                                              │
      │  speed / wheel speed / yaw / steering        │
      │  brake / accelerator / gear                  │
      │  KAFAS-like perception state                 │
      │  ACC/radar-like object state                 │
      │  driver inputs / stalks                      │
      │  validity / health / wake/network state      │
      │                                              │
      └───────────────────┬──────────────────────────┘
                          │
                          ▼
                       SAS ECU
                          │
            CAN / FlexRay / Ethernet observation
                          │
                          ▼
                 SAS semantic output
                          │
              OFFLINE / SHADOW ONLY
                          │
                          ▼
                semantic normalization
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
         G-series model        F13 hypotheses
                                     │
                                     ▼
                           F13-specific validation
```

## Compatibility layers

### L0 — static teacher

Inputs:
- firmware / SWFL where legally available;
- coding metadata;
- diagnostic metadata;
- teardown / public technical documentation.

Outputs:
- candidate CAN/FlexRay/Ethernet maps;
- possible function groups;
- state-machine hypotheses.

No powered SAS required.

### L1 — powered SAS bench

Goal:
- establish stable ECU power-up;
- identify ECU;
- observe network participation;
- determine what missing dependencies prevent normal state.

Inputs are still passive or static.

### L2 — virtual vehicle context

Replay or emulate only the minimum benign state needed for the SAS to remain operational on an isolated bench.

Potential dependency classes:
- wake / ignition state;
- network-management state;
- vehicle speed / wheel speed;
- steering angle / yaw;
- gear / brake / accelerator state;
- KAFAS-like observations;
- ACC/radar-like observations;
- valid/invalid/fault state;
- gateway-visible topology.

The exact minimum set is unknown and must be discovered experimentally.

### L3 — SAS shadow behavior

Feed controlled synthetic scenarios and record what SAS outputs.

Examples:
- lane-following-like scenario;
- lead vehicle closing/opening;
- driver steering intervention;
- ACC enable/disable;
- indicator/lane-change intent;
- parking-state transitions.

Outputs remain read-only observations.

### L4 — cross-generation semantic comparison

Compare SAS output families with F-series raw candidates.

Example:

```text
G-series SAS
  request_valid-like
  lateral_request-like
  override-like
  fault-like

       ↓ semantic template

F13 raw candidates
  field A
  field B
  field C
  field D

       ↓

cross-generation hypothesis
```

This can increase confidence about *what kind of state* an F13 signal may represent.

It does not prove identical protocol.

## What “fooling the SAS” means in this project

It means reproducing enough expected **bench context** for the ECU to expose its normal state-machine behavior.

It does not mean:
- bypassing security controls;
- cloning vehicle identity for theft or unauthorized access;
- defeating anti-theft systems;
- defeating secure boot/HSM;
- injecting donor commands into a live F13;
- pretending an unvalidated F13 actuator is a G-series actuator.

The research target is functional context, not security circumvention.

## Expected obstacles

A SAS may refuse or degrade operation because of:

- missing FlexRay startup/synchronization;
- missing gateway/BDC state;
- missing KAFAS/radar data;
- wrong coding/variant configuration;
- inconsistent vehicle state;
- stale counters or validity flags;
- missing network management;
- missing Ethernet service discovery;
- missing partner ECUs;
- startup plausibility checks;
- diagnostic fault state.

These obstacles are useful evidence because they reveal the dependency graph.

## Dependency discovery method

For each missing dependency:

1. power SAS on isolated bench;
2. record faults and network output;
3. add one known dependency or replay one known state;
4. repeat;
5. measure which new states appear;
6. build a dependency graph.

Output example:

```text
SAS
├── requires wake/network state
├── requires steering/yaw state
├── requires KAFAS validity for lateral function
├── requires ACC/radar validity for longitudinal function
└── enters degraded mode when partner ECU absent
```

## Why this is more valuable than direct transplantation

If the SAS can be made operational in a virtual G-series environment, we get a BMW-authored reference for:

- request/state separation;
- update timing;
- validity semantics;
- driver override logic;
- fault behavior;
- cross-domain coordination.

Then the F13 adapter can be written against **BMW semantics**, not guessed byte patterns.

## Possible final architecture if the research succeeds

The strongest architectural role for SAS is as a central BMW-ADAS semantic coordinator and validator that can consume normalized states from the F13 OEM sensor ecosystem.

It should not replace KAFAS, FRR, SWW, PDC or ICM/DSC. Those remain the physical/OEM sources.

The most ambitious safe architecture would still keep the modern SAS outside direct F13 actuation:

```text
Comma/openpilot
      │
      ▼
BMWControlIntent
      │
      ├──────────────► F13-native validated controller path
      │
      └──────────────► SAS shadow comparison
                         │
                         ▼
                 disagreement / validation
```

A more experimental HIL-only architecture could compare:

```text
openpilot intent
vs
SAS modern-BMW intent
vs
human action
vs
F13 measured response
```

The SAS remains a teacher/validator until a separate safety case proves any deeper role.

## Current project boundary

Allowed:
- static firmware analysis;
- read-only diagnostics;
- isolated bench power-up;
- passive CAN/FlexRay/Ethernet capture;
- synthetic/replayed benign state;
- offline semantic comparison;
- HIL-only experiments after explicit review.

Not implemented:
- direct SAS-to-F13 forwarding;
- live F13 actuator commands;
- generic G-series-to-F-series command translation;
- vehicle security bypass;
- production control authority.
