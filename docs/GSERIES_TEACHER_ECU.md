# G-Series Teacher ECU Bench

Status: research concept only. Passive/offline/HIL study. No direct F13 actuation.

## Question

Can a more modern BMW driver-assistance ECU be used as a reference to understand how BMW structures steering, longitudinal, parking and ADAS coordination?

Yes — as a **teacher ECU / bench reference**, not as a plug-in controller for the F13.

## Best initial teacher candidate: G30/G12-era SAS

BMW G-series uses an optional-equipment / driver-assistance controller commonly referred to as SAS.

Public technical material indicates that SAS:

- receives sensor/control-unit information rather than containing its own primary sensors;
- participates in adaptive cruise, lane-keeping/traffic-jam assistance and parking-related functions depending vehicle/equipment;
- is connected into BMW FlexRay;
- interfaces with local CAN networks for radar/blind-spot subsystems on some architectures;
- coexists with KAFAS and modern chassis controllers.

A G30 SAS teardown also shows a hardware architecture with:

- Infineon AURIX/TC297-class MCU;
- FlexRay transceiver;
- multiple high-speed CAN interfaces;
- automotive Ethernet.

That makes SAS interesting because it sits close to the exact architectural boundary we care about:

```text
perception / ADAS logic
      ↓
BMW semantic requests
      ↓
chassis / steering / braking domains
```

## What we want to learn from it

Not raw command injection into the F13.

We want to study:

1. message/state taxonomy;
2. which functions live on FlexRay vs CAN vs Ethernet;
3. separation between request, enable, status and feedback;
4. timing and update rates;
5. stale/invalid state behavior;
6. counters/checksums in a bench environment;
7. ECU-to-ECU topology;
8. how steering and ACC requests are represented semantically;
9. parking/PMA coordination;
10. how KAFAS/radar/SAS divide responsibility.

## Suggested donor bench layers

### A. SAS

Primary modern ADAS coordination teacher.

### B. KAFAS4 / modern KAFAS

Useful for:

- lane/object/perception outputs;
- traffic-control state;
- camera-to-SAS relationship;
- semantic message structure.

### C. Modern EPS

Useful only as a bench reference for:

- request vs feedback separation;
- driver torque/override states;
- health/fault state;
- angle/torque semantics.

Do not assume G-series EPS command messages can be translated directly to an F-series steering actuator.

### D. DSC / ICM / VDP-class chassis controllers

Useful for understanding:

- longitudinal request/response topology;
- yaw/acceleration feedback;
- chassis arbitration;
- steering/braking coordination.

### E. PMA / parking-related controller

Useful for low-speed coordination and parking-state machine research.

## Safe bench architecture

```text
G-series donor ECU(s)
        ↓
isolated bench harness
        ↓
CAN / FlexRay / Ethernet passive capture
        ↓
our transport-aware logger
        ↓
function identifier
        ↓
request↔feedback topology
        ↓
semantic comparison with F-series captures
```

The first phase should be:

- power-up inventory;
- passive bus observation;
- read-only diagnostics;
- recorded donor traffic where legally available;
- offline replay.

No connection from a donor G-series ECU to a live F13 actuator network is part of this research stage.

## Why a teacher ECU helps

Without a modern reference we may observe an F13 signal and know only:

> this field correlates with steering.

With a modern BMW reference we may see a recurring design pattern:

```text
enable state
request state
requested curvature/angle-like value
actual value
driver override
validity
alive counter
fault state
```

That can guide where to look in F-series traffic.

The teacher does not prove equivalence.

It generates hypotheses.

## Cross-generation semantic mapper

Future offline tool concept:

```text
G-series known/partly-known semantic state
            +
F-series raw candidate
            ↓
cross-generation correlation
            ↓
semantic-family hypothesis
```

Example output:

```text
F13 candidate X
resembles modern BMW:
  STEERING_REQUEST_STATE_LIKE

confidence:
  MEDIUM

evidence:
  event pattern
  update rate
  request→feedback lag
  validity behavior
```

Still not a decoder or command.

## Candidate modern platforms

### G30 / G31 5 Series

Preferred initial donor family because:

- modern but not latest-generation zonal architecture;
- SAS is well documented publicly;
- rich 5AT/5AU driver-assistance variants exist;
- combines CAN, FlexRay and automotive Ethernet;
- close conceptual successor to F10/F11.

### G11 / G12 7 Series

Very useful for:

- SAS;
- EPS/steering-angle over FlexRay;
- rear-steer/HSR;
- parking;
- high-end ADAS architecture.

### G14 / G15 / G16 8 Series

Interesting later comparison to F06/F12/F13 because it is the conceptual successor to the 6 Series GT/coupé family and adds later Ethernet-connected radar/camera architecture.

## What not to do

Do not assume:

- same CAN IDs;
- same FlexRay slots;
- same scaling;
- same checksums;
- same request semantics;
- same EPS protocol;
- same DSC protocol;
- same gateway routing;
- same safety model.

Do not create a generic:

```text
G-series command
→ translate
→ F13 actuator
```

The correct use is:

```text
G-series behavior
→ semantic pattern
→ F-series hypothesis
→ F-series-specific validation
```

## Possible future research kit

A useful isolated donor set could eventually include:

- one G30/G12 SAS;
- matching KAFAS module;
- one modern EPS controller/rack or bench ECU;
- DSC/ICM/VDP-class controller as needed;
- ZGW/BDC depending topology;
- appropriate gateway/network bench harness;
- CAN/FlexRay/Ethernet capture interfaces;
- programmable protected bench power.

Acquisition should wait until the exact learning objective and donor compatibility are documented.

## Project safety boundary

This document authorizes research planning only.

Current allowed uses:

- passive capture;
- read-only diagnostics;
- offline decoding;
- replay;
- isolated bench/HIL experiments after explicit review.

Current prohibited project uses:

- live donor ECU commanding the F13;
- direct G-series-to-F13 message forwarding;
- FlexRay MITM/TX on the vehicle;
- EPS/DSC/DME live actuation without the existing staged review gates.
