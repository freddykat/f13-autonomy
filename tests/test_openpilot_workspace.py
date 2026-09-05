import copy
import json
from pathlib import Path

import pytest

from tools import openpilot_workspace


LOCK_PATH = Path(__file__).parents[1] / "upstream" / "openpilot.lock.json"
OVERLAY_PATH = Path(__file__).parents[1] / "integration" / "openpilot" / "overlay_manifest.json"


def test_project_lock_and_overlay_are_read_only_and_consistent():
    lock = openpilot_workspace.load_lock(LOCK_PATH)
    overlay = openpilot_workspace.load_overlay(OVERLAY_PATH, lock)

    assert lock["openpilot"]["release"] == "0.11.2"
    assert lock["safety_policy"]["default_mode"] == "SHADOW_ONLY"
    assert lock["safety_policy"]["actuation_authority"] == "NONE"
    assert overlay["target_openpilot_commit"] == lock["openpilot"]["commit"]
    assert all(component["write_capable"] is False for component in overlay["components"])
    assert set(overlay["prohibitions"].values()) == {False}


def test_lock_rejects_enabling_sendcan(tmp_path):
    data = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    data["safety_policy"]["allow_sendcan"] = True
    candidate = tmp_path / "unsafe-lock.json"
    candidate.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(openpilot_workspace.BaselineError, match="allow_sendcan"):
        openpilot_workspace.load_lock(candidate)


def test_overlay_rejects_carcontroller_target(tmp_path):
    lock = openpilot_workspace.load_lock(LOCK_PATH)
    data = json.loads(OVERLAY_PATH.read_text(encoding="utf-8"))
    data["components"][0]["target"] = "opendbc_repo/opendbc/car/bmw/carcontroller.py"
    candidate = tmp_path / "unsafe-overlay.json"
    candidate.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(openpilot_workspace.BaselineError, match="prohibited transmission boundary"):
        openpilot_workspace.load_overlay(candidate, lock)


def test_checkout_verification_checks_head_and_submodule_gitlinks(tmp_path, monkeypatch):
    lock = openpilot_workspace.load_lock(LOCK_PATH)
    answers = {
        ("rev-parse", "HEAD"): lock["openpilot"]["commit"],
        ("ls-tree", "HEAD", "opendbc_repo"): (
            f"160000 commit {lock['critical_submodules']['opendbc_repo']['commit']}\topendbc_repo"
        ),
        ("ls-tree", "HEAD", "panda"): (
            f"160000 commit {lock['critical_submodules']['panda']['commit']}\tpanda"
        ),
    }

    monkeypatch.setattr(openpilot_workspace, "_git", lambda _checkout, arguments: answers[tuple(arguments)])
    report = openpilot_workspace.verify_checkout(tmp_path, lock)

    assert report["status"] == "PASS"
    assert report["actuation_authority"] == "NONE"


def test_checkout_verification_reports_drift(tmp_path, monkeypatch):
    lock = openpilot_workspace.load_lock(LOCK_PATH)
    drifted = copy.deepcopy(lock)
    wrong = "0" * 40
    answers = {
        ("rev-parse", "HEAD"): wrong,
        ("ls-tree", "HEAD", "opendbc_repo"): (
            f"160000 commit {drifted['critical_submodules']['opendbc_repo']['commit']}\topendbc_repo"
        ),
        ("ls-tree", "HEAD", "panda"): (
            f"160000 commit {drifted['critical_submodules']['panda']['commit']}\tpanda"
        ),
    }
    monkeypatch.setattr(openpilot_workspace, "_git", lambda _checkout, arguments: answers[tuple(arguments)])

    report = openpilot_workspace.verify_checkout(tmp_path, drifted)
    assert report["status"] == "FAIL"
    assert "locked commit" in report["errors"][0]


def test_prepare_refuses_nonempty_target(tmp_path):
    lock = openpilot_workspace.load_lock(LOCK_PATH)
    target = tmp_path / "existing"
    target.mkdir()
    (target / "user-data").write_text("preserve", encoding="utf-8")

    with pytest.raises(openpilot_workspace.BaselineError, match="non-empty target"):
        openpilot_workspace.prepare_checkout(target, lock, with_submodules=False)
