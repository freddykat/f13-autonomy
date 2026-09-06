#!/usr/bin/env python3
"""Validate and summarize the BMW actuator research matrix.

This tool is intentionally non-actuating. It validates that every control
research domain stays inside the current SHADOW/HIL boundary and has explicit
feedback/override requirements before any future actuator work is considered.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ALLOWED_STAGES = {"DISABLED", "SHADOW", "HIL_ONLY"}
FORBIDDEN_KEYS = {
    "can_id",
    "arbitration_id",
    "slot_id",
    "frame_id",
    "payload",
    "checksum",
    "alive_counter",
    "sendcan",
    "tx_message",
    "diagnostic_write",
    "panda_safety_bypass",
}


@dataclass(frozen=True)
class DomainResearchSummary:
    domain: str
    current_stage: str
    feedback_count: int
    override_count: int
    research_event_count: int
    transport_confirmed: bool
    tx_allowed: bool
    ready_for_passive_research: bool
    ready_for_hil_design: bool
    live_actuation_allowed: bool
    status: str = "CONTROL_RESEARCH_ONLY"


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("domains"), list):
        raise ValueError("manifest must contain a domains list")
    return payload


def _walk_forbidden_keys(value: Any, path: str = "root") -> list[str]:
    violations: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                violations.append(f"{path}.{key}")
            violations.extend(_walk_forbidden_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            violations.extend(_walk_forbidden_keys(child, f"{path}[{index}]"))
    return violations


def validate_manifest(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if payload.get("live_transmit") is not False:
        errors.append("live_transmit must remain false")
    if payload.get("auto_promote") is not False:
        errors.append("auto_promote must remain false")

    forbidden = _walk_forbidden_keys(payload)
    if forbidden:
        errors.append("forbidden low-level control fields present: " + ", ".join(forbidden))

    seen_domains: set[str] = set()
    for index, domain in enumerate(payload["domains"]):
        prefix = f"domains[{index}]"
        name = str(domain.get("domain", ""))
        if not name:
            errors.append(f"{prefix}: domain is required")
            continue
        if name in seen_domains:
            errors.append(f"{prefix}: duplicate domain {name}")
        seen_domains.add(name)

        stage = domain.get("current_stage")
        if stage not in ALLOWED_STAGES:
            errors.append(f"{prefix}: unsupported current_stage {stage!r}")

        if domain.get("tx_allowed") is not False:
            errors.append(f"{prefix}: tx_allowed must remain false")

        if domain.get("transport_confirmed") not in {False, None}:
            errors.append(f"{prefix}: transport cannot be marked confirmed pre-validation")

        feedback = domain.get("required_feedback")
        overrides = domain.get("driver_override")
        events = domain.get("research_events")

        if not isinstance(feedback, list) or not feedback:
            errors.append(f"{prefix}: required_feedback must be non-empty")
        if not isinstance(overrides, list) or not overrides:
            errors.append(f"{prefix}: driver_override must be non-empty")
        if not isinstance(events, list) or not events:
            errors.append(f"{prefix}: research_events must be non-empty")

    return errors


def summarize_manifest(payload: dict[str, Any]) -> list[DomainResearchSummary]:
    errors = validate_manifest(payload)
    if errors:
        raise ValueError("; ".join(errors))

    summaries: list[DomainResearchSummary] = []
    for domain in payload["domains"]:
        feedback = list(domain["required_feedback"])
        overrides = list(domain["driver_override"])
        events = list(domain["research_events"])
        stage = str(domain["current_stage"])

        passive_ready = bool(feedback and overrides and events)
        hil_ready = (
            passive_ready
            and stage == "HIL_ONLY"
            and domain.get("transport_confirmed") is True
        )

        summaries.append(DomainResearchSummary(
            domain=str(domain["domain"]),
            current_stage=stage,
            feedback_count=len(feedback),
            override_count=len(overrides),
            research_event_count=len(events),
            transport_confirmed=bool(domain.get("transport_confirmed", False)),
            tx_allowed=False,
            ready_for_passive_research=passive_ready,
            ready_for_hil_design=hil_ready,
            live_actuation_allowed=False,
        ))

    return summaries


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate BMW actuator research matrix safety boundaries"
    )
    parser.add_argument(
        "manifest",
        type=Path,
        nargs="?",
        default=Path("validation/manifests/prototype_001_bmw_actuator_research.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = load_manifest(args.manifest)
    errors = validate_manifest(payload)
    result = {
        "mode": "CONTROL_RESEARCH_ONLY",
        "valid": not errors,
        "errors": errors,
        "live_transmit": False,
        "actuation_authority": "NONE",
        "domains": [] if errors else [asdict(item) for item in summarize_manifest(payload)],
    }
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
