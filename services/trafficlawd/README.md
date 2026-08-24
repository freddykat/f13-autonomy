# trafficlawd

`trafficlawd` is the read-only legal/rule-context service for Prototype 001.

It combines versioned jurisdiction rules with observed dynamic traffic controls. It does not drive the vehicle and does not treat perception output as law unless the observation is sufficiently trusted and applicable.

## Inputs

- jurisdiction / country
- date/version of rule set
- road type
- lane context
- static map context where available
- recognized signs
- `TrafficControlState`
- optional route context

## Outputs

A normalized `TrafficRuleContext` for the shadow planner, including:

- current speed limit and source
- lane-change legality
- keep-right / lane-use obligations
- overtaking restrictions
- lane closure / lane availability
- traffic-light movement permission
- temporary restrictions
- confidence / uncertainty
- source provenance

## Rule precedence concept

The exact legal precedence is jurisdiction-specific and must be validated from official sources. Operationally, the service should distinguish at least:

```text
static/default rule
    ↓
fixed roadside sign
    ↓
temporary/dynamic control
    ↓
police/authorized traffic direction where represented
```

This ordering is a model to be verified per jurisdiction, not hard-coded globally without source validation.

## Countries targeted first

- Netherlands (NL)
- Germany (DE)
- Belgium (BE)
- Portugal (PT)

Each rule pack must be versioned and source-attributed so later legal changes do not silently alter historical replay.

## Dynamic motorway matrix signs

The service should understand lane-scoped matrix controls such as:

- variable speed limits
- red X / lane closed
- green arrow / lane open
- directional lane-change arrows
- warnings / congestion / roadworks indications

Lane association is mandatory. A sign above one lane should not automatically apply to all lanes.

## Traffic lights

Traffic-light recognition must include:

- RED
- AMBER
- GREEN
- RED_AMBER where applicable
- FLASHING_AMBER
- OFF
- UNKNOWN
- directional arrows

The planner must know which lane/movement a signal applies to. `UNKNOWN` must never be interpreted as permission to proceed.

## M0 behaviour

At M0 this service uses synthetic/versioned rule data and synthetic `TrafficControlState`. It should be deterministic and explainable.

Example:

```text
jurisdiction: NL
road_type: motorway
static_limit: 100 km/h
matrix_limit: 80 km/h
matrix_confidence: 0.98
current_rule_limit: 80 km/h
reason: TRUSTED_DYNAMIC_SPEED_CONTROL
```

Example lane closure:

```text
current_lane: 2
matrix: RED_X over lane 2
adjacent_lane_1: OPEN
adjacent_lane_3: OPEN

rule result:
- remain-in-lane: TEMPORARILY_INVALID / EXIT_LANE_REQUIRED
- move to an available lane when physically safe
```

## Learning-mode rule

Human, openpilot or HW4 behaviour cannot automatically overwrite a legal rule. Disagreement with a rule becomes a review event.

## Future source ingestion

Official traffic-code publications and transport-authority guidance should be converted into a structured, human-reviewed rule pack rather than blindly embedding PDFs into a model.
