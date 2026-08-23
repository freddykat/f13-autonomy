# System Architecture

## Goal

Build an independent openpilot-based autonomy stack for a BMW F13, with Tesla HW4/FSD used only as a read-only behavioural teacher/benchmark.

## Core domains

1. **Perception domain** — synchronized cameras, BMW radar/KAFAS/PDC, GNSS/IMU, occupancy and tracking.
2. **Driving domain** — openpilot driving model, custom world model, route-aware behaviour and meta-planning.
3. **Benchmark domain** — Tesla HW4/FSD observer (`teslaoracled`) for behavioural comparison.
4. **Vehicle domain** — BMW state extraction and command abstraction over CAN/FlexRay.
5. **Safety domain** — independent MCU watchdog, plausibility checks, driver override and fail-safe behaviour.

## Intended data flow

```text
Custom Cameras ─┐
BMW Radar ──────┤
KAFAS/PDC ──────┤──> worldmodeld ──┐
GNSS/IMU ───────┘                  │
                                   ├──> metaplannerd ──> bmwcontrold ──> Safety MCU ──> BMW
openpilot modeld ──────────────────┤
                                   │
Tesla HW4/FSD ──> teslaoracled ───┘
```

## Software boundaries

- `our_camerad`: custom synchronized camera capture into VisionIPC-compatible interfaces.
- `bmwstated`: BMW vehicle state from CAN/FlexRay/OEM sensors.
- `worldmodeld`: fused ego-centric representation.
- `teslaoracled`: read-only Tesla HW4/FSD benchmark state.
- `metaplannerd`: combines openpilot, world-model safety, route intent and benchmark comparison.
- `bmwcontrold`: converts abstract vehicle commands into BMW-specific requests.

## VehicleCommand abstraction

```text
VehicleCommand {
  target_speed
  target_acceleration
  target_curvature
  curvature_rate
  lane_change_intent
}
```

The autonomy stack should not expose direct low-level motor/brake commands above `bmwcontrold`.

## Operating modes

### OEM / Manual

Normal BMW operation remains available if autonomy compute is unavailable.

### Partial Autopilot

No active navigation route required. Lane centering, ACC, following-distance control, cut-in/collision handling, blind-spot awareness and driver-confirmed lane changes.

### Highway Supervised Autonomy

Only when a valid route and supported ODD are available, and only after explicit driver activation. Route-aware lane management, overtaking, merge handling and exits are the initial target.

## Design rule

Tesla HW4/FSD is a benchmark input, never a direct actuator authority. Physics and deterministic safety constraints must be able to veto any learned-model proposal.
