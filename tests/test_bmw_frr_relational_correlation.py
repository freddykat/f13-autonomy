from tools.bmw_continuous_signal_correlation import ContinuousCandidate
from tools.bmw_frr_relational_correlation import rank_frr_relational_candidates


def c(event, delta, *, bus="can0", address=0x123, start=2, score=0.9):
    return ContinuousCandidate(
        event=event,
        bus=bus,
        address=address,
        start_byte=start,
        width=2,
        signed=False,
        endian="big",
        score=score,
        observations=3,
        mean_delta=delta,
        sign_consistency=1.0,
        direction_match=1.0,
    )


def test_distance_like_candidate_scores_high_across_closing_opening_steady_loss():
    ranked = rank_frr_relational_candidates([
        c("LEAD_CLOSING", -30.0),
        c("LEAD_OPENING", 28.0),
        c("LEAD_STEADY", 1.0),
        c("LEAD_LOSS", 35.0),
    ])
    assert ranked
    top = ranked[0]
    assert top.opposite_direction_score == 1.0
    assert top.steady_score > 0.9
    assert top.loss_transition_score == 1.0
    assert top.score > 0.85


def test_same_direction_closing_opening_is_penalized():
    good = rank_frr_relational_candidates([
        c("LEAD_CLOSING", -20.0, start=1),
        c("LEAD_OPENING", 20.0, start=1),
    ])[0]
    bad = rank_frr_relational_candidates([
        c("LEAD_CLOSING", 20.0, start=3),
        c("LEAD_OPENING", 15.0, start=3),
    ])[0]
    assert good.score > bad.score
    assert bad.opposite_direction_score == 0.0


def test_steady_motion_penalizes_candidate_that_keeps_moving():
    stable = rank_frr_relational_candidates([
        c("LEAD_CLOSING", -20.0, start=0),
        c("LEAD_OPENING", 20.0, start=0),
        c("LEAD_STEADY", 1.0, start=0),
    ])[0]
    drifting = rank_frr_relational_candidates([
        c("LEAD_CLOSING", -20.0, start=4),
        c("LEAD_OPENING", 20.0, start=4),
        c("LEAD_STEADY", 18.0, start=4),
    ])[0]
    assert stable.score > drifting.score


def test_bus_identity_is_not_collapsed():
    ranked = rank_frr_relational_candidates([
        c("LEAD_CLOSING", -10.0, bus="can0"),
        c("LEAD_OPENING", 10.0, bus="can0"),
        c("LEAD_CLOSING", -11.0, bus="can1"),
        c("LEAD_OPENING", 11.0, bus="can1"),
    ])
    assert {x.bus for x in ranked} == {"can0", "can1"}


def test_no_decoder_or_control_authority_fields_exist():
    ranked = rank_frr_relational_candidates([
        c("LEAD_CLOSING", -10.0),
        c("LEAD_OPENING", 10.0),
    ])
    top = ranked[0]
    for forbidden in ("decoder", "scale", "unit", "command", "actuation", "sendcan"):
        assert not hasattr(top, forbidden)
