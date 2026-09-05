# Continuous BMW signal correlation

This workflow extends the offline discovery tooling to raw continuous numeric candidates such as steering angle, yaw rate, wheel speed, lead range and relative velocity.

It is **read-only discovery tooling**. It does not connect to vehicle transmit paths, generate DBC entries, assign engineering units, infer final scale, or promote decoders.

## Interpretations tested

For every eligible byte window the analyzer may test:

- unsigned 8-bit
- signed 8-bit
- unsigned/signed 16-bit big-endian
- unsigned/signed 16-bit little-endian
- unsigned/signed 24-bit big-endian
- unsigned/signed 24-bit little-endian

The same arbitration/frame identifier remains separated by bus.

## Event-direction hints

A capture campaign may supply a direction hint such as:

- `STEER_LEFT_SLOW: +1`
- `STEER_RIGHT_SLOW: -1`
- `LEAD_CLOSING: -1` for a candidate interpreted as longitudinal range
- `LEAD_OPENING: +1`

These are experiment expectations, not decoder semantics. A candidate receives a penalty when repeated deltas contradict the expected direction.

## Ranking inputs

The score combines:

1. repeated sign consistency across equivalent marked events;
2. match to an optional expected direction;
3. a small normalized raw-magnitude contribution;
4. minimum repeated observations.

The magnitude contribution is normalized only against the raw integer representable span. This deliberately avoids pretending to know physical scaling.

## December use

For a controlled steering episode:

```text
STEER_CENTER
STEER_LEFT_SLOW
STEER_CENTER
STEER_RIGHT_SLOW
STEER_CENTER
```

candidate windows can be ranked independently for left and right events. A strong hypothesis should later satisfy additional checks:

- opposite direction between left/right events;
- return toward baseline at center;
- independent SZL/ICM/IMU corroboration where available;
- measured update rate and stale behavior;
- replay regression before decoder promotion.

The same pattern applies to FRR lead distance and relative velocity using repeated `LEAD_CLOSING` / `LEAD_OPENING` episodes.

## Safety boundary

This analyzer contains no SocketCAN transmit path, Panda transmit path, diagnostic write, routine control, `sendcan`, FlexRay TX or actuator authority. Its output is discovery evidence for human review only.
