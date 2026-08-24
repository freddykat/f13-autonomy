# bmwstated

`bmwstated` is the read-only normalization and health service for BMW vehicle telemetry.

Its job is to convert validated BMW bus/diagnostic observations into the unified `BMWVehicleState` interface used by the rest of the autonomy stack.

## Responsibilities

- ingest passive CAN/FlexRay/LIN/diagnostic observations
- normalize units and naming
- timestamp every signal
- track freshness/staleness
- distinguish UNKNOWN from valid zero
- expose source and confidence
- maintain per-subsystem health
- publish `BMWVehicleState`
- preserve raw logs separately for replay/research

## Non-responsibilities

`bmwstated` must not:

- transmit steering/braking/powertrain requests
- write vehicle configuration
- alter DSC/ICM/EPS/IAS behaviour
- hide unknown signals behind guessed values

## Pipeline

```text
BMW buses / diagnostic observation
             |
             v
       passive decoders
             |
             v
     validation / freshness
             |
             v
         bmwstated
             |
             v
      BMWVehicleState
```

## Initial development order

### BS0 — synthetic state

Publish simulated `BMWVehicleState` objects from `fake_bmw`.

### BS1 — recorded replay

Feed recorded BMW bus data into offline decoders and compare with known driver actions/instrument-cluster behaviour.

### BS2 — live passive logging

Read vehicle buses without transmitting control traffic.

### BS3 — subsystem confidence

Add health/freshness metrics for chassis, powertrain, ADAS and parking signals.

### BS4 — autonomy consumers

Connect trusted normalized fields to `motionvalidatord`, `bmwdynamicsd`, `worldmodeld`, HMI and black-box logging.

## Signal acceptance rule

A field only becomes trusted when we can answer:

1. what physical quantity/state it represents;
2. its units/scaling;
3. its update rate;
4. its source ECU/bus;
5. its valid range;
6. its stale timeout;
7. how it behaves during faults/degraded modes.

Until then it stays experimental/raw.

## Example health behaviour

If rear-steer state stops updating while vehicle motion continues:

```text
rearSteerAngle = UNKNOWN
rearSteerFresh = false
iasHealthy = UNKNOWN/DEGRADED
```

not:

```text
rearSteerAngle = 0.0
```

Likewise an unavailable radar track list is different from a valid empty track list.

## Time synchronization

All inputs should be projected onto a common monotonic timeline. Camera, BMW bus, IMU, GNSS and Tesla benchmark logs must be correlatable after the drive.

## Consumer philosophy

Consumers should request the smallest relevant subsection rather than depending on the entire BMW bus universe.

For example:

- `motionvalidatord` consumes chassis/motion states;
- `bmwdynamicsd` consumes powertrain/dynamics states;
- `worldmodeld` consumes ADAS/parking observations;
- HMI consumes user-facing vehicle/mode/health states.

This keeps future BMW decoding changes isolated from higher-level autonomy logic.
