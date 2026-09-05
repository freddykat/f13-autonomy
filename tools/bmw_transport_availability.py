#!/usr/bin/env python3
"""Summarize passive BMW function availability across CAN and FlexRay.

This stage combines cross-session function evidence with optional synchronized
CAN<->FlexRay correspondence results. It answers a narrow engineering question:
which transport currently appears sufficient to observe each function?

It does not validate a decoder, prove gateway ownership, or authorize control.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FunctionTransportSummary:
    function_family: str
    availability: str
    can_evidence_score: float
    can_confidence: str
    can_source_key: str | None
    flexray_evidence_score: float
    flexray_confidence: str
    flexray_source_key: str | None
    best_correspondence_score: float
    correspondence_relationship: str
    gateway_hypothesis: str
    observation_path: str
    flexray_translation_need: str
    openpilot_read_path_status: str
    status: str = "UNVALIDATED_TRANSPORT_AVAILABILITY"


@dataclass(frozen=True)
class _Evidence:
    function_family: str
    transport: str
    source_key: str
    evidence_score: float
    confidence: str


@dataclass(frozen=True)
class _Correspondence:
    function_family: str
    can_source_key: str
    flexray_source_key: str
    correspondence_score: float
    relationship: str
    gateway_hypothesis: str


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_function_evidence(path: Path) -> list[_Evidence]:
    payload = _load_json(path)
    items = payload.get("evidence")
    if not isinstance(items, list):
        raise ValueError(f"{path}: missing evidence list")
    result: list[_Evidence] = []
    for item in items:
        result.append(_Evidence(
            function_family=str(item["function_family"]),
            transport=str(item["transport"]).upper(),
            source_key=str(item["source_key"]),
            evidence_score=float(item.get("evidence_score", 0.0)),
            confidence=str(item.get("confidence", "LOW")),
        ))
    return result


def load_correspondence(path: Path | None) -> list[_Correspondence]:
    if path is None:
        return []
    payload = _load_json(path)
    items = payload.get("correspondence")
    if not isinstance(items, list):
        raise ValueError(f"{path}: missing correspondence list")
    result: list[_Correspondence] = []
    for item in items:
        result.append(_Correspondence(
            function_family=str(item["function_family"]),
            can_source_key=str(item["can_source_key"]),
            flexray_source_key=str(item["flexray_source_key"]),
            correspondence_score=float(item.get("correspondence_score", 0.0)),
            relationship=str(item.get("relationship", "WEAK_OR_UNRELATED")),
            gateway_hypothesis=str(item.get("gateway_hypothesis", "NOT_INFERRED")),
        ))
    return result


def _best(items: list[_Evidence]) -> _Evidence | None:
    if not items:
        return None
    return max(items, key=lambda item: item.evidence_score)


def _best_correspondence(items: list[_Correspondence]) -> _Correspondence | None:
    if not items:
        return None
    return max(items, key=lambda item: item.correspondence_score)


def _is_usable_evidence(item: _Evidence | None, minimum_score: float) -> bool:
    return item is not None and item.evidence_score >= minimum_score and item.confidence in {"MEDIUM", "HIGH"}


def summarize_transport_availability(
    evidence: list[_Evidence],
    correspondence: list[_Correspondence],
    *,
    minimum_evidence_score: float = 0.65,
) -> list[FunctionTransportSummary]:
    families = sorted({item.function_family for item in evidence})
    summaries: list[FunctionTransportSummary] = []

    for family in families:
        can = _best([
            item for item in evidence
            if item.function_family == family and item.transport == "CAN"
        ])
        flexray = _best([
            item for item in evidence
            if item.function_family == family and item.transport == "FLEXRAY"
        ])
        can_ok = _is_usable_evidence(can, minimum_evidence_score)
        flex_ok = _is_usable_evidence(flexray, minimum_evidence_score)

        corr = _best_correspondence([
            item for item in correspondence
            if item.function_family == family
            and (can is None or item.can_source_key == can.source_key)
            and (flexray is None or item.flexray_source_key == flexray.source_key)
        ])

        corr_relationship = corr.relationship if corr else "NO_CORRESPONDENCE_EVIDENCE"
        corr_score = corr.correspondence_score if corr else 0.0
        gateway_hypothesis = corr.gateway_hypothesis if corr else "NOT_INFERRED"

        if can_ok and not flex_ok:
            availability = "CAN_EVIDENCE_ONLY"
            observation_path = "CAN_FIRST"
            flexray_need = "NOT_INDICATED_BY_CURRENT_EVIDENCE"
        elif flex_ok and not can_ok:
            availability = "FLEXRAY_EVIDENCE_ONLY"
            observation_path = "FLEXRAY_REQUIRED_FOR_OBSERVATION"
            flexray_need = "LIKELY_REQUIRED_FOR_THIS_FUNCTION"
        elif can_ok and flex_ok:
            if corr and corr.relationship == "STRONG_DUAL_TRANSPORT_CORRESPONDENCE":
                availability = "DUAL_TRANSPORT_CORRELATED"
                observation_path = "CAN_MAY_SUFFICE_PENDING_DECODER_VALIDATION"
                flexray_need = "POSSIBLY_OPTIONAL_FOR_RUNTIME_OBSERVATION"
            else:
                availability = "DUAL_TRANSPORT_UNRESOLVED"
                observation_path = "CAPTURE_BOTH_UNTIL_CORROBORATED"
                flexray_need = "UNRESOLVED"
        else:
            availability = "INSUFFICIENT_EVIDENCE"
            observation_path = "CAPTURE_BOTH_WHERE_AVAILABLE"
            flexray_need = "UNRESOLVED"

        summaries.append(FunctionTransportSummary(
            function_family=family,
            availability=availability,
            can_evidence_score=can.evidence_score if can else 0.0,
            can_confidence=can.confidence if can else "NONE",
            can_source_key=can.source_key if can else None,
            flexray_evidence_score=flexray.evidence_score if flexray else 0.0,
            flexray_confidence=flexray.confidence if flexray else "NONE",
            flexray_source_key=flexray.source_key if flexray else None,
            best_correspondence_score=corr_score,
            correspondence_relationship=corr_relationship,
            gateway_hypothesis=gateway_hypothesis,
            observation_path=observation_path,
            flexray_translation_need=flexray_need,
            openpilot_read_path_status="TRANSPORT_CANDIDATE_ONLY_NOT_DECODER_VALIDATED",
        ))

    summaries.sort(key=lambda item: (
        item.availability,
        item.function_family,
    ))
    return summaries


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize passive BMW function availability on CAN and FlexRay"
    )
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--correspondence", type=Path)
    parser.add_argument("--minimum-evidence-score", type=float, default=0.65)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    summaries = summarize_transport_availability(
        load_function_evidence(args.evidence),
        load_correspondence(args.correspondence),
        minimum_evidence_score=args.minimum_evidence_score,
    )
    payload = {
        "mode": "OFFLINE_READ_ONLY_TRANSPORT_AVAILABILITY",
        "status": "UNVALIDATED_TRANSPORT_AVAILABILITY",
        "decoder_validated": False,
        "gateway_derivation_proven": False,
        "auto_promote": False,
        "diagnostic_writes": False,
        "transmit": False,
        "actuation_authority": "NONE",
        "functions": [asdict(item) for item in summaries],
    }
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
