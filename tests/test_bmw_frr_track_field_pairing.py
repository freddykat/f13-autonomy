from tools.bmw_frr_track_field_pairing import RawField, rank_range_velocity_pairs
from tools.bmw_signal_correlation import Frame


def _frame(t, bus, address, values):
    return Frame(t=t, bus=bus, address=address, data=bytes(values))


def test_true_range_velocity_pair_ranks_high():
    frames = []
    ranges = [100, 96, 92, 88, 88, 88, 92, 96]
    vels = [-4, -4, -4, 0, 0, 4, 4, 4]
    for i, (r, v) in enumerate(zip(ranges, vels)):
        t = i * 0.1
        frames.append(_frame(t, "can0", 0x120, [r, 0]))
        frames.append(_frame(t + 0.01, "can0", 0x121, [v & 0xFF, 0]))
    rf = RawField("can0", 0x120, 0, 1, False, "big")
    vf = RawField("can0", 0x121, 0, 1, True, "big")
    ranked = rank_range_velocity_pairs(frames, [rf], [vf], max_pair_dt=0.06, min_samples=4)
    assert ranked
    assert ranked[0].derivative_sign_agreement >= 0.8
    assert ranked[0].correlation_abs >= 0.7
    assert ranked[0].score > 0.45


def test_incoherent_velocity_pair_scores_lower():
    frames = []
    ranges = [100, 96, 92, 88, 84, 80, 76, 72]
    true_vel = [-4] * 8
    noise_vel = [4, -4, 4, -4, 4, -4, 4, -4]
    for i, (r, tv, nv) in enumerate(zip(ranges, true_vel, noise_vel)):
        t = i * 0.1
        frames.append(_frame(t, "can0", 0x120, [r]))
        frames.append(_frame(t + 0.01, "can0", 0x121, [tv & 0xFF]))
        frames.append(_frame(t + 0.01, "can0", 0x122, [nv & 0xFF]))
    rf = RawField("can0", 0x120, 0, 1, False, "big")
    good = RawField("can0", 0x121, 0, 1, True, "big")
    bad = RawField("can0", 0x122, 0, 1, True, "big")
    ranked = rank_range_velocity_pairs(frames, [rf], [good, bad], max_pair_dt=0.06, min_samples=4)
    scores = {c.velocity_field.address: c.score for c in ranked}
    assert scores[0x121] > scores[0x122]


def test_inverse_sign_convention_is_allowed():
    frames = []
    ranges = [50, 45, 40, 35, 30, 25]
    inverse_vel = [5, 5, 5, 5, 5, 5]
    for i, (r, v) in enumerate(zip(ranges, inverse_vel)):
        t = i * 0.1
        frames.append(_frame(t, "can0", 0x130, [r]))
        frames.append(_frame(t + 0.01, "can0", 0x131, [v]))
    rf = RawField("can0", 0x130, 0, 1, False, "big")
    vf = RawField("can0", 0x131, 0, 1, False, "big")
    ranked = rank_range_velocity_pairs(frames, [rf], [vf], max_pair_dt=0.06, min_samples=4)
    assert ranked[0].derivative_sign_agreement == 1.0


def test_cross_bus_pair_is_allowed_but_penalized():
    frames = []
    ranges = [80, 76, 72, 68, 64, 60]
    vels = [-4] * 6
    for i, (r, v) in enumerate(zip(ranges, vels)):
        t = i * 0.1
        frames.append(_frame(t, "can0", 0x140, [r]))
        frames.append(_frame(t + 0.01, "can1", 0x141, [v & 0xFF]))
    rf = RawField("can0", 0x140, 0, 1, False, "big")
    vf = RawField("can1", 0x141, 0, 1, True, "big")
    ranked = rank_range_velocity_pairs(frames, [rf], [vf], max_pair_dt=0.06, min_samples=4)
    assert ranked
    assert ranked[0].same_bus is False
    assert ranked[0].score < 1.0


def test_safety_boundary_metadata_is_read_only():
    frames = []
    for i in range(6):
        t = i * 0.1
        frames.append(_frame(t, "can0", 0x150, [100 - 4 * i]))
        frames.append(_frame(t + 0.01, "can0", 0x151, [0xFC]))
    rf = RawField("can0", 0x150, 0, 1, False, "big")
    vf = RawField("can0", 0x151, 0, 1, True, "big")
    candidate = rank_range_velocity_pairs(frames, [rf], [vf], max_pair_dt=0.06, min_samples=4)[0]
    assert candidate.mode == "OFFLINE_READ_ONLY_DISCOVERY"
    assert candidate.auto_promote is False
    assert candidate.actuation == "NONE"
    assert not hasattr(candidate, "command")
    assert not hasattr(candidate, "dbc")
