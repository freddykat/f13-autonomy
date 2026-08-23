# Prototype 001 — MY2026 Complete Specification

## Vehicle identity

**Base vehicle:** BMW 650i M Sport F13

Prototype 001 is intentionally a 650i M Sport, not an M6. The aim is a civilised V8 GT daily driver with 2026-level technology, not an M6 replica.

## Product thesis

An EV can be cheaper and more efficient per kilometre. Prototype 001 is not trying to beat an EV at being an EV.

The proposition is that a driver should not have to abandon a well-designed interior, physical controls, GT comfort and a V8 in order to gain modern perception, connectivity, parking assistance, digital UX and supervised highway autonomy.

## Design rule

Every modification should answer one question:

> Would this feel plausible if BMW had continued developing the F13 into model year 2026?

That means integrated, serviceable and restrained rather than gadget-heavy.

---

## 1. Vehicle foundation

The autonomy stack depends on a mechanically healthy base vehicle.

Targets:

- N63 reliability refresh
- cooling system health
- oiling/PCV/sealing reliability work
- timing/valvetrain condition as required
- turbo/charge-air system health
- ignition/fuelling baseline
- transmission/xDrive baseline
- braking system baseline
- suspension/bush/geometry baseline
- battery/alternator/LV power health
- clean diagnostic baseline before autonomy work

The project should preserve daily-driver refinement and avoid turning the 650i into an unnecessarily harsh track car.

---

## 2. Exterior modernisation

Goal: subtly modern, recognisably F13.

Potential areas:

- updated headlight internals/light guides
- progressive indicators where legally compliant
- modern welcome/approach lighting
- camera integration that does not look aftermarket
- discreet side/rear perception cameras
- OEM-like antenna/GNSS packaging
- no unnecessary external screens or exposed sensors

---

## 3. Digital cabin

The original F13 interior architecture is part of the reason to keep the car.

Targets:

- modern infotainment and wireless phone integration
- retained useful physical controls/iDrive behaviour
- digital cluster/HUD modernisation
- autonomy state integrated into cluster/HUD
- navigation route shared with autonomy stack
- clear Partial Autopilot vs Highway Supervised state
- driver monitoring status
- camera/parking views
- vehicle health summary
- no tablet-wall aesthetic

Example autonomy HMI states:

```text
ASSIST READY
PARTIAL AUTOPILOT
HIGHWAY PILOT AVAILABLE
HIGHWAY SUPERVISED ACTIVE
TAKE OVER
SYSTEM UNAVAILABLE
```

---

## 4. Smart key and connected vehicle

Targets:

- secure phone-key research
- owner proximity/welcome functions
- remote status
- locate vehicle
- selected comfort actions
- temporary/revocable guest access concept
- security-event notifications
- explicit remote-parking authorization

The custom layer must not weaken the BMW immobiliser/start-security model.

See `SMART_KEY_AND_SUMMON.md`.

---

## 5. Sentry / black-box / security

The same perception hardware used for autonomy should support an integrated parked-security and evidence system.

Targets:

- rolling multi-camera black-box while driving
- parking-event recording
- impact/wake event preservation
- proximity-triggered recording where appropriate
- timestamped vehicle-state data
- secure local storage
- owner event notifications through the companion layer
- privacy-aware retention controls

Driving black-box and parked-security modes should share storage infrastructure but remain logically separated.

---

## 6. Parking and near-field perception

Targets:

- reuse BMW PDC/Parking High where practical
- modern 360-degree stitched or BEV parking view
- near-field free-space/obstacle model
- curb/wheel awareness if achievable
- automatic parking research
- supervised remote parking / Summon as a later staged feature

---

## 7. Exterior perception

Highway-first synchronized camera system.

Potential views:

- front tele
- front main
- front wide
- front-left
- front-right
- side-left
- side-right
- rear-left
- rear-right
- rear-centre as required

Priorities:

- HDR
- low latency
- synchronized timestamps
- appropriate FOVs
- robust low-light behaviour
- GMSL-class final transport

---

## 8. BMW sensor reuse

Where useful and trustworthy, reuse OEM data from:

