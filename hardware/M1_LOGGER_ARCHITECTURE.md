# M1 Passive Logger Hardware Architecture

Status: architecture freeze before product/BOM selection

## Goal

Build a reliable, synchronized, read-only data-acquisition platform for Prototype 001 before selecting exact parts. The logger must capture BMW vehicle state, independent motion reference and camera data without creating a control path to the vehicle.

## Top-level architecture

```text
BMW CAN / FlexRay / other readable buses
                |
                v
        isolated bus interfaces
                |
                +------------------+
                |                  |
                v                  v
          logger compute      timestamp service
                ^                  ^
                |                  |
GNSS ---------->+                  |
IMU ------------+------------------+
                |
forward cameras +----> capture/indexing
                |
NVMe / SSD <----+----> episode storage
                |
                +----> optional display / service UI
```

No actuator interface is part of M1.

## 1. Compute node

The initial compute node does not need high-end inference performance. It must prioritize deterministic I/O, storage throughput, Linux support and expandability.

Minimum architecture requirements:
- x86-64 or ARM64 Linux support
- at least 4 modern CPU cores
- minimum 8 GB RAM; 16 GB preferred
- native NVMe support
- at least 2 independent USB 3.x controllers/ports or equivalent high-bandwidth camera I/O
- Ethernet
- hardware or kernel-supported monotonic clock suitable for source timestamp correlation
- automatic boot and clean shutdown support
- operating temperature appropriate for a vehicle cabin/trunk installation

GPU acceleration is optional in M1. Heavy perception can initially be run offline after the drive.

## 2. BMW bus acquisition

### CAN

Requirements:
- electrically isolated interface where practical
- listen-only capability
- hardware timestamps strongly preferred
- support for multiple simultaneous CAN buses
- CAN FD capability is desirable for reuse even if a specific F13 bus is classic CAN

The logger must default to listen-only mode.

### FlexRay

FlexRay access is a separate requirement and must not be treated as CAN with a different connector.

Requirements:
- dual-channel FlexRay support where required
- deterministic receive timestamps
- raw-frame capture
- ability to operate without transmitting frames during M1
- Linux-compatible API or a bridge with documented capture format

FlexRay hardware selection is expected to be one of the more difficult/costly parts of the BOM, so the design must allow M1-A to begin with CAN + independent motion logging while FlexRay integration is completed.

## 3. GNSS

Minimum requirements:
- raw timestamped position/velocity output
- at least 10 Hz navigation updates preferred
- PPS output strongly preferred
- external automotive antenna support
- GNSS time availability for cross-checking the monotonic timeline

RTK is optional for initial highway learning. The architecture should allow later RTK replacement without changing the rest of the logger.

## 4. IMU

Minimum requirements:
- 3-axis gyro
- 3-axis accelerometer
- at least 100 Hz sample rate; 200 Hz preferred
- hardware timestamp or deterministic host acquisition
- known sensor range/resolution
- rigid mounting to vehicle body

The mounting orientation becomes part of the calibration metadata.

## 5. Cameras

### Phase A
Start with forward perception cameras only.

Requirements:
- global shutter preferred for motion/perception cameras
- fixed, known optics
- stable frame rate
- exposure timestamps where possible
- no hidden frame interpolation
- calibration data stored per camera

The first logger should reserve bandwidth, storage and synchronization interfaces for later surround cameras.

### Phase B
Add left/right/rear/near-field cameras only after Phase A proves synchronized recording and replay.

## 6. Storage

Primary recording storage should be NVMe/SSD rather than SD card.

Requirements:
- sustained write bandwidth above worst-case combined bus + video data rate with margin
- power-loss-resilient filesystem strategy
- episode segmentation
- free-space monitoring
- SMART/health monitoring where available
- ability to remove/copy data without reconfiguring the logger

Recommended design target: at least 2x expected peak write bandwidth and enough capacity for multiple full driving sessions.

## 7. Power system

The logger must not be connected directly to an unprotected vehicle 12 V feed.

Required power path:

```text
vehicle supply
   -> fuse
   -> automotive transient/reverse-polarity protection
   -> low-voltage cutoff
   -> regulated DC/DC rails
   -> compute / interfaces / cameras
```

Required behaviours:
- ignition/wake sense separate from main power
- delayed clean shutdown
- protection against battery depletion while parked
- brownout handling during engine start
- no back-feeding into BMW circuits

A small UPS/supercapacitor or dedicated shutdown reserve may be added if needed to close files cleanly.

## 8. Time synchronization

Time alignment is a first-class subsystem.

Preferred hierarchy:
1. host monotonic clock as common local timeline
2. GNSS PPS disciplines/checks logger time
3. hardware bus timestamps transformed into host timeline
4. camera exposure timestamps transformed into host timeline
5. IMU timestamps transformed into host timeline

Every record preserves both source timestamp and normalized timestamp where available.

Target M1 timing goals:
- BMW bus correlation: <= 2 ms where hardware permits
- IMU correlation: <= 2 ms
- camera-to-vehicle correlation: <= 10 ms initial target, with tighter calibration pursued later
- GNSS position timestamp integrity more important than raw low latency

## 9. Isolation between acquisition and future control

M1 uses physical/software separation to reduce accidental authority:
- interfaces configured listen-only where supported
- no control-service dependencies in logger boot target
- capture software has no actuator API
- future control gateway must be a separate explicitly reviewed subsystem

Observation authority is not actuation authority.

## 10. Service/HMI

A small service UI may show:
- recording status
- disk remaining
- camera health
- bus health
- GNSS lock
- IMU health
- clock sync quality
- current episode ID

It must not require interaction while driving.

## 11. Environmental/mechanical installation

The enclosure should provide:
- secure mounting
- strain relief on all connectors
- airflow or conductive cooling as required
- protection from loose cargo
- access to removable storage/service connectors
- clear labeling of every bus connection

The GNSS antenna requires an appropriate view of the sky. The IMU must be rigidly attached to the vehicle body, not a soft trim panel.

## 12. BOM selection gates

Do not select a product unless its documentation verifies the required interface.

For each candidate part record:
- exact model
- electrical interface
- Linux driver/API
- timestamp capability
- isolation
- sample/frame rate
- power draw
- automotive supply requirements
- price
- availability
- known limitations

## 13. First purchasable configurations

### M1-Lite
- inexpensive Linux compute
- 1-2 CAN interfaces
- GNSS + PPS
- IMU
- NVMe
- one forward camera
- protected DC/DC

Purpose: begin synchronized real BMW motion learning at the lowest cost.

### M1-Full Logger
Adds:
- multi-bus CAN
- FlexRay capture
- multiple synchronized cameras
- larger storage
- higher-bandwidth networking

### M1-Perception Compute
Separate optional high-performance GPU computer for offline/online perception. It should consume the same logged interfaces rather than forcing the acquisition logger to become the safety-critical compute node.

## Definition of success

The hardware architecture is successful when a drive can be replayed with trustworthy timing between:

`BMW chassis state <-> independent IMU/GNSS <-> forward video <-> traffic-control detections <-> shadow decisions`

without any M1 component being capable of commanding the vehicle.