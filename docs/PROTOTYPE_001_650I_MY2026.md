# Prototype 001 — BMW 650i M Sport F13 MY2026

## The demonstrator

Prototype 001 is a **BMW 650i M Sport F13**, not an M6.

That distinction is intentional and will remain explicit throughout the project. We are not building an M6 replica or rebadging a 650i as an M6.

The objective is to answer a different question:

> **What would a V8 BMW F13 daily driver look and behave like if its technology had continued evolving through model year 2026?**

## Why the 650i M Sport?

For the autonomy, perception and digital-modernisation work, beginning with an M6 would not materially change the central engineering problem. Both cars belong to the F13 family and give us the grand-touring packaging and architecture around which the project is being developed.

There are real mechanical differences between a 650i and an M6 — engine, drivetrain, chassis tuning, brakes, cooling and M-specific hardware among them — and the project will not pretend otherwise.

But Prototype 001 is intended primarily as a **fast, comfortable, civilised daily-driver GT** rather than a track-focused M car. In that role the 650i M Sport is not a compromise in the project philosophy; it is arguably the more appropriate starting point.

## The thesis

Modern EVs can have a genuine operating-cost and energy-efficiency advantage per kilometre. This project does not attempt to make a V8 beat an EV at being an EV.

Instead, it asks why choosing a V8 grand tourer should also require accepting decade-old perception, infotainment, parking technology, connectivity and driver assistance.

We want to preserve the qualities that still make the F13 desirable:

- V8 character
- long-distance GT capability
- a well-designed driver-oriented interior
- physical controls where they make sense
- BMW seating and ergonomics
- mature ride and refinement
- the emotional/mechanical character of an ICE performance coupe

while modernising the technological layer around them.

## MY2026 target

Prototype 001 is intended to combine the original F13 character with a coherent 2026 technology package:

```text
BMW 650i M Sport F13
        |
        +-- V8 / GT character
        +-- OEM-quality cabin and controls
        +-- reliability and drivetrain refresh
        +-- modern infotainment / connectivity
        +-- modern digital cluster / HUD integration
        +-- modern lighting and vehicle UX
        +-- 360-degree camera perception
        +-- upgraded parking / proximity awareness
        +-- BMW radar + KAFAS sensor reuse where useful
        +-- driver monitoring
        +-- black-box / dashcam / sentry functions
        +-- F13 Autonomy
              +-- Partial Autopilot
              +-- Highway Supervised Autonomy
```

## Autonomy positioning

The public target for Prototype 001 is **supervised autonomy**, initially motorway/highway focused.

The project may use contemporary Tesla HW4/FSD behaviour as an evolving quality benchmark, but Tesla HW4 is a teacher/reference rather than the final vehicle controller.

The production target remains an independent openpilot-based stack using our own compute, perception, BMW integration and safety boundary.

We should not describe Prototype 001 as unsupervised autonomous or imply capabilities that have not been validated.

## OEM-like integration

A key requirement is that Prototype 001 should not look like a university prototype or a PC bolted into a car.

The intended experience is closer to:

> **an F13 BMW might have shipped this way if BMW had continued developing the platform into 2026.**

That means:

- compute hidden from occupants
- automotive camera housings integrated into trim/bodywork
- no unnecessary tablets attached around the cabin
- autonomy state integrated into the vehicle HMI
- retained physical controls
- factory-like wiring, connectors and serviceability where practical
- graceful fallback to OEM/manual operation

## Driver experience

### Manual / OEM

The car remains a normal BMW GT and should not depend on the autonomy computer for basic manual operation.

### Partial Autopilot

Available without route guidance. Intended capabilities include lane centering, adaptive longitudinal assistance, collision/cut-in awareness and supervised/confirmed lane-change assistance.

### Highway Supervised

With a valid route, supported road and healthy system state, the car may offer route-aware motorway assistance including lane selection, overtaking, merging and exits within the validated ODD.

The transition should be explicit to the driver rather than silently activating because GPS exists.

## The EV comparison

The message is not anti-EV.

EV advantages such as efficiency and lower energy cost per kilometre can be acknowledged directly.

Prototype 001 demonstrates a different proposition:

> **Electrification and modern vehicle intelligence are separate choices.**

A driver may prefer an EV. Another may prefer a V8 GT. Advanced perception, software, connectivity and supervised driving assistance should not conceptually require abandoning the latter.

## What makes Prototype 001 different from an M6 project?

An M6 donor would change the performance hardware and vehicle character substantially, but it would not eliminate the core work required for:

- synchronized perception cameras
- GPU/openpilot compute
- world modelling
- radar fusion
- driver monitoring
- CAN/FlexRay research
- EPS/ICM/DSC integration
- safety MCU design
- autonomy HMI
- HW4 teacher/benchmark research

For Prototype 001, the more civilised 650i M Sport character is deliberately retained.

A future M6 demonstrator could reuse much of the autonomy platform while pursuing a more extreme performance brief.

## Prototype 001 workstreams

### Vehicle foundation

Reliability, cooling, engine/drivetrain health, braking, suspension and electrical baseline must be established before autonomy actuation testing.

### Digital cabin

Modern infotainment/connectivity, cluster/HUD integration, navigation/autonomy state and coherent OEM-style user interaction.

### Perception

Synchronized exterior cameras, BMW radar/KAFAS/PDC reuse where useful, GNSS/IMU, driver monitoring and a unified world representation.

### Vehicle integration

BMW CAN/FlexRay state acquisition, EPS strategy, ICM/DSC integration research and an independent safety boundary.

### Autonomy

openpilot-based models, custom perception/world model, shadow testing, Tesla HW4 behavioural benchmark, disagreement mining, HIL and progressively validated supervised functions.

### Logging and validation

Synchronized black-box recording, replay, disagreement review, regression scenarios and intervention tracking.

## Success criteria

Prototype 001 succeeds if it can demonstrate that an F13 can retain its original V8 GT identity while feeling technologically contemporary rather than merely having aftermarket gadgets attached to it.

The technology should feel integrated, understandable and subordinate to the vehicle — not the other way around.

## One-line description

**Prototype 001 is a BMW 650i M Sport F13 re-imagined as a 2026 V8 daily-driver GT, combining the original car's character and cabin with modern perception, connectivity and progressively validated supervised highway autonomy.**
