# Tesla HW4 / FSD Benchmark

## Purpose

Tesla HW4/FSD is used as a read-only behavioural teacher and benchmark for the BMW F13 autonomy project.

The long-term BMW stack must remain independent from Tesla hardware.

## Non-goals

- No redistribution of Tesla proprietary firmware or model weights.
- No direct Tesla control of BMW EPS, DSC, DME or other actuators.
- No assumption that Tesla behaviour is always correct.

## Proposed observer service

`teslaoracled` should normalize externally observable FSD/DAS state into a stable project-facing interface.

Candidate state fields:

```text
TeslaHW4State {
  autopilot_state
  desired_speed
  longitudinal_request
  steering_request
  lane_change_state
  lane_change_direction
  blind_spot_left
  blind_spot_right
  fcw
  speed_limit
  navigation_state
  timestamp
}
```

Exact fields depend on what can be observed legitimately and reliably.

## Benchmark use

For each selected driving event, compare:

```text
Tesla FSD
openpilot
our policy
human driver
```

Disagreements become high-value replay, review and training cases.

## Bench research questions

1. What is the minimum viable HW4 environment for useful DAS/FSD behaviour?
2. Which genuine Tesla modules/states must remain present?
3. Which vehicle states can be replayed or emulated for legitimate bench research?
4. Which camera/calibration states are mandatory?
5. Which FSD/DAS outputs are externally observable?
6. What changes across OTA versions?
7. Can the observer interface remain stable despite message-layout changes?
8. Can a genuine entitled donor system remain useful outside the complete donor vehicle?

## Preferred development stages

```text
fake Tesla state
    ↓
recorded Tesla CAN/DAS data
    ↓
live HW4 observer
```

At every stage the output toward the BMW side remains read-only benchmark data.

## Community collaboration

We are looking for developers with practical HW4 bench, DAS/FSD CAN, gateway, camera calibration, replay and logging experience. The highest-value contribution is documentation of the minimum viable environment and observable control/planner state.
