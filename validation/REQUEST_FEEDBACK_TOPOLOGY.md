# BMW Request ↔ Feedback Topology

## Purpose

This stage estimates temporal ordering between already-selected BMW raw signal candidates.

It is designed to help distinguish a possible upstream request/state candidate from downstream actuator feedback and eventual physical vehicle response.

It remains offline/read-only.

## Example

```text
candidate A
  changes first

candidate B
  follows +8 ms

steering angle
  follows +15 ms

yaw
  follows +35 ms
```

Possible interpretation:

```text
A -> upstream-like
B -> actuator/internal-state-like
steering angle -> feedback-like
yaw -> physical-response-like
```

This is not proof that A is a steering command.

## Method

For nodes in the same function family:

1. extract the raw series with CAN/FlexRay provenance preserved;
2. search a bounded lead/lag range;
3. align samples by timestamp;
4. compute raw correlation;
5. rank edges by correlation × overlap;
6. label relative ordering:
   - SOURCE_LEADS_TARGET
   - SOURCE_FOLLOWS_TARGET
   - SIMULTANEOUS_WITHIN_RESOLUTION

A positive best lag means the source series tends to occur first and the target follows.

## Uses

### Steering

```text
possible ICM state/request
      ↓
possible EPS/AL state
      ↓
steering-angle feedback
      ↓
yaw response
```

### Longitudinal

```text
ACC/setpoint-like state
      ↓
DSC/DME response-like state
      ↓
longitudinal acceleration
      ↓
vehicle speed
```

### Indicators

```text
stalk state
      ↓
network request-like state
      ↓
body-controller/lamp state
```

### Parking

```text
park-assist state
      ↓
steering request-like candidate
      ↓
road-wheel angle
      ↓
vehicle motion
```

## Required caution

Correlation and temporal lead do not establish causality.

An upstream-looking field may still be:

- another observer of the same sensor;
- a forwarded ZGW representation;
- an ECU estimate;
- a supervisory state;
- a counter or transformed state that happens to lead.

Request roles require additional cross-session, topology, diagnostic and HIL evidence.

## Safety boundary

The analyzer has no:

- CAN transmit;
- FlexRay transmit;
- diagnostic writes;
- control-message encoding;
- checksum/alive-counter generation;
- EPS/DSC/DME/EGS command path;
- openpilot CarController integration.

Output status remains:

`UNVALIDATED_REQUEST_FEEDBACK_TOPOLOGY`
