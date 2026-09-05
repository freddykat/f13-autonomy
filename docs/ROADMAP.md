# Roadmap

## M0 — Shadow Lab

No vehicle actuation.

Goals:

- record synchronized camera data
- record BMW CAN
- begin FlexRay capture
- prepare and verify the locked upstream openpilot 0.11.2 build
- run openpilot live/offline on comma hardware or a verified replay host
- simulate Tesla benchmark state
- visualize proposed decisions
- save disagreement events

Exit criteria: repeatable logging/replay and a working comparison pipeline.

## M1 — Sensor Shadow Beta

Run the locked openpilot build on the F13 with no vehicle output.

Goals:

- use comma road/wide/cabin cameras and driver monitoring
- receive BMW CAN through Panda/ZGM/OBD
- populate verified `CarState` fields
- populate front ACC `radarTracks` if the required objects reach the capture bus
- populate SWW left/right blind-spot state
- record KAFAS and extra 360-camera observations through sidecars
- preserve raw data, loss counters, timestamps and decoder provenance

Exit criteria: repeatable real-car shadow logging and replay with Panda `noOutput`, no BMW controller and no transmission path.

## Parallel track — Tesla verification

Collect genuine Tesla/openpilot shadow episodes where practical and qualify them with `validation/tesla_benchmark_gate.py`. Matched but non-simultaneous scenarios remain explicitly lower-confidence. Tesla verification is not required to start the BMW Sensor Shadow Beta.

## M2 — BMW Shadow

`bmwcontrold` computes but does not transmit actuation commands.

Goals:

- produce target curvature/speed/acceleration
- compare with human vehicle response
- validate driver override/state detection

Exit criteria: command proposals remain plausible across a representative dataset.

## M3 — Hardware in the Loop

Goals:

- connect safety MCU
- build BMW CAN/FlexRay bench
- test donor EPS/ICM/DSC modules where practical
- verify watchdogs, timeouts and command rejection

Exit criteria: safe deterministic behaviour under faults and replayed scenarios.

## M4 — Closed Course

First controlled physical actuation.

Start with tightly bounded low-risk functions and conservative limits.

## M5 — Partial Autopilot

Initial target:

- lane centering
- ACC
- cut-in/collision handling
- blind-spot support
- driver-confirmed lane changes

No navigation route required.

## M6 — Highway Supervised Autonomy

Within a validated highway ODD:

- route-aware lane management
- overtaking
- automatic lane changes
- merges
- exit preparation/management
- Action Questions for semantic/navigation ambiguity

## Continuous benchmark loop

```text
Tesla benchmark update
        ↓
repeat benchmark scenarios
        ↓
find disagreements/regressions
        ↓
label/review
        ↓
model/planner improvement
        ↓
replay + HIL validation
```

The target is not a one-time feature set; the benchmark should continue to move as reference systems improve.
