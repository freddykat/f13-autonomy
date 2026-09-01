# BMW observation decoder manifest

`validation/manifests/prototype_001_bmw_decoders.json` is the declarative gate between canonical raw CAN frames and decoded BMW observations.

The committed manifest intentionally contains **zero signals**. No arbitration ID, bit position, scaling or unit has yet been confirmed strongly enough on Prototype 001 to enter it.

## Pipeline boundary

```text
candump / Vector ASC
        |
        v
canonical raw CAN frames
        |
        v
validated decoder manifest
        |
        v
decoded observation stream
        |
        v
observation episode importer
        |
        v
cross-source validation
        |
        v
BMWVehicleState candidate
```

Manifest validation does not decode a frame and does not promote a signal. It only proves that a proposed decoder entry is complete, internally consistent and explicitly scoped.

## Required identity and selector fields

Every future signal entry must declare:

- stable `decoder_id`
- semantic `signal` name
- intended `BMWVehicleState` `state_path`
- `transport`, logical `bus` and capture `channel`
- CAN arbitration ID, standard/extended form, DLC and receive direction
- zero-based start byte, bit within byte and absolute start bit
- bit length, explicit bit-numbering convention and byte order
- signedness, scale, offset, unit and any categorical choices
- physical validity range, stale timeout and invalid raw values when known
- evidence with a durable reference and independence group
- explicit vehicle-profile applicability
- decoder semantic version and validation status

The three start-location fields are intentionally redundant. The validator requires:

`absolute_start_bit = start_byte * 8 + start_bit_in_byte`

This catches a common class of DBC/bit-numbering transcription mistakes before a decoder can consume a capture.

## Initial scope

Schema version 1 accepts classic CAN only:

- transport must be `CAN`
- DLC must be 1 through 8
- direction must be `Rx`
- standard IDs must fit 11 bits; extended IDs must fit 29 bits
- bit layout must fit within the declared DLC

CAN FD, multiplexing, counters/checksums and FlexRay selectors need representative raw fixtures and a documented schema extension. They must not be smuggled in through extra fields: unknown fields are rejected.

## Vehicle applicability

The initial vehicle profile describes Prototype 001 as a 2012 BMW F13 650i xDrive with N63 non-TU.

Each signal must reference one or more declared profiles. ECU part numbers and software versions remain explicit lists, including when they are still empty. A decode observed on another F-series chassis or firmware is not silently assumed to apply to this car.

## Evidence and status ladder

Allowed statuses are:

1. `UNVERIFIED`
2. `FRAME_OBSERVED`
3. `SEMANTIC_CANDIDATE`
4. `CROSS_SOURCE_VALIDATED`
5. `STATE_SOURCE_CANDIDATE`
6. `REJECTED`

Every entry requires at least one evidence item. `CROSS_SOURCE_VALIDATED` and `STATE_SOURCE_CANDIDATE` additionally require:

- evidence from at least two independent source groups; and
- a referenced `cross_source_report`.

`STATE_SOURCE_CANDIDATE` also requires a known physical validity range and stale timeout. It means only that the signal is eligible for review by `bmwstated`; it does not automatically enter `BMWVehicleState`.

`REJECTED` entries may be retained as negative knowledge so a disproven mapping is not rediscovered later.

## Evidence kinds

The schema recognizes:

- official documentation
- recorded captures
- instrument-cluster observation
- read-only diagnostics
- independent sensors
- cross-source reports
- community references

References must point to durable material such as a versioned document, hashed capture or checked-in report. For capture evidence, `capture_id` and SHA-256 should be populated as soon as the raw corpus exists.

## Safety boundary

The loader reads JSON from disk and returns a validation report. It contains no CAN socket, diagnostic request, FlexRay TX, EPS, DSC, torque, brake or steering path.

Every report states:

`actuation_authority = NONE`

Observation confidence never becomes actuation authority.

## Usage

```bash
python -m validation.bmw_decoder_manifest \
  validation/manifests/prototype_001_bmw_decoders.json
```

The initial expected result is `signal_count = 0` and `state_source_candidate_count = 0`.
