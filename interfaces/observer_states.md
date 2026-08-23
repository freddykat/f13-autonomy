# M0 Observer State Contracts

Status: draft, non-actuating interface for Shadow Lab.

This document defines the smallest useful normalized state contracts for comparing a manually driven BMW, openpilot, and an optional read-only Tesla teacher. These interfaces intentionally contain **no actuator command fields**.

## Design rules

1. Every sample uses monotonic timestamps in nanoseconds.
2. Unknown values remain explicitly unknown; they are never guessed from stale data.
3. Every decoded field carries source/validity information at the implementation layer.
4. Tesla data is observation only. Nothing in this interface writes to a Tesla or BMW bus.
5. BMW actuation interfaces belong in a later, separately reviewed safety boundary.

## `TeslaOracleState`

```text
TeslaOracleState {
  mono_time_ns: uint64
  source_hw: enum { UNKNOWN, HW3, HW4 }
  autopilot_state: enum { UNKNOWN, UNAVAILABLE, AVAILABLE, ACTIVE, ABORTING }
  lane_change_state: enum { UNKNOWN, NONE, REQUESTED, EXECUTING, ABORTING }
  lane_change_direction: enum { UNKNOWN, NONE, LEFT, RIGHT }
  blind_spot_left: tri_state
  blind_spot_right: tri_state
  forward_collision_warning: tri_state
  vision_speed_limit_mps: optional<float>
  desired_speed_mps: optional<float>
  hands_on_state: optional<int>
  nav_route_active: tri_state
  sample_age_ms: uint32
}
```

The first implementation should populate only fields supported by independently verified read-only captures. A field existing in a public DBC or third-party decoder is evidence to investigate, not proof that it is stable across HW4 trims/firmware.

## `BMWState`

```text
BMWState {
  mono_time_ns: uint64
  vehicle_speed_mps: optional<float>
  steering_angle_rad: optional<float>
  steering_rate_rad_s: optional<float>
  yaw_rate_rad_s: optional<float>
  longitudinal_accel_mps2: optional<float>
  lateral_accel_mps2: optional<float>
  brake_pressed: tri_state
  accelerator_percent: optional<float>
  left_indicator: tri_state
  right_indicator: tri_state
  gear: enum { UNKNOWN, P, R, N, D }
  acc_state: enum { UNKNOWN, OFF, STANDBY, ACTIVE }
  driver_steering_override: tri_state
  dsc_intervention: tri_state
  sample_age_ms: uint32
}
```

BMW signal mappings are deliberately absent until captured/verified against the target F13 or a well-documented F-series reference vehicle.

## `PolicyObservation`

A common representation for comparing systems without transmitting control:

```text
PolicyObservation {
  mono_time_ns: uint64
  source: enum { HUMAN, OPENPILOT, OUR_POLICY, TESLA_ORACLE }
  longitudinal_intent: enum { UNKNOWN, DECELERATE, HOLD, ACCELERATE }
  lateral_intent: enum { UNKNOWN, KEEP, LEFT, RIGHT }
  target_speed_mps: optional<float>
  target_curvature_1pm: optional<float>
  confidence: optional<float>  // 0..1, only if source provides a meaningful calibrated value
}
```

For the human source, intent should initially be derived only for offline review and labelled as derived data.

## `DisagreementEvent`

```text
DisagreementEvent {
  event_id: uuid
  mono_time_ns: uint64
  pre_roll_s: float
  post_roll_s: float
  reason: enum {
    LATERAL_DISAGREEMENT,
    LONGITUDINAL_DISAGREEMENT,
    HUMAN_OVERRIDE,
    FCW,
    SENSOR_INVALID,
    MANUAL_MARK
  }
  participants: list<PolicyObservation>
  bmw_state_ref: reference
  tesla_state_ref: optional<reference>
  media_refs: list<reference>
  review_status: enum { UNREVIEWED, REVIEWED, REJECTED_BAD_DATA }
}
```

## Freshness policy

Suggested starting point for Shadow Lab only:

- State consumers reject/mark stale samples rather than holding the last value silently.
- Raw bus/camera timestamps are preserved alongside normalized timestamps.
- Cross-source comparisons are made only inside a documented synchronization tolerance.
- No safety claim is inferred from these initial tolerances; they exist only for offline data quality.

## First implementation tasks

- Add serialization schema after choosing the project message framework.
- Implement `fake_tesla` and `fake_bmw` producers.
- Write schema round-trip and stale-data tests.
- Add a recorder that stores normalized states next to raw source data.
- Add a disagreement detector that operates only on recorded/shadow observations.

## Research notes (2026-08-23)

Recent public Tesla CAN projects indicate that useful **read-only** HW4 observations may be available on DAS status frames, including AP state, lane-change/blind-spot/FCW and vision speed-limit related state. Public projects also show firmware/vehicle-layout differences in DAS status framing, so the project must treat decoder mappings as versioned hypotheses and validate them against captures before relying on them.

Current openpilot development also has active work/issues around external/USB GPU execution. That supports keeping GPU/runtime assumptions outside these observer contracts so M0 logs remain portable across compute experiments.
