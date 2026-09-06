# BMW F-Series Expansion — 2026-Era ADAS Modernization

Status: planning document.

## Product / experience target

The long-term target for the BMW F13 prototype is a **supervised driver-assistance experience broadly comparable in ambition to an early Tesla FSD Beta v8/v9-era feature envelope**, not a claim of Tesla-equivalent validation or current Tesla FSD capability.

Target behaviors include, progressively:

- stable lane centering;
- adaptive longitudinal control;
- stop/resume;
- cut-in handling;
- supervised lane changes;
- motorway merges and exits;
- route-aware lane selection;
- blind-spot awareness;
- traffic-control understanding where validated;
- parking assistance later.

The defining constraint is that the BMW should retain OEM/manual operation and the retrofit should remain modular and reversible where practical.

## Why F-series is a useful platform family

BMW F-series vehicles share many architectural ideas relevant to this project:

- ICM-based chassis coordination;
- distributed CAN / PT-CAN / K-CAN networks;
- substantial FlexRay use on many chassis domains;
- KAFAS and ACC radar variants;
- DSC/ICM integration;
- several models with factory EPS;
- several premium variants with rear steering / Integral Active Steering.

This means the F13 is not necessarily a one-off project. A validated read-only BMW compatibility layer may be reusable across a wider F-series family, with different actuator difficulty by model and drivetrain.

## Candidate families

### Tier A — strongest future candidates

These are likely to be the most attractive first expansion targets because many variants use factory EPS and have later-generation F-series electronics.

#### F20 / F21 — 1 Series

Potential advantages:

- compact platform;
- factory EPS architecture on many variants;
- FlexRay/ICM generation close to F30-family systems;
- lower vehicle cost makes community testing more accessible.

Validation still required per engine, drivetrain, build date and ADAS package.

#### F22 / F23 — 2 Series

Potential advantages:

- closely related to F20/F30-era electronics;
- enthusiast owner base;
- factory EPS on many variants;
- attractive modernization target for M235i/M240i and similar cars.

#### F30 / F31 / F34 — 3 Series

High-priority expansion family.

BMW technical training explicitly lists EPS, ICM, DSC, KAFAS, PMA and FlexRay in the platform architecture.

Potentially useful variants:

- 320i / 328i / 330i
- 335i / 340i
- 330d / 335d
- M3 F80 as a later variant-specific target

#### F32 / F33 / F36 — 4 Series

Strong candidate due to architecture overlap with F30 and the premium/enthusiast owner segment.

Potential targets:

- 428i / 430i
- 435i / 440i
- M4 F82/F83 later, after standard variants

### Tier B — premium platform candidates

#### F10 / F11 — 5 Series

Very relevant because of architectural similarity to F12/F13.

BMW technical training states:

- rear-wheel-drive F10 models use EPS;
- xDrive F10 models retain hydraulic steering;
- the same hydraulic-steering caveat applies to contemporary F12/F13 xDrive models.

This makes **RWD F10/F11 a potentially easier actuation research platform than the xDrive F13 prototype**, while still sharing much of the ICM/FlexRay/ACC/KAFAS ecosystem.

Potential target variants:

- 528i / 530i
- 535i / 540i
- 530d / 535d
- 550i RWD
- M5 F10 later, with variant-specific validation

#### F06 / F12 / F13 — 6 Series

Core project family.

Potentially easier variants:

- rear-wheel-drive cars with factory EPS or electromechanical steering depending build/market;
- cars already equipped with ACC, KAFAS, Parking High and richer ADAS options.

Harder variants:

- xDrive F12/F13 with hydraulic steering, including Prototype 001.

The F06 Gran Coupé should be treated as a close sibling but still requires its own vehicle/ECU provenance.

#### F01 / F02 — 7 Series

Premium owner segment and rich chassis/ADAS architecture.

BMW technical training for F01/F02 LCI documents variants using EPS or hydraulic steering and Integral Active Steering.

This family is technically attractive but should be treated as a second-wave target because:

- steering variants differ materially;
- 24 V electromechanical active-steering configurations exist;
- rear-steer integration is more complex;
- early/LCI electronics differ.

### Tier C — SUVs / xDrive-heavy variants

#### F25 — X3
#### F26 — X4

Potentially valuable due to owner base and BMW electronics generation, but every drivetrain/steering architecture needs variant-specific confirmation.

The software observation layer may transfer earlier than the control layer.

#### F15 / F16 — X5 / X6

Potential long-term targets.

These cars are highly relevant commercially because they remain desirable premium vehicles, but their chassis/ADAS complexity and xDrive-heavy configurations make them poor first actuation targets.

## Key distinction: observation portability vs actuation portability

We should expect the read-only layer to generalize much faster than steering/braking control.

Example:

```text
BMW transport model
BMW signal discovery
BMWVehicleState
FRR/SWW evidence
KAFAS observations
request↔feedback topology
```

may transfer across several F-series platforms.

But:

```text
steering actuator
longitudinal actuator
gear control
parking control
```

must remain platform/variant-specific until proven.

## Initial expansion order

Recommended after the F13 read-only port becomes stable:

1. F10/F11 RWD
2. F30/F31
3. F32/F36
4. F20/F22
5. F06/F12/F13 sibling variants
6. F01/F02 LCI
7. F25/F26
8. F15/F16

This order optimizes for architectural reuse and factory EPS availability rather than market size alone.

## Market / owner rationale

The opportunity is not limited to owners of one 650i.

There is a wider group of F-series owners maintaining:

- 5 Series;
- 6 Series;
- 7 Series;
- 3/4 Series performance variants;
- X3/X4/X5/X6;
- M cars.

Many of these vehicles remain mechanically and dynamically desirable while their ADAS/software stack is a decade behind current vehicles.

The modernization proposition is:

> keep the BMW you value, preserve OEM/manual driving, and add carefully validated modern supervised driver-assistance technology where the platform allows it.

This is not a promise that all F-series cars will receive the same capabilities.

Each platform needs:

- ECU inventory;
- steering architecture classification;
- CAN/FlexRay transport evidence;
- ACC/radar/KAFAS availability;
- driver-override validation;
- replay/HIL/closed-course gates.

## F-series compatibility database

Future manifest structure should track:

- chassis code;
- build date;
- drivetrain;
- RWD/xDrive;
- steering type;
- EPS/active steering/IAS;
- ICM generation;
- DSC generation;
- KAFAS generation;
- FRR radar type;
- SWW/HC2 type;
- Parking/PMA variant;
- gateway/ZGW generation;
- observed CAN paths;
- observed FlexRay paths;
- validated CarState fields;
- validated RadarData fields;
- control stage.

The software should never infer compatibility solely from a chassis code.
