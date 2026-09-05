# Digital Cockpit Architecture v0

## 1. Objective

Build a multi-display F13 HMI where the Android head unit, Android cluster and OEM HUD can show the same navigation/media/vehicle session independently.

The central principle is **state distribution, not pixel distribution**.

The head unit may show Spotify while the cluster shows a map and the HUD shows the next maneuver. Conversely, the head unit may show full navigation while the cluster shows gauges only.

## 2. Runtime domains

### Vehicle Gateway

Independent MCU/Linux gateway between BMW networks and non-OEM compute.

Responsibilities:
- read and normalize approved BMW state
- timestamp and sanity-check inputs
- watchdog Android/ADAS peers
- expose read-only vehicle state to HMI clients during early milestones
- later host separately reviewed control interfaces

The Android cluster is never the safety authority.

### Cluster Runtime

Primary driver-facing HMI.

Responsibilities:
- instruments and tell-tales
- navigation presentation
- media presentation
- phone presentation
- ADAS/OpenPilot visualization
- theme/layout switching
- user display preferences
- HUD composition requests

### Radio Bridge

Runs on the 14.9-inch Android head unit.

Responsibilities:
- navigation-session host/adapter
- MediaSession/media metadata adapter
- radio/Bluetooth/vendor-MCU adapters where available
- publish normalized state to the cluster
- accept safe UI/media/navigation commands from the cluster

### HUD Manager

Consumes normalized navigation/vehicle/ADAS state and converts it into an abstract HUD model.

Initial implementation is a mock transport. BMW HUD/KOMBI injection is not considered solved until bench captures identify the exact supported messages and graphics.

## 3. Transport

Prototype transport: WebSocket over a dedicated local IP link.

Preferred physical order:
1. USB Ethernet / dedicated Ethernet
2. isolated Wi-Fi link
3. shared hotspot only for development

Messages carry monotonically increasing sequence numbers and source timestamps.

Suggested streams:

```text
/state/vehicle       10-20 Hz
/state/navigation     1-5 Hz + change events
/state/media          on change + 1 Hz progress
/state/adas           10-20 Hz for visualization
/state/phone          on change
/state/preferences    on change
/command/media        event
/command/navigation   event
/command/display      event
```

The transport must be replaceable later by protobuf/gRPC/ZeroMQ without changing UI models.

## 4. Navigation

The radio hosts one navigation session. The cluster does not depend on the radio's visible screen.

Normalized navigation state includes:
- active/rerouting/arrived state
- destination
- current road
- next road
- maneuver type
- maneuver distance
- exit/roundabout information
- lane guidance when available
- ETA
- remaining distance/time
- route polyline/segments for cluster map rendering
- road-snapped position when available

The radio can render the full navigation UI. The cluster can independently render a mini-map or maneuver card. HUD receives only reduced guidance.

Screen mirroring remains an optional `MirrorTile` feature and is never the primary navigation path.

## 5. Media

All media sources normalize into one `MediaState`.

Potential adapters:
- Android MediaSession (Spotify/Tidal/Poweramp/etc.)
- Bluetooth AVRCP
- Android Auto/CarPlay bridge when metadata is exposed
- head-unit FM/DAB MCU adapter
- CIC/Combox adapter after BMW bus/MOST research

Normalized controls:
- play
- pause
- next
- previous
- seek
- source select (only where the source adapter supports it)

Artwork is transferred only when its content ID changes and cached by the cluster.

## 6. Display independence

Each display has independent preferences:

```text
radioNavMode   = FULL | CARD | OFF
clusterNavMode = MAP | CARD | OFF
hudNavMode     = GUIDANCE | MINIMAL | OFF

clusterMediaMode = AUTO | COMPACT | EXPANDED | OFF
```

No display state implies another display state.

## 7. Priority model

Driver-information priority, highest first:
1. mandatory/critical vehicle warnings
2. safety/ADAS takeover warnings
3. core instruments
4. navigation maneuver guidance
5. phone call state
6. media/source changes
7. decorative/secondary content

A media artwork animation must never hide a critical warning or required instrument.

## 8. Failure behavior

### Radio lost
- cluster keeps vehicle instruments
- last nav/media state expires after timeout
- HUD removes stale navigation/media guidance

### Cluster process lost
- vehicle gateway remains alive
- radio remains usable
- OEM fallback remains available

### Gateway lost
- cluster visibly marks vehicle-data loss
- HMI must not synthesize plausible-looking speed/RPM values
- autonomy/control path handles this independently through its safety design

## 9. Development phases

### C0 — Desktop/Android simulator
- shared state model
- fake vehicle publisher
- fake nav/media publisher
- cluster renderer

### C1 — Two Android devices
- radio bridge on test Android
- cluster app on second Android
- WebSocket synchronization
- independent nav/media display modes

### C2 — Real aftermarket hardware
- identify head-unit MCU/platform
- identify cluster platform
- ADB/app-install capability
- stable boot/autostart

### C3 — BMW read-only integration
- gateway receives logged/decoded BMW data
- cluster shows real speed/RPM/gear/doors/warnings
- no control transmission

### C4 — Navigation/media production adapters
- navigation SDK adapter
- MediaSession adapter
- Bluetooth/radio adapters

### C5 — HUD bench
- capture OEM HUD-related traffic
- create abstract-to-BMW HUD adapter
- validate fail-safe behavior on bench

## 10. Graphics strategy

Android hardware target: Kotlin + Jetpack Compose.

UI layers:

```text
ClusterRoot
  ThemeEngine
  WarningLayer
  NavigationLayer
  InstrumentLayer
  AdasLayer
  MediaLayer
  PhoneLayer
  DebugLayer (dev builds only)
```

The state model is immutable from the renderer's point of view. Themes map state into geometry/typography/animations without changing vehicle logic.
