from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ALLOWED_TIMING_PROVENANCE = {
    "per_sample_monotonic",
    "per_frame_monotonic",
    "diagnostic_response_time",
    "usb_batch_wall_clock",
    "unknown",
}


@dataclass(frozen=True)
class SourceSpec:
    source: str
    clock_domain: str
    timing_provenance: str
    calibration_version: str
    decoder_version: str


def _require_int(raw: dict[str, Any], name: str) -> int:
    if name not in raw:
        raise ValueError(f"missing required field: {name}")
    return int(raw[name])


def _source_spec(raw: dict[str, Any]) -> SourceSpec:
    timing = str(raw.get("timing_provenance", "unknown"))
    if timing not in ALLOWED_TIMING_PROVENANCE:
        raise ValueError(f"unsupported timing provenance: {timing}")
    return SourceSpec(
        source=str(raw["source"]),
        clock_domain=str(raw["clock_domain"]),
        timing_provenance=timing,
        calibration_version=str(raw.get("calibration_version", "UNSPECIFIED")),
        decoder_version=str(raw.get("decoder_version", "UNSPECIFIED")),
    )


def normalize_record(raw: dict[str, Any], spec: SourceSpec) -> dict[str, Any]:
    if str(raw.get("source", spec.source)) != spec.source:
        raise ValueError("record source does not match source spec")

    signal = str(raw["signal"])
    unit = str(raw["unit"])
    validity = str(raw.get("validity", "VALID"))
    value = raw.get("value")

    sample_time_ns = raw.get("sample_time_ns")
    if sample_time_ns is not None:
        sample_time_ns = int(sample_time_ns)

    receive_time_ns = _require_int(raw, "receive_time_ns")

    return {
        "signal": signal,
        "source": spec.source,
        "value": None if value is None else float(value),
        "unit": unit,
        "sample_time_ns": sample_time_ns,
        "receive_time_ns": receive_time_ns,
        "validity": validity,
        "confidence": float(raw.get("confidence", 1.0)),
        "timing_provenance": spec.timing_provenance,
        "provenance": {
            "clock_domain": spec.clock_domain,
            "calibration_version": spec.calibration_version,
            "decoder_version": spec.decoder_version,
            "capture_id": str(raw.get("capture_id", "UNSPECIFIED")),
        },
    }


def build_episode(
    *,
    episode_id: str,
    source_streams: Iterable[dict[str, Any]],
    expected: dict[str, str] | None = None,
    policies: dict[str, Any] | None = None,
) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    source_manifest: dict[str, Any] = {}

    for stream in source_streams:
        spec = _source_spec(stream["source_spec"])
        if spec.source in source_manifest:
            raise ValueError(f"duplicate source spec: {spec.source}")

        source_manifest[spec.source] = {
            "clock_domain": spec.clock_domain,
            "timing_provenance": spec.timing_provenance,
            "calibration_version": spec.calibration_version,
            "decoder_version": spec.decoder_version,
        }

        for raw in stream.get("records", []):
            observations.append(normalize_record(raw, spec))

    observations.sort(key=lambda item: (item["receive_time_ns"], item["source"], item["signal"]))

    return {
        "episode_id": str(episode_id),
        "source_manifest": source_manifest,
        "expected": expected or {},
        "policies": policies or {},
        "observations": observations,
    }


def import_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    episodes = []
    for raw_episode in bundle.get("episodes", []):
        episodes.append(
            build_episode(
                episode_id=str(raw_episode["episode_id"]),
                source_streams=raw_episode.get("sources", []),
                expected=raw_episode.get("expected"),
                policies=raw_episode.get("policies"),
            )
        )

    return {
        "schema_version": 1,
        "import_provenance": {
            "bundle_schema_version": bundle.get("schema_version", 1),
            "mode": "read_only_observation_import",
        },
        "episodes": episodes,
    }


def load_bundle(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Normalize read-only M1 observation bundles into the corpus schema")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = import_bundle(load_bundle(args.bundle))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
