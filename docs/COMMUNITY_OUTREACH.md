# Community Outreach

## Short project pitch

We are building an experimental BMW F13 autonomy platform based on openpilot, custom synchronized cameras, BMW CAN/FlexRay integration and a separate Tesla HW4/FSD read-only behavioural benchmark.

We are not professional autonomous-driving software developers. Our background is practical automotive/mechanical/electrical engineering, and we are using AI-assisted research and development to help structure and implement the project.

The unusual part of the project is the benchmark loop:

```text
Tesla HW4/FSD behaviour
        vs
openpilot behaviour
        vs
our own policy/world model
        vs
human driver
```

The BMW should ultimately run independently from Tesla hardware. HW4 is intended only as a teacher/reference system.

We are especially looking for people with real experience in Tesla HW4 bench testing, DAS/FSD CAN, openpilot custom hardware, BMW FlexRay/ICM/DSC/EPS and multi-camera perception.

## Message for HW4 / Tesla CAN developers

Hi,

We found your work while doing AI-assisted research into Tesla HW4, CAN/DAS and FSD bench testing.

We should be transparent that we are not professional software developers. Our background is much more practical/mechanical/electrical engineering, and we are trying to build the software side in a modular way with AI assistance and help from people who already know these systems deeply.

Our project is an experimental autonomy stack for a BMW F13, initially focused on supervised motorway/highway driving.

The BMW side is planned around openpilot, custom synchronized cameras, GPU compute, BMW radar/KAFAS/PDC data and a CAN/FlexRay control bridge toward the BMW ICM/DSC/EPS architecture.

We do not want to put Tesla FSD directly in control of the BMW.

Instead, we want to use a genuine HW4 running legitimate FSD as a read-only behavioural teacher/benchmark. In the same driving situation we want to compare:

- Tesla FSD behaviour
- openpilot behaviour
- our own world-model/policy behaviour
- human-driver action

The idea is to collect disagreements and use those events for validation, tuning and eventually training so the independent openpilot-based system can progressively approach the benchmark.

We are particularly interested in whether it is possible to build a useful read-only HW4 observer/bench and expose enough state to create something like `teslaoracled -> openpilot`.

Useful observable outputs could include, where technically available and reliable, FSD/DAS state, speed intent, longitudinal request, steering/curvature request, lane-change state/direction, blind-spot state, FCW and navigation-related state.

We would really appreciate practical information on:

- minimum viable HW4 bench environment
- which genuine Tesla modules must remain present
- which vehicle states can be replayed/emulated for legitimate research
- camera/calibration requirements
- which DAS/FSD outputs can be externally observed
- what changes across OTA versions
- whether recorded CAN/state replay can reproduce useful development conditions

The Tesla side would remain electrically isolated from direct BMW actuation. BMW control would go through our own openpilot/vehicle-command/safety-MCU/BMW CAN-FlexRay stack.

If this sounds interesting, we would be very interested in collaborating and documenting what we learn openly in the project.

The goal is not to copy or redistribute Tesla proprietary FSD software or model weights. The experiment is whether an evolving HW4/FSD system can be used as a teacher/benchmark to improve an independent openpilot-based highway autonomy stack.

Thanks for any guidance or collaboration.
