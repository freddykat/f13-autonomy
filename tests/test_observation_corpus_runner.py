from validation.observation_corpus_runner import evaluate_corpus, evaluate_episode


def test_corpus_reports_expected_agreement_states():
    corpus = {
        "schema_version": 1,
        "episodes": [
            {
                "episode_id": "agree",
                "expected": {"yaw_rate": "AGREE"},
                "observations": [
                    {"signal":"yaw_rate","source":"flexray","value":5.0,"unit":"deg/s","sample_time_ns":1_000_000_000,"receive_time_ns":1_030_000_000},
                    {"signal":"yaw_rate","source":"imu","value":5.4,"unit":"deg/s","sample_time_ns":1_001_000_000,"receive_time_ns":1_030_000_000},
                ],
            }
        ],
    }

    result = evaluate_corpus(corpus)

    assert result["passed"] is True
    assert result["passed_count"] == 1
    assert result["episodes"][0]["reports"]["yaw_rate"]["agreement"] == "AGREE"


def test_batch_timing_source_is_excluded_from_corroboration():
    episode = {
        "episode_id": "batch",
        "expected": {"yaw_rate": "SINGLE_SOURCE"},
        "observations": [
            {"signal":"yaw_rate","source":"pico","value":4.0,"unit":"deg/s","sample_time_ns":2_000_000_000,"receive_time_ns":2_030_000_000,"timing_provenance":"usb_batch_wall_clock"},
            {"signal":"yaw_rate","source":"imu","value":4.1,"unit":"deg/s","sample_time_ns":2_001_000_000,"receive_time_ns":2_030_000_000},
        ],
    }

    result = evaluate_episode(episode)
    report = result["reports"]["yaw_rate"]

    assert result["passed"] is True
    assert report["agreement"] == "SINGLE_SOURCE"
    assert report["excluded_sources"]["pico"] == "untrusted timing provenance"


def test_missing_expected_signal_fails_episode():
    result = evaluate_episode(
        {
            "episode_id": "missing",
            "expected": {"vehicle_speed": "AGREE"},
            "observations": [],
        }
    )

    assert result["passed"] is False
    assert result["missing_expected_signals"] == ["vehicle_speed"]


def test_policy_override_can_be_stricter_than_default():
    episode = {
        "episode_id": "strict",
        "expected": {"vehicle_speed": "DISAGREE"},
        "policies": {
            "vehicle_speed": {"max_age_ns": 150_000_000, "max_disagreement": 0.1}
        },
        "observations": [
            {"signal":"vehicle_speed","source":"can","value":20.0,"unit":"m/s","sample_time_ns":3_000_000_000,"receive_time_ns":3_030_000_000},
            {"signal":"vehicle_speed","source":"gnss","value":20.2,"unit":"m/s","sample_time_ns":3_000_000_000,"receive_time_ns":3_030_000_000},
        ],
    }

    result = evaluate_episode(episode)

    assert result["passed"] is True
    assert result["reports"]["vehicle_speed"]["agreement"] == "DISAGREE"
