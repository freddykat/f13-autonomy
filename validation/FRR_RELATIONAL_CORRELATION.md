# FRR relational correlation

This validation step ranks raw BMW integer candidates across complementary lead-relative events. It is an offline discovery aid only.

## Intended marker set

- `LEAD_CLOSING`
- `LEAD_OPENING`
- `LEAD_STEADY`
- `LEAD_LOSS`

## What is rewarded

A distance-like candidate is stronger when the same raw field:

1. moves in opposite directions for closing versus opening;
2. changes much less during a steady-spacing episode;
3. shows a distinct transition around lead loss;
4. appears consistently on the same bus/address/byte interpretation.

No sign convention is assumed. A negative raw delta during closing does **not** establish that the field is physical distance, metres, centimetres, or any particular FRR signal.

`LEAD_LOSS` is intentionally treated only as evidence of a transition. The tool does not assume an invalid sentinel, stale value, zeroing policy, track deletion convention, or timeout behavior.

## December capture usage

For useful replay evidence, record several repetitions of each event with synchronized markers and preserve raw bus identity. Prefer varied distances and relative speeds, including a period where spacing is approximately constant. Cross-check strong candidates against read-only ENET/diagnostic observations and independent camera/GNSS timing where practical.

A candidate may only move toward a real decoder after capture provenance passes, sign/scaling are independently established, freshness/stale behavior is measured, replay regression exists, and a human reviews the promotion.

## Safety boundary

This module does not:

- transmit CAN or FlexRay frames;
- invoke `sendcan`;
- issue diagnostic writes or routine control;
- create DBC entries;
- mutate the BMW decoder manifest;
- infer actuation authority;
- create BMW `CarController` paths.

It exists to reduce passive FRR/ACC discovery time before any control work is considered.
