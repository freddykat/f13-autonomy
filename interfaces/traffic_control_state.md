# TrafficControlState

`TrafficControlState` represents dynamic road-control information observed by the perception stack and supplied to `trafficlawd` / `shadowplannerd`.

This is read-only state. It does not control the vehicle.

## Goals

Support dynamic controls that can override or refine static map/legal context, including:

- traffic lights
- motorway matrix signs
- variable speed limits
- lane-control arrows
- red X / closed lane indications
- green arrows / open lane indications
- congestion/warning symbols
- temporary roadworks controls

## Proposed structure

```text
TrafficControlState {
  timestamp_ns
  source_health

  traffic_lights[] {
    id
    state        // RED, AMBER, GREEN, RED_AMBER, FLASHING_AMBER, OFF, UNKNOWN
    arrow        // NONE, LEFT, RIGHT, STRAIGHT, UTURN, MULTI, UNKNOWN
    applies_to_lane_ids[]
    distance_m
    confidence
    source
    stale
  }

  matrix_signs[] {
    id
    type         // SPEED_LIMIT, RED_X, GREEN_ARROW, LANE_ARROW_LEFT, LANE_ARROW_RIGHT,
                 // WARNING, END_RESTRICTION, OTHER, UNKNOWN
    value        // e.g. speed in km/h when relevant
    applies_to_lane_ids[]
    distance_m
    confidence
    source
    stale
  }
}
```

## Important semantics

- `UNKNOWN` is not equivalent to `GREEN`, `OPEN`, or `NO_RESTRICTION`.
- A stale matrix/traffic-light observation must not silently remain active forever.
- Lane applicability matters. A red X over lane 3 must not be interpreted as a road-wide closure unless confirmed.
- Conflicting observations from different cameras/sources must remain visible to the fusion layer.
- Dynamic controls should carry higher operational relevance than an older static-map assumption when sufficiently trusted.

## Recognition pipeline

```text
camera frames
   ↓
traffic-control detector
   ↓
classification + lane association
   ↓
tracking across frames
   ↓
TrafficControlState
   ↓
trafficlawd / worldmodeld / HMI
```

## Initial M0 synthetic scenarios

- red traffic light
- green traffic light
- amber transition
- left-turn arrow
- variable 80 km/h matrix sign
- red X over current lane
- green arrow over adjacent lane
- matrix sign stale/dropout
- conflicting speed-limit observations
- unknown/unclassified matrix symbol
