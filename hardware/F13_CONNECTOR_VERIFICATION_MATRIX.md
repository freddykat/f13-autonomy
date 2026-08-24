# F13 Connector Verification Matrix

Status: M1 passive acquisition planning

This document records only connector/location facts that are supported by F12/F13 service information. Pin-level bus assignments remain UNKNOWN until verified against a wiring diagram for the exact vehicle configuration and confirmed on the car.

## Verification states

- `VERIFIED_DOC`: supported by F12/F13 service/connector documentation.
- `VERIFIED_CAR`: physically confirmed on Prototype 001.
- `PROBABLE`: consistent with platform documentation but not yet confirmed for the exact vehicle.
- `UNKNOWN`: do not wire to it yet.

## Modules relevant to the logger

| Function | BMW ID | Connector IDs seen in F13 service information | Location / role | State |
|---|---|---|---|---|
| Central Gateway Module | A51 / ZGM | A51*1B, A51*2B, A51*3B | Gateway between vehicle networks; F13 service information distinguishes variants with/without transfer box | VERIFIED_DOC |
| Dynamic Stability Control | A91 / DSC | A91*1B, A91*2B | Chassis stability domain | VERIFIED_DOC |
| Active Steering | A65 / AL | connector exists in F13 connector index; exact bus pins not yet transcribed | Front active-steering actuator controller | VERIFIED_DOC |
| Rear-Axle Slip-Angle Control | A77 / HSR | connector exists in F13 connector index; exact bus pins not yet transcribed | HSR controller; located in luggage-compartment well | VERIFIED_DOC |
| Integrated Chassis Management | A78 / ICM | A78*1B, A78*2B | Mounted near vehicle centre of gravity on transmission tunnel; high variant contains redundant yaw/lateral sensor system for IAS/ACC | VERIFIED_DOC |
| Camera-Based Driver Support Systems | A56 / KAFAS | A56*1B, A56*2B | ADAS camera control domain | VERIFIED_DOC |
| Transfer Box | A79 | platform connector entry present | Relevant to xDrive configuration and ZGM connector variant | VERIFIED_DOC |

## Network relationships currently verified

### ZGM

The ZGM is the central gateway between the main buses. F10/F12/F13 service/training material identifies PT-CAN, PT-CAN2, K-CAN2 and equipment-dependent FlexRay in the BN2020 network architecture.

For Prototype 001 this means an OBD capture through diagnostic routing must not be treated as equivalent to a direct physical capture on a chassis bus.

### ICM / IAS / HSR

The ICM is the higher-level chassis controller for Integral Active Steering. It calculates steering/yaw setpoints and provides resulting targets to Active Steering and HSR.

The HSR controller is located in the luggage-compartment well. F13 service information states that the HSR is connected on FlexRay via the Active Steering control unit.

The ICM high version includes redundant lateral-acceleration/yaw-rate sensing for vehicles requiring it, including Integral Active Steering.

### DSC

The DSC is part of the chassis network and is a key source/domain for wheel-speed/stability state. Its F13 connector entries include A91*1B and A91*2B.

## Current passive-tap priority

1. **OBD diagnostic baseline** — establish clocks/log format only.
2. **ZGM connector identification on the actual car** — photograph labels, connector keying and wire populations without depinning.
3. **ICM A78 identification** — physical confirmation on transmission tunnel.
4. **HSR A77 identification** — physical confirmation in luggage-compartment well.
5. **DSC A91 identification** — physical confirmation and harness routing.
6. Only then select a direct CAN/FlexRay tap location.

## Pin-level policy

No pin is added to a Y-harness drawing until all of the following are true:

1. exact model/configuration wiring diagram supports the assignment;
2. connector ID and pin number are visible in the source;
3. bus type and polarity/channel are explicit;
4. the connector is physically confirmed on Prototype 001;
5. electrical measurement is consistent with the expected network;
6. the tap can be made reversibly without changing network termination.

A forum post, retrofit photo, wire colour alone, or a diagram for another F-chassis is not sufficient to promote a pin to `VERIFIED_CAR`.

## FlexRay caution

Do not probe FlexRay as though it were ordinary CAN. Preserve topology, channel assignment and termination. The first FlexRay acquisition stage must use an interface suitable for passive FlexRay observation and a verified tap point.

## What we still need before a Y-harness

- exact F13 650i xDrive wiring pages for A51, A78, A77 and A91;
- connector pin tables for the specific build/equipment set;
- confirmation of which FlexRay channel reaches ICM/AL/HSR;
- confirmation of any direct PT-CAN/PT-CAN2 pair suitable for passive logging;
- BMW repair connector housings/contact part numbers for a non-destructive male/female pass-through harness;
- physical photos from Prototype 001.

Until those items are verified, the logger should start through OBD/diagnostic access and non-invasive measurement rather than a guessed inline harness.
