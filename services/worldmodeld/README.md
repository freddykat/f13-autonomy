# worldmodeld — M0/M1 read-only world model

## Goal

`worldmodeld` builds a normalized environmental state for shadow development by combining ego state from `BMWVehicleState` with synthetic or decoded perception observations.

M0 is deliberately deterministic and simple. It is a software integration layer, not yet a learned perception network.

## Inputs

Initial inputs:

- `BMWVehicleState`
- synthetic radar tracks
- synthetic camera detections
- synthetic lane geometry
- optional map/route context

Later inputs may include:

- BMW ACC radar
- KAFAS observations
- custom camera perception
- Parking High / PDC near-field data
- GNSS/map context

## Output

`WorldState` as defined in `interfaces/world_state.md`.

## M0 fusion rules

Start with transparent rules:

1. Convert all observations to BMW ego coordinates.
2. Reject stale sources before fusion.
3. Associate observations by proximity/velocity consistency.
4. Preserve source provenance.
5. Increase confidence when independent sources agree.
6. Lower confidence and flag disagreement when sources conflict.
7. Never convert missing data into assumed free space.

## Example

```text
camera:
  vehicle x=71.9 m y=0.3 m confidence=0.82

BMW radar:
  object x=71.5 m y=0.2 m relativeSpeed=-6.7 m/s

worldmodeld:
  track #14
  x=71.6 m
  y=0.2 m
  relativeSpeed=-6.7 m/s
  sourceMask=[CAMERA, BMW_RADAR]
  confidence=HIGH
```

## Safety/architecture boundary

`worldmodeld` does not control the car. Its job is to describe the environment and uncertainty for planner/validation tools.

## M0 success criteria

- deterministic output for deterministic synthetic input
- correct source staleness handling
- object source provenance retained
- camera/radar disagreement visible
- lane and object data use one coordinate frame
- world state serializable/loggable
- no vehicle actuation dependency

## Next evolution

After M0:

1. feed recorded BMW radar/KAFAS data
2. add real camera-derived detections
3. add temporal tracking
4. add occupancy/free-space representation
5. integrate route and traffic-law context
6. expose stable inputs to the shadow planner and disagreement viewer
