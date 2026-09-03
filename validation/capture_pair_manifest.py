"""Bind two canonical capture documents to one audited physical session."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any


SYNC_METHODS = {"SHARED_CLOCK", "HARDWARE_TRIGGER", "OBSERVED_MARKER", "MANUAL_ASSERTION"}
VERIFIED_SYNC_METHODS = {"SHARED_CLOCK", "HARDWARE_TRIGGER", "OBSERVED_MARKER"}


class CapturePairManifestError(ValueError):
    pass


def capture_document_sha256(document: dict[str, Any]) -> str:
    if not isinstance(document, dict):
        raise CapturePairManifestError("capture document must be an object")
    canonical = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class CapturePairManifest:
    pair_id: str
    session_id: str
    transport: str
    logical_bus: str
    physical_tap: str
    reference_capture_id: str
    reference_document_sha256: str
    candidate_capture_id: str
    candidate_document_sha256: str
    same_physical_interval: bool
    sync_method: str
    sync_evidence: str
    schema_version: int = 1
    mode: str = "offline_capture_pair_manifest"
    actuation_authority: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "CapturePairManifest":
        if not isinstance(raw, dict):
            raise CapturePairManifestError("capture-pair manifest must be an object")
        expected = {item.name for item in fields(cls)}
        missing = sorted(expected - set(raw))
        unknown = sorted(set(raw) - expected)
        if missing:
            raise CapturePairManifestError(f"capture-pair manifest missing fields: {', '.join(missing)}")
        if unknown:
            raise CapturePairManifestError(f"capture-pair manifest contains unknown fields: {', '.join(unknown)}")
        manifest = cls(**raw)
        manifest.validate()
        return manifest

    @property
    def sync_quality(self) -> str:
        if not self.same_physical_interval:
            return "NOT_SAME_INTERVAL"
        if self.sync_method in VERIFIED_SYNC_METHODS:
            return "VERIFIED"
        return "DECLARED_ONLY"

    def validate(self) -> None:
        if self.schema_version != 1 or self.mode != "offline_capture_pair_manifest":
            raise CapturePairManifestError("unsupported capture-pair schema or mode")
        if self.actuation_authority != "NONE":
            raise CapturePairManifestError("capture-pair manifest cannot grant actuation authority")
        if self.transport != "CAN":
            raise CapturePairManifestError("capture-pair transport must be CAN")
        for name in (
            "pair_id", "session_id", "logical_bus", "physical_tap",
            "reference_capture_id", "candidate_capture_id", "sync_evidence",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise CapturePairManifestError(f"{name} must be a non-empty string")
        if self.reference_capture_id == self.candidate_capture_id:
            raise CapturePairManifestError("reference and candidate capture IDs must differ")
        for name in ("reference_document_sha256", "candidate_document_sha256"):
            value = getattr(self, name)
            if not isinstance(value, str) or len(value) != 64:
                raise CapturePairManifestError(f"{name} must be a SHA-256 hex digest")
            try:
                bytes.fromhex(value)
            except ValueError as exc:
                raise CapturePairManifestError(f"{name} must be a SHA-256 hex digest") from exc
        if not isinstance(self.same_physical_interval, bool):
            raise CapturePairManifestError("same_physical_interval must be boolean")
        if self.sync_method not in SYNC_METHODS:
            raise CapturePairManifestError("unsupported sync_method")

    def validate_against(
        self, reference: dict[str, Any], candidate: dict[str, Any]
    ) -> None:
        self.validate()
        if reference.get("capture_id") != self.reference_capture_id:
            raise CapturePairManifestError("reference capture_id does not match pair manifest")
        if candidate.get("capture_id") != self.candidate_capture_id:
            raise CapturePairManifestError("candidate capture_id does not match pair manifest")
        if capture_document_sha256(reference) != self.reference_document_sha256:
            raise CapturePairManifestError("reference capture content hash does not match pair manifest")
        if capture_document_sha256(candidate) != self.candidate_document_sha256:
            raise CapturePairManifestError("candidate capture content hash does not match pair manifest")
        if self.sync_method == "SHARED_CLOCK" and reference.get("clock_domain") != candidate.get("clock_domain"):
            raise CapturePairManifestError("SHARED_CLOCK requires equal capture clock_domain values")


def build_capture_pair_manifest(
    reference: dict[str, Any],
    candidate: dict[str, Any],
    *,
    pair_id: str,
    session_id: str,
    logical_bus: str,
    physical_tap: str,
    same_physical_interval: bool,
    sync_method: str,
    sync_evidence: str,
) -> CapturePairManifest:
    manifest = CapturePairManifest(
        pair_id=pair_id,
        session_id=session_id,
        transport="CAN",
        logical_bus=logical_bus,
        physical_tap=physical_tap,
        reference_capture_id=reference.get("capture_id"),
        reference_document_sha256=capture_document_sha256(reference),
        candidate_capture_id=candidate.get("capture_id"),
        candidate_document_sha256=capture_document_sha256(candidate),
        same_physical_interval=same_physical_interval,
        sync_method=sync_method,
        sync_evidence=sync_evidence,
    )
    manifest.validate_against(reference, candidate)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Bind two canonical CAN captures to one audited session")
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--pair-id", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--logical-bus", required=True)
    parser.add_argument("--physical-tap", required=True)
    parser.add_argument("--same-physical-interval", action="store_true", required=True)
    parser.add_argument("--sync-method", choices=tuple(sorted(SYNC_METHODS)), required=True)
    parser.add_argument("--sync-evidence", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    manifest = build_capture_pair_manifest(
        reference,
        candidate,
        pair_id=args.pair_id,
        session_id=args.session_id,
        logical_bus=args.logical_bus,
        physical_tap=args.physical_tap,
        same_physical_interval=args.same_physical_interval,
        sync_method=args.sync_method,
        sync_evidence=args.sync_evidence,
    )
    args.output.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
