# shadowplannerd

## Scope

`shadowplannerd` is the first explainable, deterministic planner for M0/M1 development.

It is **read-only** and has no actuation path.

It consumes:

- `WorldState`
- `BMWVehicleState`
- `BMWDynamicCapabilityState`
- `TrafficRuleContext`
- optional route context
- optional Tesla/openpilot policy proposals for comparison

It produces a `ShadowDecision` such as:

```text
KEEP
LEFT
RIGHT
WAIT
SLOW
STOP
```

plus reasons, constraints, confidence and rejected alternatives.

## Priority order

The initial planner follows a strict hierarchy:

```text
1. LEGALITY
2. PHYSICAL SAFETY
3. VEHICLE CAPABILITY
4. ROUTE INTENT
5. BEHAVIOURAL PREFERENCE
```

A lower layer cannot override a higher one.

Examples:

- A manoeuvre that appears comfortable but is illegal is rejected.
- A manoeuvre that is legal but has an unsafe rear-closing gap is rejected.
- A manoeuvre that is legal and geometrically safe but requires acceleration the BMW cannot deliver in time is rejected or delayed.
- Only after legality, safety and capability pass do route/preference rules choose among valid options.

## Explainability

Every output should include machine-readable and human-readable reasons.

Example:

```text
Decision: WAIT
Reason codes:
- LEFT_GAP_REAR_CLOSING_TOO_FAST
- CURRENT_LANE_LEAD_SLOWER
- OVERTAKE_LEGAL

Explanation:
"Overtake is legal, but the rear-left vehicle is closing too quickly. Wait for a safer gap."
```

Another example:

```text
Decision: KEEP
Reason codes:
- RIGHT_LANE_AVAILABLE
- KEEP_RIGHT_RULE
- NO_ROUTE_NEED_TO_STAY_LEFT
```

## Learning-mode role

During early development, shadow decisions are compared against:

```text
traffic rules
Tesla benchmark
openpilot proposal
human action
actual outcome
```

Disagreements are logged for review. The shadow planner does not automatically rewrite its own safety/legal rules based on observed behaviour.

## Initial motorway scenarios

- clear road -> KEEP / keep-right where applicable
- slower lead vehicle -> evaluate LEFT
- fast rear-left vehicle -> WAIT
- insufficient BMW acceleration margin -> WAIT/SLOW
- cut-in -> SLOW
- stopped obstacle -> SLOW/STOP depending on synthetic context
- route exit approaching -> evaluate RIGHT
- lane change legally prohibited -> KEEP
- unknown legal context -> conservative WAIT/KEEP depending on scenario
- stale perception -> conservative action / insufficient-confidence flag

## Gap evaluation

M0 should use transparent deterministic calculations such as:

- front gap
- rear gap
- relative speed
- time-to-collision / time-gap estimates
- predicted BMW response delay
- predicted acceleration capability
- lane occupancy/confidence

Thresholds are placeholders for simulation and must not be treated as validated road-driving limits.

## Capability-aware planning

`BMWDynamicCapabilityState` is used to answer whether a candidate manoeuvre is feasible within the simulated time/gap envelope.

For example, if a merge requires rapid acceleration but the current BMW mode/gear predicts a downshift delay, `shadowplannerd` may reject the gap even if a static geometry check would pass.

## Relationship to Tesla/openpilot

Tesla HW4/FSD and upstream openpilot are proposals/benchmarks, not authorities.

Example:

```text
Tesla: LEFT
openpilot: LEFT
shadowplannerd: WAIT
reason: rear-left closing too fast
```

This disagreement should be stored, not majority-voted away.

## Non-goals

M0 `shadowplannerd` does not:

- send steering commands
- send acceleration/braking commands
- command BMW drive modes
- select gears
- override DSC/ICM
- learn legal rules from human driving

## Next implementation step

Create serializable M0 `ShadowDecision` types and deterministic synthetic scenario tests. Then connect the output to the disagreement logger and human review UI.
