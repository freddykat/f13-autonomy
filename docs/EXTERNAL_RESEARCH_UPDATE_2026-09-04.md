# External research update — 2026-09-04

This note records upstream developments that materially affect the next non-actuating milestones for `f13-autonomy`.

The purpose is not to import undocumented CAN/FlexRay actuation knowledge. It is to choose safer observation, replay, compute and collaboration paths.

## 1. openpilot / comma: Chestnut changes the custom-compute decision

On 2026-08-12 comma announced **Chestnut**, a comma four compute expansion that connects a desktop-class GPU and is intended to run larger openpilot models. The launch is important to Prototype 001 because it validates a design direction we were already pursuing: keep openpilot messaging/camera/model contracts close to upstream while allowing substantially more inference compute outside the base embedded device.

Current upstream `modeld` still consumes camera data through `VisionIpcClient` / `VisionStreamType`. That remains the preferred compatibility boundary for our camera work.

### Project consequence

Do not start by forking `modeld` into an F13-specific GPU stack.

Prefer this development order:

1. synthetic/replay VisionIPC producer;
2. synchronized custom-camera producer that preserves upstream VisionIPC semantics;
3. benchmark unmodified/current `modeld` against our replay corpus;
4. evaluate Chestnut-class/upstream external-GPU architecture against fully custom GPU hosting;
5. fork inference plumbing only when a measured incompatibility requires it.

### Evidence to preserve in benchmarks

For every model run record:

- exact openpilot commit;
- model artifact/version;
- camera stream type, dimensions and pixel format;
- frame ID and capture timestamp provenance;
- inference backend/device;
- inference latency and dropped-frame counters.

A faster GPU does not authorize vehicle control and does not repair bad camera timing.

References:
- https://blog.comma.ai/chestnut/
- https://github.com/commaai/openpilot
- current `openpilot/selfdrive/modeld/modeld.py` VisionIPC consumer path

## 2. BMW F-series: add ENET/HSFZ/UDS as a semantic cross-check path

`HadiCherkaoui/klartext` is a recent native-Rust BMW F-series diagnostic project using ENET, BMW HSFZ transport and UDS. Its read stack is reported as developed against F20 and wire-confirmed on F25. It deliberately ships no BMW proprietary datasets and includes a read-only MCP surface.

This is relevant to our existing cross-source validation rule: a diagnostic observation can corroborate **value semantics** without pretending that diagnostic response time equals the original ECU sample time.

### Project consequence

Add a read-only ENET adapter to the Beta-1 observation roadmap before attempting to make a candidate FlexRay recorder authoritative.

The adapter should export our existing observation envelope with at least:

- ECU/source identity;
- diagnostic service/job identity;
- requested measurement identity;
- decoded value and unit;
- request timestamp;
- response timestamp;
- explicit `timing_provenance = diagnostic_response_time` unless a stronger source timestamp is genuinely available;
- calibration/decoder version;
- validity/error result;
- `actuation_authority = NONE`.

Default policy must continue to exclude diagnostic response timing from tight yaw/speed/lateral-acceleration temporal agreement. It may still help validate scaling, units, enum meaning and slow-changing state.

No diagnostic write/routine-control/coding path is required for this milestone.

Reference:
- https://github.com/HadiCherkaoui/klartext

## 3. BMW F-series public topology knowledge remains useful but non-authoritative

Public BMW-F repositories continue to identify F-series ECUs such as ICM, DSC, EPS, KAFAS2, TRSVC and the central gateway/diagnostic path. These sources are useful for forming capture hypotheses, but many explicitly state that fields are deduced or incomplete.

Therefore:

- ECU presence/address tables may seed a discovery checklist;
- they must not directly create a `STATE_SOURCE_CANDIDATE` decoder mapping;
- no steering/torque/DSC request IDs are to be promoted from public tables alone;
- real Prototype-001 captures plus independent evidence remain mandatory.

References:
- https://github.com/packetpilot/bmw-f
- https://github.com/lattwood/bmw-f

## 4. Tesla HW4 research: useful observer clues, poor authority source

Recent public Tesla CAN projects claim HW4-specific monitoring of DAS-related messages and distinguish behaviour by firmware/FSD generation. These repositories can help identify where public researchers are observing configuration/state changes, but many are explicitly designed to modify vehicle CAN behaviour (FSD-enable flags, profile changes, nag suppression, config spoofing).

That is outside our current scope.

### Project consequence

For the Tesla teacher/benchmark work:

- use such projects only as a bibliography for **observable** message families and firmware-version questions;
- do not copy CAN modification/injection logic into `f13-autonomy`;
- require a genuine entitled Tesla/HW4 donor environment for behavioural benchmarking;
- keep `teslaoracled` read-only and version its evidence by Tesla firmware/FSD release;
- prefer video/UI/telemetry-observable outputs where CAN semantics cannot be independently verified.

References for research context only:
- https://github.com/1-v-1/tesla-open-can-mod
- https://github.com/manaux/HW4-checker

## 5. Collaboration status and useful targets

### Existing pico-flexray outreach

`dynm/pico-flexray` remains the strongest directly relevant public FlexRay collaboration target. We already opened issue #8 requesting receive-only per-frame timestamp, sequence and drop/error provenance, and separately contacted the F30 test-candidate thread. No upstream reply was present at the time of this review.

Avoid duplicate follow-up until there is a response or a concrete downstream artifact to offer.

### New high-value collaboration target: klartext

The useful overlap with `HadiCherkaoui/klartext` is narrow and legitimate:

- read-only F-series ENET/HSFZ measurement export;
- timestamp/provenance semantics;
- F10/F12/F13 compatibility observations;
- stable machine-readable output suitable for offline cross-source validation.

A future outreach should ask about read-only measurement/export compatibility, not BMW proprietary data and not write/coding functionality.

## Next safe implementation step

Implement a schema/adapter fixture for **read-only ENET diagnostic observations** and add tests proving that:

1. diagnostic response timestamps cannot satisfy tight temporal corroboration policies;
2. diagnostic values can still corroborate units/scaling/state semantics;
3. stale/failed diagnostics become UNKNOWN rather than zero;
4. the adapter exposes no write/routine-control/coding interface;
5. all outputs retain `actuation_authority = NONE`.

This gives Beta 1 a second BMW observation path without increasing vehicle-control authority.
