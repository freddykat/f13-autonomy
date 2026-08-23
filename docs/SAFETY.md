# Safety Architecture

## Principle

Safety-critical vehicle control must not depend solely on the main Linux/GPU computer or on any single learned model.

## Layers

1. **Driver authority** — brake and steering override remain authoritative.
2. **Deterministic safety layer** — hard limits and plausibility checks independent from learned policy.
3. **Independent safety MCU** — watchdog, command gating and communication-fault handling.
4. **BMW OEM safeguards** — preserve EPS/DSC/ICM plausibility and stability logic wherever possible.
5. **Development process** — replay, simulation, HIL and controlled testing before actuation.

## Example fail conditions

- main compute crash or timeout
- malformed or stale command
- CAN/FlexRay communication fault
- EPS fault
- DSC intervention/fault
- sensor disagreement beyond threshold
- invalid calibration
- driver brake input
- strong driver steering override

## Degradation model

```text
Highway Supervised Autonomy
          ↓ fault / ODD exit
Partial Autopilot
          ↓ fault
OEM / Manual
```

Where safe degradation cannot be guaranteed, automation should disengage and request driver takeover rather than improvise.

## Read-only first

The first milestones are intentionally non-actuating:

- logging
- replay
- model comparison
- Tesla benchmark observation
- BMW shadow commands

Only after those layers are validated should HIL and closed-course actuation begin.

## Learned-model rule

No learned model gets direct low-level actuator access. All proposals must pass through vehicle abstraction and deterministic safety gating.
