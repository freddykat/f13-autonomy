# Relational BMW Signal Correlation

This validation tool ranks raw continuous integer interpretations by how coherently the same candidate behaves across complementary event markers.

It is intended for December passive BMW captures and replay only.

## Safety boundary

The analyzer is strictly offline/read-only. It does not:

- transmit CAN or FlexRay frames;
- call Panda `sendcan`;
- issue diagnostic writes or routine control;
- generate or mutate a DBC;
- promote a decoder automatically;
- assign engineering units or actuator authority.

A high score is only discovery evidence.

## Why relational scoring

Single-event correlation can produce many false positives because unrelated bytes may move around the same time as an event. Relational scoring asks whether the **same raw interpretation** behaves consistently across complementary events.

For steering, a useful relation is:

```text
STEER_LEFT_SLOW  -> excursion in one direction
STEER_RIGHT_SLOW -> excursion in the opposite direction
STEER_CENTER     -> return near the midpoint/baseline
```

The implementation does not assume which raw sign means left or right. It chooses the better of the two opposite-sign assignments.

For lead range, a useful relation can be:

```text
LEAD_OPENING -> excursion one way
LEAD_CLOSING -> excursion the other way
```

A separate validity/state analyzer should handle `LEAD_LOSS`, because invalid/default/stale behavior is often categorical rather than a continuous baseline.

## Relation specification

```python
RelationSpec(
    name="steering_opposition",
    positive_event="STEER_LEFT_SLOW",
    negative_event="STEER_RIGHT_SLOW",
    baseline_event="STEER_CENTER",
)
```

The event names are labels only. The analyzer does not convert them into physical semantics.

## Candidate identity

Candidates remain separated by:

- bus;
- arbitration address;
- start byte;
- width (1/2/3 bytes);
- signed/unsigned interpretation;
- big/little endian interpretation.

This prevents the same numeric arbitration ID observed on two buses from being silently treated as one signal.

## Score components

`opposite_direction_score`
: repeated positive/negative events move in opposite raw directions.

`baseline_recovery_score`
: when a baseline event is supplied, its post-event raw value returns near the midpoint between the complementary event post-values.

`coverage_score`
: required events have repeated observations meeting the configured minimum.

Current combined score:

```text
0.60 * opposite_direction_score
+ 0.25 * baseline_recovery_score
+ 0.15 * coverage_score
```

The weights are heuristic discovery aids, not statistical confidence or safety certification.

## December steering protocol

Recommended controlled sequence:

```text
STEER_CENTER
STEER_LEFT_SLOW
STEER_CENTER
STEER_RIGHT_SLOW
STEER_CENTER
```

Repeat the sequence multiple times at standstill or another safe controlled condition when physically appropriate for the vehicle and capture setup.

A strong candidate should later also be checked for:

1. consistent opposite left/right behavior;
2. return toward center baseline;
3. monotonicity during slow steering motion;
4. plausible update rate and stale behavior;
5. independent corroboration from ICM/SZL/diagnostic observation where available;
6. repeatability in an independent capture;
7. replay regression before any decoder-manifest proposal.

## Promotion boundary

Even a score near 1.0 does **not** prove:

- that the signal is steering angle;
- which ECU sent it;
- degrees/radians or scale;
- offset;
- checksum/counter layout;
- exact transport topology;
- suitability for control.

Promotion into `prototype_001_bmw_decoders.json` still requires human review, provenance-quality capture, independent corroboration, measured timing/freshness, stale/UNKNOWN behavior, and replay regression.
