# TrafficRuleContext

Read-only normalized legal/rule context for shadow planning.

## Purpose

`trafficlawd` converts authoritative traffic rules into structured context. It does not control the vehicle.

## Suggested fields

```text
TrafficRuleContext {
  jurisdiction
  roadType
  speedLimit
  keepRightRequired
  overtakingAllowed
  undertakingAllowed
  laneChangeAllowed
  minimumFollowingRule
  specialRestrictions[]
  sourceVersion
  validFrom
  confidence
  timestamp
}
```

## Rules

- Unknown legal state must remain UNKNOWN.
- Historical/outdated rules must be versioned and never mixed silently with current rules.
- Law/rules have precedence over behavioural imitation.
- The service should prefer official or authoritative sources over informal summaries.
- The planner must not infer legality purely from observed human/Tesla behaviour.
