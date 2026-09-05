from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import Iterable, Optional


VALID_STATES = {"VALID", "UNKNOWN", "INVALID", "STALE"}


@dataclass(frozen=True)
class Observation:
    signal: str
    source: str
    value: Optional[float]
    unit: str
    sample_time_ns: Optional[int]
    receive_time_ns: int
    validity: str = "VALID"
    confidence: float = 1.0
    timing_provenance: str = "per_sample_monotonic"

    @property
    def age_ns(self) -> Optional[int]:
        if self.sample_time_ns is None:
            return None
        return max(0, self.receive_time_ns - self.sample_time_ns)


@dataclass
class CrossSourceReport:
    signal: str
    usable_sources: list[str] = field(default_factory=list)
    excluded_sources: dict[str, str] = field(default_factory=dict)
    median_value: Optional[float] = None
    max_pairwise_disagreement: Optional[float] = None
    agreement: str = "UNKNOWN"
    notes: list[str] = field(default_factory=list)

    @property
    def source_count(self) -> int:
        return len(self.usable_sources)


@dataclass(frozen=True)
class ValidationPolicy:
    max_age_ns: int
    max_disagreement: float
    min_sources_for_agreement: int = 2
    accepted_timing_provenance: tuple[str, ...] = ("per_sample_monotonic", "per_frame_monotonic")


def _exclude_reason(obs: Observation, policy: ValidationPolicy) -> Optional[str]:
    if obs.validity not in VALID_STATES:
        return "invalid validity token"
    if obs.validity != "VALID":
        return obs.validity.lower()
    if obs.value is None:
        return "missing value"
    if not 0.0 <= obs.confidence <= 1.0:
        return "confidence outside [0,1]"
    if obs.sample_time_ns is None:
        return "missing per-sample timestamp"
    if obs.timing_provenance not in policy.accepted_timing_provenance:
        return "untrusted timing provenance"
    if obs.age_ns is not None and obs.age_ns > policy.max_age_ns:
        return "stale by policy"
    return None


def validate_signal(
    observations: Iterable[Observation],
    policy: ValidationPolicy,
) -> CrossSourceReport:
    observations = list(observations)
    if not observations:
        return CrossSourceReport(signal="UNKNOWN", notes=["no observations supplied"])

    signal = observations[0].signal
    report = CrossSourceReport(signal=signal)

    units = {obs.unit for obs in observations}
    signals = {obs.signal for obs in observations}
    if len(signals) != 1:
        report.agreement = "REJECTED"
        report.notes.append("mixed signals supplied")
        return report
    if len(units) != 1:
        report.agreement = "REJECTED"
        report.notes.append("mixed units supplied; convert before comparison")
        return report

    usable: list[Observation] = []
    for obs in observations:
        reason = _exclude_reason(obs, policy)
        if reason is not None:
            report.excluded_sources[obs.source] = reason
            continue
        usable.append(obs)
        report.usable_sources.append(obs.source)

    if not usable:
        report.agreement = "UNKNOWN"
        report.notes.append("no trustworthy fresh observations")
        return report

    values = [float(obs.value) for obs in usable if obs.value is not None]
    report.median_value = median(values)

    if len(values) == 1:
        report.agreement = "SINGLE_SOURCE"
        report.notes.append("value is observable but not independently corroborated")
        return report

    disagreements = [abs(a - b) for i, a in enumerate(values) for b in values[i + 1 :]]
    # Normalize binary floating-point noise at the evidence/report boundary.
    report.max_pairwise_disagreement = round(max(disagreements), 12) if disagreements else 0.0

    if len(values) < policy.min_sources_for_agreement:
        report.agreement = "INSUFFICIENT_SOURCES"
    elif report.max_pairwise_disagreement <= policy.max_disagreement:
        report.agreement = "AGREE"
    else:
        report.agreement = "DISAGREE"
        report.notes.append("cross-source disagreement exceeds policy threshold")

    return report
