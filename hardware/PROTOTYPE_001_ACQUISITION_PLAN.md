# Prototype 001 — Passive Acquisition Plan

Status: M1 preparation

This plan turns Prototype 001 into a synchronized measurement and shadow-learning vehicle before any autonomous actuation is considered.

## Objective

Record enough synchronized evidence to reconstruct what the BMW did, what the road environment contained, what the autonomy stack believed, and where those views disagreed.

## Initial channels

### BMW read-only state
- vehicle speed
- individual wheel speeds where available
- steering-wheel / road-wheel angle signals where decoded
- yaw rate and lateral/longitudinal acceleration
- brake state / brake pressure where safely observable
- accelerator position
- selected gear and engine speed
- DSC/ICM intervention state
- drive mode
- rear-steer / Integral Active Steering state where available
- ACC/KAFAS/PDC/parking-related state where present

All unknown signals remain explicitly UNKNOWN until verified from captures. No guessed DBC values are promoted to production interfaces.

### Independent motion reference
- timestamped GNSS
- IMU angular rates and acceleration
- monotonic host clock

### Vision
Phase A starts with synchronized forward vision. Surround cameras are added only after timing, storage and calibration are stable.

Required metadata per frame:
- camera ID
- exposure timestamp
- receive timestamp
- sequence number
- calibration version
- dropped-frame counter

### Perception-derived observations
- lanes / road edges
- tracked vehicles and vulnerable road users
- free-space / occupancy representation
- static and variable speed signs
- matrix signs and lane-control signals
- traffic lights where applicable
- confidence and provenance for every derived observation

## Time synchronization

Every source is converted to a common monotonic timeline. Original source timestamps are preserved.

Never silently interpolate across an excessive gap. Mark the interval stale/unknown instead.

## Storage unit

A drive is divided into bounded episodes. Each episode should contain:

```
manifest
raw BMW bus captures
GNSS/IMU stream
camera indexes/media references
normalized BMWVehicleState
WorldState snapshots
TrafficControlState
ODD/degradation state
shadow decisions
human actions
openpilot advisory output when available
external benchmark annotations when lawfully available
outcome / review labels
software + calibration hashes
```

## Privacy

Raw road video can contain faces, number plates, homes and location history. Raw recordings stay private by default. Public examples should be clipped/minimized and anonymized where appropriate.

## First acquisition milestones

P001-A: bench clocks and logger survive start/stop cycles.

P001-B: ignition-on static capture with no bus transmission from the autonomy computer.

P001-C: private-area passive rolling capture; compare BMW yaw/wheel speed with independent IMU/GNSS.

P001-D: decode and validate rear-steer awareness against observed vehicle motion.

P001-E: synchronized forward video + BMW state + GNSS/IMU replay.

P001-F: run perception and planner in shadow against recorded drives.

P001-G: disagreement mining and human review.

Only after these milestones feed the existing replay, promotion and HIL gates should any separate controlled-authority programme be considered.

## Definition of M1 success

M1 succeeds when a recorded drive can be replayed deterministically enough to answer:

1. What did the BMW actually do?
2. What did each sensor observe?
3. What did the world model believe?
4. Which traffic control/rule constrained the manoeuvre?
5. What did the shadow planner propose and why?
6. What did the human do?
7. Where did advisors disagree?
8. Did a new software build improve or regress the episode?
