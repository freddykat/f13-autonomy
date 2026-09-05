# FRR Track Hypotheses

This stage combines passive BMW FRR discovery evidence into ranked **track hypotheses**. It is intentionally not a decoder, not a DBC generator, and not an openpilot `RadarData` producer.

A hypothesis may contain raw candidates for:

- range-like behavior;
- relative-velocity-like behavior;
- validity/state behavior;
- lateral-offset-like behavior;
- track/object-ID-like behavior.

The builder rewards stronger candidate scores and nearby topology, while keeping bus/address/byte/endian/signed identity explicit. Optional fields remain optional because real F13 captures are not yet available.

## Promotion boundary

Pre-vehicle results must remain `OFFLINE_READ_ONLY_DISCOVERY` with `auto_promote = false` and `actuation = NONE`.

A candidate set may only be promoted after repeated December vehicle captures corroborate event behavior, timing, scaling, validity semantics, object persistence, and cross-checks against independent observation where practical.

Only after that evidence should a separate adapter map validated BMW fields into openpilot radar concepts such as `dRel`, `yRel`, `vRel`, `trackId`, and `measured`.

No transmit path, diagnostic write, DBC mutation, CarController, Panda safety bypass, FlexRay TX, or vehicle actuation belongs in this stage.
