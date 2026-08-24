# BMW F12/F13 Bus Access Map — M1 passive acquisition

Status: architecture/research. Pin numbers and wire colours are deliberately NOT asserted until verified against the exact vehicle wiring diagrams and measured on the car.

## Confirmed architecture-level topology

BMW's F12/F13 bus overview shows the ZGM as central gateway between K-CAN/K-CAN2, PT-CAN/PT-CAN2, FlexRay, D-CAN diagnostic access, Ethernet programming access and MOST. The F12/F13 overview places chassis/driver-assistance modules including DSC, EPS, ICM, KAFAS, HSR, VDM/EDC and related systems across these networks.

Conceptual map:

```
                       diagnostic/programming access
                              OBD / D-CAN
                                  |
                                [ZGM]
              ____________________|____________________
             /          /          |         \         \
          K-CAN      K-CAN2     PT-CAN    PT-CAN2   FlexRay
           body       body/fast   powertrain/chassis   chassis
                                                   |
                                      DSC / EPS / ICM / etc.

                     MOST / Ethernet also terminate through
                     the vehicle gateway architecture
```

Do not infer that every desired message is exposed raw at the OBD connector. Gatewayed diagnostic access and direct physical bus observation are different things.

## M1 access strategy

### Stage A — OBD diagnostic-side observation
Purpose: identify vehicle, validate logger power/timing, collect diagnostic information and establish a baseline without opening harnesses.

Rules:
- no periodic diagnostic polling during timing-sensitive baseline captures unless explicitly being tested;
- no coding/programming during acquisition drives;
- preserve raw timestamps and diagnostic-session metadata;
- treat data obtained through a gateway as gateway-observed, not equivalent to direct bus capture.

### Stage B — direct CAN observation using reversible breakout harnesses
Target candidate networks:
- PT-CAN
- PT-CAN2
- K-CAN
- K-CAN2

Exact connector/pin selection must come from vehicle-specific wiring diagrams for the exact build/options, then be electrically verified before connecting the logger.

Passive tap requirements:
- high-impedance receiver;
- galvanic isolation preferred;
- do not add termination to an already terminated vehicle bus;
- short stub;
- removable Y/breakout harness rather than cutting OEM wiring;
- default interface configuration listen-only/silent where supported;
- record bus/channel identity in capture metadata.

### Stage C — FlexRay observation
FlexRay is valuable for chassis/motion correlation but is not an M1 blocker.

Before connecting:
1. obtain exact F13 topology/wiring for the target node/branch;
2. identify channel/branch and physical-layer requirements;
3. use hardware explicitly supporting passive FlexRay monitoring;
4. validate on bench first;
5. do not splice arbitrary long stubs into the FlexRay topology.

The first FlexRay objective is observation/correlation only: reconstruct timing and chassis state around ICM/DSC/EPS/rear-steer behaviour. No FlexRay transmission is part of M1.

## Modules of interest

### ZGM
Use as topology anchor and diagnostic gateway reference. Do not assume it is the best physical tap for every network.

### ICM
High-value source/domain for vehicle dynamics context. Candidate signals to validate include yaw-related state, longitudinal/lateral dynamics and integrated chassis state. Signal IDs/scaling remain UNKNOWN until verified.

### DSC
High-value for wheel/motion/braking/intervention correlation. Never infer brake command authority merely from observing DSC traffic.

### EPS
High-value for steering-state correlation. M1 remains read-only.

### HSR / rear steering
The F12/F13 bus overview includes HSR in the chassis architecture. Prototype 001 must correlate any decoded rear-steer state against independent vehicle motion before using it in swept-path prediction.

### KAFAS / ACC / parking systems
Useful later as independent OEM perception/advisory sources. Their presence and exact network path depend on vehicle equipment. Missing option/module must be represented as unavailable, not synthesized.

## Capture naming

Every raw channel gets a stable logical name independent of USB enumeration:

```
bmw.obd_diag
bmw.pt_can_a
bmw.pt_can2_a
bmw.k_can_a
bmw.k_can2_a
bmw.flexray_a
```

Physical connector, adapter serial, wiring-diagram reference and measured bus characteristics are stored in the episode manifest.

## Verification worksheet per tap

Before first capture record:
- exact vehicle/build/options
- wiring-diagram document/revision
- module and connector designation
- candidate pins
- measured voltage characteristics with suitable instrumentation
- observed bitrate/protocol
- termination/resistance check performed only with vehicle safely powered down as appropriate
- logger interface mode
- isolation status
- timestamp source
- reversible harness ID

Only after those checks can a candidate tap be marked VERIFIED_FOR_PASSIVE_CAPTURE.

## M1 recommended order

1. OBD-side baseline
2. one verified direct CAN
3. second CAN / cross-gateway correlation
4. GNSS+IMU synchronization
5. front camera synchronization
6. ICM/DSC/EPS state decoding
7. HSR/rear-steer correlation
8. remaining CAN networks
9. passive FlexRay capture
10. KAFAS/radar/parking fusion

## Hard rule

Architecture diagrams tell us *which networks and modules exist*. They do not safely provide the exact physical tap for this individual car. Exact pins, colours and connector locations must be verified from the correct BMW wiring data and the vehicle itself before a harness is built.
