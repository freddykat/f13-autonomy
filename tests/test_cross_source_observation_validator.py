from validation.cross_source_observation_validator import (
    Observation,
    ValidationPolicy,
    validate_signal,
)


POLICY = ValidationPolicy(max_age_ns=100_000_000, max_disagreement=0.5)


def obs(source, value, *, t=1_000_000_000, recv=1_050_000_000, validity="VALID", provenance="per_sample_monotonic"):
    return Observation(
        signal="yaw_rate",
        source=source,
        value=value,
        unit="deg/s",
        sample_time_ns=t,
        receive_time_ns=recv,
        validity=validity,
        timing_provenance=provenance,
    )


def test_two_independent_fresh_sources_agree():
    report = validate_signal([obs("flexray", 12.0), obs("imu", 12.3)], POLICY)

    assert report.agreement == "AGREE"
    assert report.source_count == 2
    assert report.max_pairwise_disagreement == 0.3


def test_disagreement_is_explicit_not_averaged_away():
    report = validate_signal([obs("flexray", 12.0), obs("imu", 14.0)], POLICY)

    assert report.agreement == "DISAGREE"
    assert report.max_pairwise_disagreement == 2.0


def test_stale_source_is_excluded():
    report = validate_signal([
        obs("flexray", 12.0, t=0, recv=500_000_000),
        obs("imu", 12.1),
    ], POLICY)

    assert report.agreement == "SINGLE_SOURCE"
    assert report.excluded_sources["flexray"] == "stale by policy"


def test_unknown_does_not_become_zero():
    report = validate_signal([
        obs("flexray", None, validity="UNKNOWN"),
        obs("imu", 3.0),
    ], POLICY)

    assert report.agreement == "SINGLE_SOURCE"
    assert report.median_value == 3.0
    assert report.excluded_sources["flexray"] == "unknown"


def test_batch_wall_clock_is_not_accepted_as_sample_timing():
    report = validate_signal([
        obs("flexray", 12.0, provenance="usb_batch_wall_clock"),
        obs("imu", 12.1),
    ], POLICY)

    assert report.agreement == "SINGLE_SOURCE"
    assert report.excluded_sources["flexray"] == "untrusted timing provenance"


def test_mixed_units_are_rejected_before_comparison():
    a = obs("flexray", 12.0)
    b = Observation(
        signal="yaw_rate",
        source="enet",
        value=0.2,
        unit="rad/s",
        sample_time_ns=1_000_000_000,
        receive_time_ns=1_050_000_000,
    )

    report = validate_signal([a, b], POLICY)

    assert report.agreement == "REJECTED"
    assert "mixed units" in report.notes[0]
