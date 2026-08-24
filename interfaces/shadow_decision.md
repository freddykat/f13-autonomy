# ShadowDecision

`ShadowDecision` is the deterministic, read-only output of `shadowplannerd` during M0 learning.

It is a proposal for comparison and logging only. It has no vehicle-actuation authority.

## Actions

- `KEEP`
- `LEFT`
- `RIGHT`
- `WAIT`
- `SLOW`
- `STOP`

## Schema

```text
ShadowDecision {
  monotonicTime
  action
  targetLane
  targetSpeed
  confidence

  primaryReason
  reasonCodes[]
  rejectedAlternatives[] {
    action
    gate
    reasonCode
  }

  gates {
    legality
    physicalSafety
    bmwCapability
    routeIntent
    behaviouralPreference
  }

  evidence {
    worldStateTime
    bmwVehicleStateTime
    dynamicCapabilityTime
    trafficRuleContextTime
    routeContextTime
  }

  comparison {
    openpilotProposal
    teslaBenchmarkProposal
    humanAction
  }
}
```

## Gate semantics

Each gate is one of:

- `PASS`
- `FAIL`
- `UNKNOWN`
- `NOT_APPLICABLE`

A downstream preference must never override an upstream `FAIL`.

`UNKNOWN` in legality, physical safety or required vehicle capability is conservative and must prevent an optional manoeuvre.

## Example

```text
action: WAIT
primaryReason: REAR_LEFT_CLOSING_FAST

LEFT rejected:
  legality: PASS
  physicalSafety: FAIL
  bmwCapability: PASS

KEEP:
  legality: PASS
  physicalSafety: PASS
```

## Learning comparison

The comparison block records what other actors proposed or did, but it does not vote on the final legal/safety gate.

A useful disagreement event is therefore possible even when all external actors agree:

```text
Tesla: LEFT
openpilot: LEFT
human: LEFT
shadow: WAIT
reason: LEFT_PROHIBITED_BY_RULE_CONTEXT
```

Observed frequency does not rewrite a legal rule.

## Required reason-code families

- `LEGAL_*`
- `GAP_*`
- `TTC_*`
- `OBJECT_*`
- `PERCEPTION_*`
- `BMW_CAPABILITY_*`
- `BMW_HEALTH_*`
- `ROUTE_*`
- `COMFORT_*`
- `UNKNOWN_*`

Reason codes must be stable enough for regression tests and dataset mining.

## Safety invariant

`ShadowDecision` is data. No consumer in M0 may translate it into steering, throttle or brake commands.
