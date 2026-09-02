# F13 Digital Cockpit

Experimental driver-display and infotainment integration for the BMW F13 project.

The goal is to build a custom Android cluster that renders BMW vehicle state, navigation, media, phone and ADAS information independently from the 14.9-inch Android head unit, while keeping the OEM CIC/Combox domain available as fallback.

## Design rules

- The cluster is the primary driver UI, not the safety authority.
- Safety-critical vehicle state comes from a dedicated vehicle gateway, not directly from an Android app.
- The 14.9-inch Android head unit is the infotainment and navigation host.
- Navigation is exchanged as structured state, not as a crop of the radio screen.
- Media is exchanged as normalized metadata/actions, not as screen sharing.
- HUD output is a reduced presentation of the same normalized state.
- Android cluster/head-unit crashes must not become vehicle-control failures.
- OEM CIC/Combox functions remain available during development.

## Logical masters

| Domain | Authority |
|---|---|
| Vehicle/safety state | BMW + vehicle gateway |
| Driver UI | Android cluster |
| Navigation session | Android head-unit navigation host |
| Infotainment/media | Android head unit |
| ADAS state | openpilot/ADAS compute |
| HUD composition | HUD manager using normalized state |

## Data flow

```text
BMW CAN/FlexRay/OEM modules
          |
          v
   Vehicle Gateway
          |
          +--------------------+
          |                    |
          v                    v
 Android Cluster <------> Android 14.9" Head Unit
      |                         |
      |                         +-- Navigation host
      |                         +-- Spotify/media
      |                         +-- Bluetooth/FM/DAB
      |                         +-- CIC passthrough
      |
      +-- vehicle instruments
      +-- navigation renderer
      +-- media renderer
      +-- ADAS/OpenPilot renderer
      +-- theme engine
      |
      v
   HUD manager
      |
      v
   BMW OEM HUD
```

## First prototype

The first milestone deliberately avoids BMW control traffic. It uses simulated vehicle data and two Android processes/devices:

1. **Radio bridge** publishes navigation/media state.
2. **Cluster app** subscribes to normalized state and renders it.
3. **Simulator** publishes speed/RPM/gear/warnings/ADAS test data.
4. **HUD adapter** remains a mock transport until the F13 HUD protocol is validated on bench.

## Planned themes

- OEM+ / 6WB-inspired
- M Performance
- M Track
- Navigation Focus
- OpenPilot / ADAS Focus
- Night

Themes only change presentation. They do not change the underlying vehicle/nav/media state model.

## Initial protocol groups

- `VehicleState`
- `NavigationState`
- `MediaState`
- `PhoneState`
- `AdasState`
- `HudState`
- `DisplayPreferences`

See `docs/ARCHITECTURE.md` and `shared-model/UiState.kt`.

## External projects worth studying

We may study architecture and public APIs from projects such as BMW iDrive Launcher, OpenAutoLink, Kombibridge and open automotive Qt/QML dashboards. Do not copy code or assets without checking their licences first.

## Safety scope

This directory is a display/integration project. It must not become a path for unreviewed Android code to command steering, braking or drivetrain functions. Vehicle-control work belongs behind the separate safety/gateway architecture and its validation process.
