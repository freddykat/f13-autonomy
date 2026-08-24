# WorldState Interface

## Purpose

`WorldState` is the normalized read-only representation of the environment around Prototype 001 for M0/M1 development.

It intentionally sits above individual sensors. Raw camera/radar/PDC/KAFAS data is decoded and validated first; `WorldState` contains fused/normalized observations with timestamps, confidence and source provenance.

## Initial structure

```text
WorldState {
  timestamp
  valid
  stale

  ego {
    speed
    yawRate
    longitudinalAccel
    lateralAccel
    heading
    curvature
    position
    sourceHealth
  }

  lanes[] {
    id
    side
    centerOffset
    heading
    curvature
    width
    confidence
    sourceMask
  }

  objects[] {
    id
    class
    x
    y
    vx
    vy
    relativeSpeed
    heading
    length
    width
    confidence
    sourceMask
    trackAge
    stale
  }

  freeSpace {
    representation
    confidence
  }

  occupancy {
    representation
    confidence
  }

  road {
    roadType
    speedLimit
    laneCount
    egoLaneId
    routeLanePreference
  }

  hazards[]
  sourceHealth
}
```

## Coordinate frame

Use the BMW ego frame consistently:

- +X forward
- +Y left
- +Z up

Every object/lane/free-space input must be transformed into this frame before fusion.

## Source provenance

Each fused entity should retain which source families contributed, for example:

```text
CAMERA
BMW_RADAR
KAFAS
PDC
PARKING_HIGH
MAP
GNSS
SYNTHETIC
```

This lets downstream modules distinguish a strong multi-sensor track from a single weak observation.

## Unknown and stale semantics

Missing data must remain UNKNOWN/stale. Do not silently invent lane lines, object speed or free space.

A low-confidence world model is still useful if downstream consumers can see that confidence and react conservatively.

## M0 scope

M0 starts with synthetic objects and simple lane geometry only. No real camera inference is required to validate the interface and downstream logic.

Initial scenarios:

- clear straight motorway
- slower lead vehicle
- fast rear-left vehicle
- safe left gap
- unsafe left gap
- cut-in
- stopped obstacle
- temporary loss of radar
- temporary loss of camera perception
- conflicting camera/radar object range

## Consumers

Expected consumers include:

- shadow planner
- disagreement viewer
- `trafficlawd`
- `motionvalidatord`
- HMI/debug visualizer
- black-box logger

## Boundary

`WorldState` is descriptive, not an actuator command interface.
