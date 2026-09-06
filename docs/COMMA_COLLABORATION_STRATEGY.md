# comma.ai / openpilot Collaboration Strategy

Status: outreach plan, 2026-09-06.

## Why this project is relevant to comma/openpilot

The official openpilot supported-cars documentation currently states that supported vehicles use CAN for communication and specifically lists BMW among manufacturers using FlexRay. It also states that FlexRay vehicles may be supported in the future but that there are no immediate plans for FlexRay support.

That makes this project potentially useful if it can reduce the unknowns around:

- BMW F-series signal discovery;
- CAN vs FlexRay transport availability;
- passive FlexRay capture;
- BMW CarState mapping;
- BMW radar/blind-spot mapping;
- safe, reviewable future actuator architecture.

The project should approach comma as a technical contributor first, not as a generic commercial partnership request.

## Transparency about team capability

Do not present the project as if it were led by professional autonomous-driving software engineers.

The accurate description is:

- BMW F13/F-series enthusiast-led;
- strong practical BMW F13/F-series, automotive electrical/electronic, diagnostics and hardware-integration background;
- basic programming ability;
- substantial AI-assisted research, implementation, tests and documentation;
- strong system-level ideas and practical vehicle understanding;
- limited ability to independently implement or fully audit advanced openpilot, embedded-safety, ML or low-level real-time code without expert review.

This should be stated early enough that nobody reviewing the repository has to infer it later.

The goal is not to apologize for using AI. The goal is to make the development model clear:

```text
practical vehicle knowledge + system ideas
                +
AI-assisted implementation
                +
tests/replay
                +
experienced external review
                ↓
       progressively trustworthy work
```

Passing CI is evidence that the code satisfies the tests, not evidence that the authors possess professional safety-software expertise or that the implementation is safe for vehicle actuation.

## comma's preferred collaboration style

Current comma/openpilot public guidance strongly favors:

- GitHub pull requests;
- GitHub issues for concrete technical problems;
- Discord discussion for car ports and work in progress;
- small, reviewable changes with a clear goal;
- external contributors maintaining/improving brand ports.

comma's public car-company guidance explicitly describes upstream pull requests and brand-port maintenance as a useful collaboration model.

## Recommended outreach order

### Stage 1 — make the repository reviewable

Before asking for engineering attention, maintain:

- concise README;
- current project-status page;
- exact upstream commit provenance;
- machine-readable safety/read-only boundaries;
- deterministic unit tests;
- no unvalidated BMW decoder claims;
- no live actuation code.

Goal: a comma/openpilot engineer should understand the useful part of the project in five minutes, including who built it, where AI was used and where expert review is still required.

### Stage 2 — Discord introduction

Join the official comma/openpilot Discord and introduce the project in the most relevant car-port/development channel.

Do not lead with:

> We want a partnership to build FSD for a BMW.

Lead with:

> We are preparing a read-only BMW F-series brand-port research effort and have built transport-aware CAN/FlexRay signal-discovery tooling. We want feedback on what evidence/interface shape would make future upstream BMW work useful to openpilot.

Ask one or two narrow questions.

Suggested initial questions:

1. Would comma be interested in reviewing a read-only BMW/opendbc brand-port scaffold once real F13 CarState signals are validated?
2. If a BMW signal is FlexRay-only, what abstraction boundary would be most acceptable upstream: a generic transport layer, an external receiver normalized before opendbc, or keeping FlexRay support outside upstream until there is broader demand?

### Stage 3 — upstream only generic value first

Potential upstream contribution candidates should be small.

Examples:

- generic replay/signal-analysis tooling that does not depend on BMW;
- provenance/timestamp handling useful for non-CAN transport research;
- tests or documentation improvements around unsupported transport research;
- later, a clean BMW read-only brand scaffold after real vehicle evidence.

Avoid proposing:

- the complete F13 autonomy repo;
- Scene3D;
- Tesla HW4 benchmarking;
- parking/summon;
- eGPU architecture;
- one large FlexRay framework;
- unvalidated BMW command messages.

