# comma/openpilot Outreach Drafts

Status: prepared, not sent.

## 1. Discord / car-port introduction

Hi — we are working on a read-only BMW F13/F-series openpilot research port.

A quick transparency note: we are BMW F13/F-series enthusiasts rather than professional autonomous-driving software engineers. Our stronger background is practical BMW F13/F-series work, electrical/electronic systems, diagnostics, hardware integration and basic programming. We use AI extensively for research, code generation, tests and documentation, and we are specifically looking for experienced developers to challenge and review the software side rather than pretending we can independently validate every low-level implementation detail.

The broader motivation is that the F13/F-series remains a high-value luxury platform, but its ADAS stack is now more than a decade behind current vehicles. We are interested in whether owners can keep these cars and add carefully integrated 2026-era driver-assistance technology instead of replacing the vehicle purely for software features.

The main technical blocker is the BMW CAN/FlexRay boundary. Instead of assuming the car needs a generic FlexRay bridge, we built passive tooling that preserves CAN/FlexRay provenance and ranks which functions appear on CAN, FlexRay, or both.

Current repo work includes:

- transport-aware CAN/FlexRay frame model;
- event-driven function identification;
- cross-session evidence;
- FRR range/velocity and track hypotheses;
- CAN↔FlexRay temporal correspondence;
- request↔feedback topology inference;
- a minimal Comma Four Beta 1 plan with no BMW actuation.

We will have the actual 2012 F13 available for synchronized validation in December 2026.

Before we build a BMW-specific upstream-shaped adapter, we would appreciate guidance on two narrow questions:

1. Once real signals are validated, would a dashcam-only/read-only BMW `opendbc/car/bmw` scaffold be a useful first upstream contribution?
2. For genuinely FlexRay-only observations, would you prefer the transport to remain external and normalize into existing vehicle interfaces, or is there interest in a generic transport abstraction if the implementation is small and independently useful?

We are intentionally not proposing steering/brake control until replay/HIL/closed-course evidence exists.

Repo: https://github.com/freddykat/f13-autonomy

## 2. Short GitHub discussion/issue-style version

### BMW F-series read-only port research / FlexRay boundary

We are preparing an evidence-first BMW F-series openpilot port around a Comma Four.

We should be transparent about the team: this is a BMW F13/F-series enthusiast-led project with stronger practical electrical/electronic, vehicle-integration and diagnostics experience than advanced software expertise. AI is heavily used for implementation support, tests and documentation, and we want upstream/community review precisely because we do not claim to be expert openpilot or embedded-safety developers.

BMW is currently outside upstream support and the official compatibility docs call out FlexRay as a blocker. Our current work is therefore focused on determining, function by function, whether useful F13 state is:

- visible through CAN/ZGW;
- FlexRay-only;
- represented on both transports;
- or unresolved.

We have implemented offline/read-only tools for transport-aware signal discovery, cross-session evidence, CAN↔FlexRay correspondence and request↔feedback topology.

No BMW control path exists.

We expect real F13 captures in December 2026. We would like upstream guidance on the preferred shape of a future read-only BMW brand scaffold and, separately, whether generic FlexRay observation support would be useful upstream if kept small and transport-focused.

## 3. COMMA_HACK 7 application idea

Project title:

**BMW/FlexRay Shadow Port for Comma Four**

One-line pitch:

Build a transport-aware, read-only BMW F-series shadow port that lets a Comma Four consume validated BMW state without pretending FlexRay is CAN.

Team note: BMW F13/F-series enthusiast-led, with strong practical automotive/electrical/electronic integration background, basic programming experience, and AI-assisted software development. The goal of the hack would include getting experienced review on architecture and implementation choices rather than presenting the code as expert-authored autonomy software.

Demo target:

```text
Comma Four openpilot replay
+
BMW CAN/FlexRay recorded or synthetic transport
+
automatic function identification
+
BMWVehicleState / CarState shadow adapter
+
CAN↔FlexRay correspondence
+
BMWControlIntent SHADOW
```

Why useful:

There is a large class of high-value premium vehicles whose mechanical/chassis quality remains excellent while their ADAS/software stack is outdated. BMW, Mercedes, Audi, Land Rover and some Volvo platforms are also currently outside normal openpilot support partly because of FlexRay. The project explores whether useful state can remain CAN-first while adding FlexRay only where evidence proves it is required.

Safety boundary:

No steering, brake, throttle, gear or FlexRay TX.

## 4. Later private engineering outreach

Use only after real BMW evidence exists.

Subject concept:

**BMW F-series openpilot/FlexRay research — validated read-only port evidence**

Body concept:

We have completed synchronized real-car BMW F13 CAN/FlexRay observation and can provide reproducible evidence for core CarState fields, ACC/SWW observations and the CAN-vs-FlexRay transport boundary.

Rather than asking comma to support the vehicle directly, we would like feedback on a small upstream contribution path. We can keep the first BMW port dashcam-only/read-only and split generic transport work from BMW-specific decoders.

The useful artifacts are:
- exact vehicle/ECU provenance;
- repeated signal evidence;
- replayable captures;
- unit-tested decoders;
- transport correspondence;
- explicit UNKNOWN/stale handling.

If this aligns with openpilot priorities, we would be happy to reshape the work into small reviewable PRs.

## Rules before sending

- link only green-CI main or a focused PR;
- do not claim BMW support exists;
- do not lead with Tesla HW4, parking, LiDAR or full autonomy;
- do not ask comma to validate public-road actuation;
- ask one narrow technical question at a time;
- keep initial outreach short;
- offer evidence and code rather than architecture slides.


## Transparency wording to keep in all external outreach

Use some version of this when appropriate:

> We are BMW F13/F-series enthusiasts and practical integrators, not professional autonomous-driving software engineers. Our strongest background is automotive electrical/electronic systems, diagnostics, hardware integration and basic programming. We use AI extensively to help research, implement, test and document the software. We can define the practical vehicle problem and understand the intended system behavior, but we do not claim that we can independently implement or audit every advanced software or safety-critical detail. We are looking for experienced developers to review, correct and help upstream the work where useful.

Do not hide or minimize the use of AI.

Do not imply:
- professional openpilot development experience;
- professional embedded-safety experience;
- that every generated line was manually authored or deeply audited by us;
- that passing unit tests alone makes safety-critical code trustworthy.

The value we bring should be framed as:
- practical BMW F13/F-series and electrical/electronic integration knowledge;
- persistent reverse-engineering work;
- vehicle access and future real-world evidence;
- system-level ideas and test scenarios;
- willingness to document everything openly;
- willingness to accept technical correction and reshape code for upstream standards.


## Owner / market motivation

A useful way to explain the end-user motivation without overselling it:

> Many BMW F13/F-series owners are maintaining cars that were expensive, technically sophisticated luxury vehicles and are still desirable today. What dates them most is often not the chassis or powertrain, but the software and driver-assistance stack. We want to explore a path for those owners to gain modern, 2026-era supervised driver-assistance and perception features while keeping the original car and preserving OEM/manual operation.

Avoid framing this as "expensive-car owners deserve special treatment." The stronger framing is:
- preserve valuable existing vehicles;
- extend useful life;
- reduce technology obsolescence;
- offer modern safety/ADAS capability without forcing vehicle replacement;
- keep retrofits reversible and OEM-aware.
