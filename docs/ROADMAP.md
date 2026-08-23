# Roadmap

## M0 — Shadow Lab

No vehicle actuation.

Goals:

- record synchronized camera data
- record BMW CAN
- begin FlexRay capture
- run openpilot live/offline on development compute
- simulate Tesla benchmark state
- visualize proposed decisions
- save disagreement events

Exit criteria: repeatable logging/replay and a working comparison pipeline.

## M1 — Tesla Teacher

Add genuine HW4/FSD read-only observation.

Goals:

- decode useful observable DAS/FSD state
- feed it into `teslaoracled`
- compare Tesla/openpilot/human behaviour
- identify OTA-version compatibility issues

Exit criteria: stable benchmark data during real-world manual driving or validated replay.

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
