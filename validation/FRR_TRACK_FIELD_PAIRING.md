# FRR track-field pairing

This validation helper is for **offline, passive BMW FRR capture analysis only**.

It ranks pairs of raw integer interpretations that may behave like a range-like
field and a relative-velocity-like field for the same observed target. The goal
is to reduce manual search effort during F13 decoder discovery, not to assign
automotive semantics automatically.

## What it checks

For a candidate range field, the tool derives the raw time derivative between
consecutive samples. It then aligns those slopes with the nearest samples of a
candidate velocity field and scores:

- sign consistency between range slope and candidate velocity;
- absolute Pearson correlation between the two raw series;
- near-zero velocity behavior when the raw range is steady;
- sample count and a weak same-bus locality heuristic.

Unknown sign conventions are handled by accepting either direct or inverse
polarity and keeping the better relation.

## What it does not infer

A high score does **not** prove that either field is `dRel`, `vRel`, metres,
metres/second, a selected ACC lead, a full radar track, or even an FRR-owned
signal. It does not infer scale, offset, validity coding, track ID, age, lateral
position, checksum, counter layout, or message ownership.

## Safety boundary

The helper:

- transmits no CAN or FlexRay frames;
- performs no diagnostic writes;
- generates no DBC entries;
- promotes no decoder automatically;
- creates no openpilot `CarController`, `sendcan`, or actuation path;
- emits discovery candidates with `mode=OFFLINE_READ_ONLY_DISCOVERY`,
  `auto_promote=False`, and `actuation=NONE`.

Any field pair found in December captures must still be corroborated against
repeatable vehicle events and, where practical, an independent read-only source
before it is accepted into the BMW decoder manifest.
