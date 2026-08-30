from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from validation.cross_source_observation_validator import (
    Observation,
    ValidationPolicy,
    validate_signal,
)


DEFAULT_POLICIES = {
    "yaw_rate": ValidationPolicy(max_age_ns=100_000_000, max_disagreement=0.75),
    "vehicle_speed": ValidationPolicy(max_age_ns=150_000_000, max_disagreement=0.75),
    "lateral_acceleration": ValidationPolicy(max_age_ns=100_000_000, max_disagreement=0.35),
}


def _observation(raw: dict[str, Any]) -> Observation:
    return Observation(
        signal=str(raw["signal"]),
        source=str(raw["source"]),
        value=None if raw.get("value") is None else float(raw["value"]),
        unit=str(raw["unit"]),
        sample_time_ns=None if raw.get("sample_time_ns") is None else int(raw["sample_time_ns"]),
        receive_time_ns=int(raw["receive_time_ns"]),
        validity=str(raw.get("validity", "VALID")),
        confidence=float(raw.get("confidence", 1.0)),
        timing_provenance=str(raw.get("timing_provenance", "per_sample_monotonic")),
    )


def _policy(signal: str, raw: dict[str, Any] | None) -> ValidationPolicy:
    if raw is None:
        if signal not in DEFAULT_POLICIES:
            raise ValueError(f"no default policy for signal: {signal}")
        return DEFAULT_POLICIES[signal]

    return ValidationPolicy(
        max_age_ns=int(raw["max_age_ns"]),
        max_disagreement=float(raw["max_disagreement"]),
        min_sources_for_agreement=int(raw.get("min_sources_for_agreement", 2)),
        accepted_timing_provenance=tuple(
            raw.get(
                "accepted_timing_provenance",
                ("per_sample_monotonic", "per_frame_monotonic"),
            )
        ),
    )


def evaluate_episode(episode: dict[str, Any]) -> dict[str, Any]:
    episode_id = str(episode["episode_id"])
    observations = [_observation(item) for item in episode.get("observations", [])]

    grouped: dict[str, list[Observation]] = {}
    for obs in observations:
        grouped.setdefault(obs.signal, []).append(obs)

    reports: dict[str, Any] = {}
    expected = episode.get("expected", {})
    policy_overrides = episode.get("policies", {})

    for signal in sorted(grouped):
        report = validate_signal(grouped[signal], _policy(signal, policy_overrides.get(signal)))
        report_dict = asdict(report)
        report_dict["source_count"] = report.source_count
        report_dict["expected"] = expected.get(signal)
        report_dict["expectation_met"] = (
            expected.get(signal) is None or report.agreement == expected.get(signal)
        )
        reports[signal] = report_dict

    missing_expected = sorted(set(expected) - set(reports))
    passed = all(item["expectation_met"] for item in reports.values()) and not missing_expected

    return {
        "episode_id": episode_id,
        "passed": passed,
        "missing_expected_signals": missing_expected,
        "reports": reports,
    }


def evaluate_corpus(corpus: dict[str, Any]) -> dict[str, Any]:
    episodes = [evaluate_episode(episode) for episode in corpus.get("episodes", [])]
    return {
        "schema_version": corpus.get("schema_version", 1),
        "episode_count": len(episodes),
        "passed_count": sum(1 for episode in episodes if episode["passed"]),
        "failed_count": sum(1 for episode in episodes if not episode["passed"]),
        "passed": all(episode["passed"] for episode in episodes),
        "episodes": episodes,
    }


def load_and_evaluate(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return evaluate_corpus(json.load(handle))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate a read-only cross-source BMW observation corpus")
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = load_and_evaluate(args.corpus)
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)

    raise SystemExit(0 if result["passed"] else 1)