- ACC radar
- KAFAS2
- PDC
- Parking High
- wheel speeds
- steering angle
- yaw / acceleration
- brake and accelerator state
- indicators
- gear
- ICM vehicle dynamics

All sources should feed one common ego/world coordinate model.

---

## 9. Main autonomy compute

Target architecture:

- cost-effective x86/ARM development computer first
- NVIDIA GPU with enough VRAM for current models
- NVMe logging/storage
- automotive DC/DC and ignition/wake strategy
- thermal management
- upgrade path to higher-end GPU only when workload requires it

The final system should not require comma hardware if custom hardware proves reliable.

---

## 10. openpilot architecture

Keep upstream openpilot as intact as practical.

Custom modules should sit beside it:

```text
our_camerad
teslaoracled
bmwstated
worldmodeld
metaplannerd
bmwcontrold
```

Preserve VisionIPC/cereal/messaging contracts where possible to reduce update pain.

---

## 11. Tesla HW4 teacher

HW4/FSD is a behavioural benchmark, not the BMW controller.

Use cases:

- compare decisions in identical scenarios
- disagreement mining
- validate lane-change/overtake/merge behaviour
- track benchmark evolution across FSD versions
- help improve our openpilot-based policy

The long-term BMW stack should not require HW4 in order to drive.

---

## 12. Operating modes

### Manual / OEM

Normal BMW operation remains available.

### Partial Autopilot

No route required. Initial functions:

- lane centering
- adaptive longitudinal assistance
- curve handling
- cut-in/collision awareness
- supervised lane-change assistance

### Highway Supervised

Requires valid route, supported ODD, healthy system state and explicit driver activation.

Targets:

- lane selection
- overtaking
- lane changes
- merges
- motorway exits
- route preparation

### Supervised Remote Parking

Separate low-speed mode with explicit remote authorization and hold-to-move behaviour.

---

## 13. Driver monitoring and interaction

Targets:

- attention/readiness monitoring
- clear escalation
- driver override always authoritative
- Action Questions only for genuine intent/preferences
- no asking the driver to make safety/perception decisions the system should make itself

---

## 14. BMW actuation architecture

High-level models should output abstract commands only:

```text
VehicleCommand {
  target_speed
  target_acceleration
  target_curvature
  curvature_rate
  lane_change_intent
}
```

BMW-specific translation belongs in `bmwcontrold` and below.

Research areas:

- EPS retrofit/integration
- ICM
- DSC
- DME
- ACC
- CAN/FlexRay

---

## 15. Independent safety boundary

A dedicated MCU/gateway must sit between autonomy compute and BMW actuation.

Responsibilities include:

- watchdog
- rate/limit enforcement
- plausibility checks
- driver override
- communication-loss handling
- fault handling
- low-speed Summon envelope enforcement
- hardware autonomy disable

The GPU/model must never directly drive actuators.

---

## 16. Logging and validation

Continuously record a synchronized rolling buffer of:

- all useful camera feeds
- radar
- CAN
- FlexRay
- GNSS/IMU
- BMW state
- openpilot output
- world-model output
- Tesla benchmark output when present
- driver input
- system confidence

Preserve event windows around:

- takeovers
- hard braking
- FCW
- disagreements
- cut-ins
- faults
- unexpected planner/intervention events

---

## 17. Development order

```text
M0 Shadow Lab
M1 Tesla Teacher
M2 BMW Shadow
M3 HIL
M4 Closed Course
M5 Partial Autopilot
M6 Highway Supervised
SK0-SK6 Smart Key / Remote Parking track
```

No stage should skip replay/HIL/controlled validation merely because generated code appears to work.

---

## 18. Prototype 001 definition of success

Prototype 001 should feel like a coherent 2026 BMW rather than a 2012 BMW with unrelated aftermarket gadgets.

The target experience is:

- original F13/V8 identity preserved
- daily-driver refinement preserved
- modern cabin and connectivity
- modern parking/security functionality
- modern perception
- progressively validated supervised highway autonomy
- OEM/manual fallback
- transparent safety boundaries

## One-line product statement

**A BMW 650i M Sport F13 re-engineered as a model-year-2026 V8 GT: original character, modern intelligence.**
