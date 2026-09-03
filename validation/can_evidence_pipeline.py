"""Run the Beta-0 CAN evidence path as one deterministic offline operation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from validation.can_trace_compare import compare_can_captures
from validation.capture_pair_manifest import build_capture_pair_manifest
from validation.capture_quality_evaluator import evaluate_can_capture
from validation.offline_can_decoder import decode_capture


PAIR_SPEC_FIELDS = {
    "pair_id",
    "session_id",
    "logical_bus",
    "physical_tap",
    "same_physical_interval",
    "sync_method",
    "sync_evidence",
    "reference_channel_map",
    "candidate_channel_map",
    "reference_quality_evidence",
}


class CanEvidencePipelineError(ValueError):
    pass


def _validate_pair_spec(spec: dict[str, Any]) -> None:
    if not isinstance(spec, dict):
        raise CanEvidencePipelineError("pair spec must be an object")
    missing = sorted(PAIR_SPEC_FIELDS - set(spec))
    unknown = sorted(set(spec) - PAIR_SPEC_FIELDS)
    if missing:
        raise CanEvidencePipelineError(f"pair spec missing fields: {', '.join(missing)}")
    if unknown:
        raise CanEvidencePipelineError(f"pair spec contains unknown fields: {', '.join(unknown)}")
    for name in ("reference_channel_map", "candidate_channel_map"):
        if not isinstance(spec[name], dict):
            raise CanEvidencePipelineError(f"{name} must be an object")
    if spec["reference_quality_evidence"] is not None and not isinstance(
        spec["reference_quality_evidence"], dict
    ):
        raise CanEvidencePipelineError("reference_quality_evidence must be an object or null")


def _verdict(frame_fidelity: str, capture_quality: str) -> str:
    if frame_fidelity == "MISMATCH" or capture_quality == "LOSSY":
        return "REJECTED"
    if frame_fidelity == "EXACT" and capture_quality == "FULL_RATE_CANDIDATE":
        return "READY_FOR_REPLAY_REVIEW"
    return "OBSERVATION_ONLY"


def run_can_evidence_pipeline(
    reference: dict[str, Any],
    candidate: dict[str, Any],
    decoder_manifest: dict[str, Any],
    pair_spec: dict[str, Any],
    *,
    vehicle_profile: str,
) -> dict[str, Any]:
    _validate_pair_spec(pair_spec)
    pair = build_capture_pair_manifest(
        reference,
        candidate,
        pair_id=pair_spec["pair_id"],
        session_id=pair_spec["session_id"],
        logical_bus=pair_spec["logical_bus"],
        physical_tap=pair_spec["physical_tap"],
        same_physical_interval=pair_spec["same_physical_interval"],
        sync_method=pair_spec["sync_method"],
        sync_evidence=pair_spec["sync_evidence"],
    )
    comparison = compare_can_captures(
        reference,
        candidate,
        pair_manifest=pair,
        reference_channel_map=pair_spec["reference_channel_map"],
        candidate_channel_map=pair_spec["candidate_channel_map"],
        reference_quality_evidence=pair_spec["reference_quality_evidence"],
    )
    quality = evaluate_can_capture(candidate, reference_comparison=comparison)
    decoded = decode_capture(
        candidate,
        decoder_manifest,
        vehicle_profile=vehicle_profile,
        reference_comparison=comparison,
    )
    verdict = _verdict(comparison.frame_fidelity, quality.evaluated_quality)
    return {
        "schema_version": 1,
        "mode": "offline_can_evidence_pipeline",
        "beta_stage": "BETA_0_OFFLINE_REPLAY",
        "verdict": verdict,
        "summary": {
            "frame_fidelity": comparison.frame_fidelity,
            "timing_fidelity": comparison.timing_fidelity,
            "capture_quality": quality.evaluated_quality,
            "observation_count": decoded["observation_count"],
        },
        "capture_pair_manifest": pair.to_dict(),
        "comparison": comparison.to_dict(),
        "capture_quality_evaluation": quality.to_dict(),
        "decoded_observations": decoded,
        "actuation_authority": "NONE",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the complete Beta-0 CAN evidence pipeline offline"
    )
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("decoder_manifest", type=Path)
    parser.add_argument("pair_spec", type=Path)
    parser.add_argument("--vehicle-profile", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    load = lambda path: json.loads(path.read_text(encoding="utf-8"))
    report = run_can_evidence_pipeline(
        load(args.reference),
        load(args.candidate),
        load(args.decoder_manifest),
        load(args.pair_spec),
        vehicle_profile=args.vehicle_profile,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