Those are useful project work but are not good first upstream PRs.

### Stage 4 — real F13 evidence

After December capture, prepare a compact evidence package:

```text
vehicle
build date / ECU identities
openpilot baseline
capture hardware
timebase
CAN topology observed
FlexRay topology observed
core CarState candidates
FRR/SWW candidates
cross-session confidence
CAN/FlexRay correspondence
decoder provenance
known unknowns
```

This is the point where a BMW brand-port conversation becomes materially stronger.

### Stage 5 — BMW read-only brand port proposal

Target first upstream-shaped deliverable:

```text
opendbc/car/bmw/
├── interface.py
├── carstate.py
├── values.py
└── radar_interface.py  # only if real tracks are validated
```

Initial platform may remain dashcam-only/read-only.

Do not include a `carcontroller.py` that sends commands until the safety/control work is independently mature.

## Possible forms of collaboration

### A. Community/upstream collaboration — recommended

Most realistic initial route.

Benefits:

- engineering feedback;
- alignment with upstream interfaces;
- possible code review;
- avoids maintaining unnecessary divergence;
- creates a path for later BMW support if FlexRay barriers are solved.

### B. comma hardware collaboration

Possible later if the project demonstrates a useful BMW port or FlexRay interface.

Potential topics:

- Comma Four integration;
- harness topology;
- passive FlexRay companion interface;
- logging/time synchronization;
- Chestnut experiments after the base port works.

Do not request free hardware as the first contact.

### C. Commercial/official partnership

comma's public support page indicates that generic partnership requests are not their normal model. Their published guidance instead points toward wholesale/services and a specific car-company workflow.

For this independent project, commercial partnership should not be the first objective.

A more credible sequence is:

```text
working code
→ useful data
→ upstream contribution
→ engineering relationship
→ then discuss hardware/commercial cooperation if it becomes mutually useful
```

## Immediate 2026 opportunity — COMMA_HACK 7

comma announced COMMA_HACK 7 for September 18–20, 2026 at comma HQ in San Diego, focused on comma hardware, Chestnut and desktop GPUs.

Applications close September 8, 2026.

If travel is realistic, the project could apply with a tightly scoped idea such as:

> Transport-aware BMW/FlexRay passive observation and a Comma Four shadow-port demo.

Do not pitch full vehicle actuation at the hack.

A strong hack demo could be:

```text
Comma Four openpilot replay
+
synthetic/replayed BMW CAN/FlexRay
+
function identification
+
BMWVehicleState
+
shadow control intent
```

This is optional; the project does not depend on attending.

## What to ask comma for

Good requests:

- architectural feedback;
- review/correction of AI-assisted code where it could become upstream-quality;
- acceptable upstream boundaries;
- review of a small generic PR;
- advice on brand-port structure;
- discussion of FlexRay transport abstraction;
- later, review of real BMW CarState/RadarData evidence.

Poor first requests:

- fund the project;
- provide a free Comma Four;
- officially support the F13 immediately;
- review thousands of lines of experimental architecture;
- endorse unvalidated actuation;
- provide safety approval for public-road testing.

## What we can offer comma/openpilot

If executed well, our value is not claiming software expertise we do not have. It is combining practical vehicle access and integration knowledge with transparent, testable, AI-assisted engineering work.

Potential value:

1. a documented BMW F-series observation corpus;
2. CAN/FlexRay transport-availability evidence;
3. passive FlexRay tooling and provenance handling;
4. repeatable function-identification methods;
5. a future BMW opendbc port;
6. tests and replay artifacts;
7. community documentation for a currently unsupported manufacturer family.

The wider value is not one 2012 F13.

The wider value is reducing the cost of understanding **BMW/FlexRay-class vehicles**.

## Outreach gate

Do not contact comma with the full project until these are true:

- README accurately describes the current release baseline;
- project status is current;
- no claim that BMW support already works;
- all recent CI is green;
- at least one compact technical artifact can be linked;
- the first question is narrow and answerable.

The current repo is close to this gate.
