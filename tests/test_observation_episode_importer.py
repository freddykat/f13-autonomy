import pytest

from validation.observation_episode_importer import build_episode, import_bundle
from validation.observation_corpus_runner import evaluate_episode


def test_importer_preserves_clock_and_decoder_provenance():
    episode = build_episode(
        episode_id="e1",
        source_streams=[
            {
                "source_spec": {
                    "source": "imu",
                    "clock_domain": "host_monotonic",
                    "timing_provenance": "per_sample_monotonic",
                    "calibration_version": "imu-cal-v2",
                    "decoder_version": "raw-si-v1",
                },
                "records": [
                    {
                        "signal": "yaw_rate",
                        "value": 3.2,
                        "unit": "deg/s",
                        "sample_time_ns": 1_000_000_000,
                        "receive_time_ns": 1_010_000_000,
                        "capture_id": "drive-001",
                    }
                ],
            }
        ],
    )

    obs = episode["observations"][0]
    assert obs["provenance"]["clock_domain"] == "host_monotonic"
    assert obs["provenance"]["calibration_version"] == "imu-cal-v2"
    assert obs["provenance"]["decoder_version"] == "raw-si-v1"
    assert obs["provenance"]["capture_id"] == "drive-001"


def test_diagnostic_response_time_is_not_promoted_as_tight_timing():
    episode = build_episode(
        episode_id="e2",
        expected={"yaw_rate": "SINGLE_SOURCE"},
        source_streams=[
            {
                "source_spec": {
                    "source": "enet_icm",
                    "clock_domain": "host_monotonic",
                    "timing_provenance": "diagnostic_response_time",
                    "calibration_version": "none",
                    "decoder_version": "job-v1",
                },
                "records": [
                    {
                        "signal": "yaw_rate",
                        "value": 5.0,
                        "unit": "deg/s",
                        "sample_time_ns": 2_000_000_000,
                        "receive_time_ns": 2_020_000_000,
                    }
                ],
            },
            {
                "source_spec": {
                    "source": "imu",
                    "clock_domain": "host_monotonic",
                    "timing_provenance": "per_sample_monotonic",
                    "calibration_version": "imu-v1",
                    "decoder_version": "raw-v1",
                },
                "records": [
                    {
                        "signal": "yaw_rate",
                        "value": 5.1,
                        "unit": "deg/s",
                        "sample_time_ns": 2_001_000_000,
                        "receive_time_ns": 2_020_000_000,
                    }
                ],
            },
        ],
    )

    report = evaluate_episode(episode)["reports"]["yaw_rate"]
    assert report["agreement"] == "SINGLE_SOURCE"
    assert report["excluded_sources"]["enet_icm"] == "untrusted timing provenance"


def test_duplicate_source_specs_are_rejected():
    with pytest.raises(ValueError, match="duplicate source spec"):
        build_episode(
            episode_id="dup",
            source_streams=[
                {"source_spec": {"source": "can", "clock_domain": "c1", "timing_provenance": "per_frame_monotonic"}},
                {"source_spec": {"source": "can", "clock_domain": "c2", "timing_provenance": "per_frame_monotonic"}},
            ],
        )


def test_unknown_timing_provenance_is_preserved_not_invented():
    corpus = import_bundle(
        {
            "schema_version": 1,
            "episodes": [
                {
                    "episode_id": "unknown-clock",
                    "sources": [
                        {
                            "source_spec": {
                                "source": "legacy_log",
                                "clock_domain": "unknown",
                                "timing_provenance": "unknown",
                            },
                            "records": [
                                {
                                    "signal": "vehicle_speed",
                                    "value": 12.0,
                                    "unit": "m/s",
                                    "receive_time_ns": 3_000_000_000,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    )

    obs = corpus["episodes"][0]["observations"][0]
    assert obs["sample_time_ns"] is None
    assert obs["timing_provenance"] == "unknown"
