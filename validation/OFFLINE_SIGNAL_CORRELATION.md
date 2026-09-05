# Offline BMW signal correlation

This workflow is a discovery aid for Prototype 001 captures. It is read-only and cannot promote decoders or produce vehicle commands.

## Inputs

Trace JSONL:

```json
{"t": 12.345, "bus": "can0", "address": 291, "data": "0011223344556677"}
```

Event markers JSON:

```json
[
  {"t": 10.0, "event": "BLIND_LEFT_ENTER"},
  {"t": 20.0, "event": "BLIND_LEFT_ENTER"}
]
```

Use the event names defined in `docs/BMW_MESSAGE_SEMANTIC_MAP.md` where possible.

## Operation

`tools/bmw_signal_correlation.py` compares raw byte and bit state immediately before and after repeated event markers. It ranks features by repeated normalized state separation.

Example:

```bash
python tools/bmw_signal_correlation.py trace.jsonl markers.json --before 1.0 --after 1.0 --min-observations 2 --top 50
```

The output always declares:

```json
{
  "mode": "OFFLINE_READ_ONLY_DISCOVERY",
  "auto_promote": false,
  "actuation_authority": "NONE"
}
```

A high score means only that a raw feature repeatedly changed near a marker. It does **not** establish semantic identity, sender ECU, unit, scaling, checksum, counter, timing authority, or safety suitability.

## December workflow

1. pass capture-quality/provenance gates;
2. add synchronized event markers;
3. run the correlation analyzer;
4. inspect high-ranked raw bit/byte candidates;
5. repeat the event in an independent capture;
6. cross-check against ENET/UDS or an independent sensor where practical;
7. determine bus, sender, timing, counter/checksum and stale semantics;
8. add a replay regression;
9. only then propose promotion into `prototype_001_bmw_decoders.json` for human review.

## Safety boundary

This tool intentionally has no SocketCAN/Panda transmit path, no `sendcan`, no diagnostic write/routine control, no DBC generation, and no automatic decoder-manifest mutation.
