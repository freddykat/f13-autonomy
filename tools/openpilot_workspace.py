#!/usr/bin/env python3
"""Prepare and verify the exact upstream openpilot base used by Prototype 001.

The project deliberately keeps the large upstream checkout outside this Git tree.
This tool turns ``upstream/openpilot.lock.json`` into a reproducible detached
checkout and validates the read-only integration overlay policy.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = REPO_ROOT / "upstream" / "openpilot.lock.json"
DEFAULT_OVERLAY = REPO_ROOT / "integration" / "openpilot" / "overlay_manifest.json"
HEX_COMMIT = re.compile(r"^[0-9a-f]{40}$")


class BaselineError(ValueError):
    """The upstream lock, overlay or checkout violates the project contract."""


def _exact_keys(value: dict[str, Any], expected: set[str], location: str) -> None:
    missing = sorted(expected - set(value))
    unknown = sorted(set(value) - expected)
    if missing or unknown:
        details = []
        if missing:
            details.append(f"missing fields: {', '.join(missing)}")
        if unknown:
            details.append(f"unknown fields: {', '.join(unknown)}")
        raise BaselineError(f"{location}: {'; '.join(details)}")


def _object(value: Any, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BaselineError(f"{location} must be an object")
    return value


def _nonempty_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BaselineError(f"{location} must be a non-empty string")
    return value


def _commit(value: Any, location: str) -> str:
    commit = _nonempty_string(value, location)
    if HEX_COMMIT.fullmatch(commit) is None:
        raise BaselineError(f"{location} must be a full lowercase 40-character Git commit")
    return commit


def load_lock(path: Path = DEFAULT_LOCK) -> dict[str, Any]:
    data = _object(json.loads(path.read_text(encoding="utf-8")), "openpilot lock")
    _exact_keys(
        data,
        {
            "schema_version",
            "captured_at",
            "openpilot",
            "critical_submodules",
            "tracking_snapshot",
            "safety_policy",
        },
        "openpilot lock",
    )
    if data["schema_version"] != 1:
        raise BaselineError("openpilot lock schema_version must be 1")
    _nonempty_string(data["captured_at"], "captured_at")

    upstream = _object(data["openpilot"], "openpilot")
    _exact_keys(upstream, {"repository", "release", "ref", "commit"}, "openpilot")
    if upstream["repository"] != "https://github.com/commaai/openpilot.git":
        raise BaselineError("openpilot.repository must remain the official commaai upstream")
    _nonempty_string(upstream["release"], "openpilot.release")
    ref = _nonempty_string(upstream["ref"], "openpilot.ref")
    if not ref.startswith("refs/heads/"):
        raise BaselineError("openpilot.ref must pin an explicit upstream branch ref")
    _commit(upstream["commit"], "openpilot.commit")

    submodules = _object(data["critical_submodules"], "critical_submodules")
    if set(submodules) != {"opendbc_repo", "panda"}:
        raise BaselineError("critical_submodules must explicitly pin opendbc_repo and panda")
    expected_repositories = {
        "opendbc_repo": "https://github.com/commaai/opendbc.git",
        "panda": "https://github.com/commaai/panda.git",
    }
    for name, raw_spec in submodules.items():
        spec = _object(raw_spec, f"critical_submodules.{name}")
        _exact_keys(spec, {"repository", "commit"}, f"critical_submodules.{name}")
        if spec["repository"] != expected_repositories[name]:
            raise BaselineError(f"critical_submodules.{name}.repository is not the official upstream")
        _commit(spec["commit"], f"critical_submodules.{name}.commit")

    tracking = _object(data["tracking_snapshot"], "tracking_snapshot")
    _exact_keys(tracking, {"ref", "observed_commit", "observed_at"}, "tracking_snapshot")
    _nonempty_string(tracking["ref"], "tracking_snapshot.ref")
    _commit(tracking["observed_commit"], "tracking_snapshot.observed_commit")
    _nonempty_string(tracking["observed_at"], "tracking_snapshot.observed_at")

    policy = _object(data["safety_policy"], "safety_policy")
    _exact_keys(
        policy,
        {
            "default_mode",
            "actuation_authority",
            "allow_sendcan",
            "allow_bmw_controller",
            "allow_panda_safety_changes",
            "allow_flexray_tx",
        },
        "safety_policy",
    )
    if policy["default_mode"] != "SHADOW_ONLY" or policy["actuation_authority"] != "NONE":
        raise BaselineError("the baseline must default to SHADOW_ONLY with actuation_authority NONE")
    for field in (
        "allow_sendcan",
        "allow_bmw_controller",
        "allow_panda_safety_changes",
        "allow_flexray_tx",
    ):
        if policy[field] is not False:
            raise BaselineError(f"safety_policy.{field} must be false during the shadow phase")
    return data


def load_overlay(path: Path, lock: dict[str, Any]) -> dict[str, Any]:
    data = _object(json.loads(path.read_text(encoding="utf-8")), "overlay manifest")
    _exact_keys(
        data,
        {
            "schema_version",
            "target_openpilot_commit",
            "target_opendbc_commit",
            "phase",
            "actuation_authority",
            "components",
            "prohibitions",
        },
        "overlay manifest",
    )
    if data["schema_version"] != 1:
        raise BaselineError("overlay manifest schema_version must be 1")
    if data["target_openpilot_commit"] != lock["openpilot"]["commit"]:
        raise BaselineError("overlay target_openpilot_commit differs from the upstream lock")
    if data["target_opendbc_commit"] != lock["critical_submodules"]["opendbc_repo"]["commit"]:
        raise BaselineError("overlay target_opendbc_commit differs from the upstream lock")
    if data["phase"] != "SHADOW_ONLY" or data["actuation_authority"] != "NONE":
        raise BaselineError("the overlay must remain SHADOW_ONLY with actuation_authority NONE")

    components = data["components"]
    if not isinstance(components, list) or not components:
        raise BaselineError("overlay components must be a non-empty list")
    seen_names: set[str] = set()
    for index, raw_component in enumerate(components):
        location = f"components[{index}]"
        component = _object(raw_component, location)
        _exact_keys(
            component,
            {"name", "target", "state", "consumes", "publishes", "write_capable"},
            location,
        )
        name = _nonempty_string(component["name"], f"{location}.name")
        if name in seen_names:
            raise BaselineError(f"duplicate overlay component: {name}")
        seen_names.add(name)
        target = _nonempty_string(component["target"], f"{location}.target")
        if any(part in target.lower() for part in ("carcontroller", "panda/board/safety", "sendcan")):
            raise BaselineError(f"{location}.target enters a prohibited transmission boundary")
        if component["state"] not in {"PLANNED", "IMPLEMENTED"}:
            raise BaselineError(f"{location}.state must be PLANNED or IMPLEMENTED")
        if component["write_capable"] is not False:
            raise BaselineError(f"{location}.write_capable must be false")
        for field in ("consumes", "publishes"):
            values = component[field]
            if not isinstance(values, list) or not all(isinstance(item, str) and item for item in values):
                raise BaselineError(f"{location}.{field} must contain non-empty strings")

    prohibitions = _object(data["prohibitions"], "prohibitions")
    _exact_keys(
        prohibitions,
        {
            "carcontroller",
            "sendcan",
            "panda_safety_patch",
            "flexray_tx",
            "tesla_to_bmw_command_translation",
        },
        "prohibitions",
    )
    for name, present in prohibitions.items():
        if present is not False:
            raise BaselineError(f"prohibitions.{name} must be false")
    return data


def _git(checkout: Path, arguments: Iterable[str]) -> str:
    command = ["git", "-C", str(checkout), *arguments]
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or "unknown Git error"
        raise BaselineError(f"Git command failed: {' '.join(command)}: {detail}") from exc
    return result.stdout.strip()


def verify_checkout(checkout: Path, lock: dict[str, Any]) -> dict[str, Any]:
    if not checkout.is_dir():
        raise BaselineError(f"openpilot checkout does not exist: {checkout}")

    expected_head = lock["openpilot"]["commit"]
    observed_head = _git(checkout, ["rev-parse", "HEAD"])
    errors: list[str] = []
    if observed_head != expected_head:
        errors.append(f"HEAD {observed_head} != locked commit {expected_head}")

    observed_submodules: dict[str, str | None] = {}
    for path, spec in lock["critical_submodules"].items():
        entry = _git(checkout, ["ls-tree", "HEAD", path])
        match = re.fullmatch(r"160000 commit ([0-9a-f]{40})\t(.+)", entry)
        observed = None if match is None else match.group(1)
        observed_submodules[path] = observed
        if observed != spec["commit"]:
            errors.append(f"{path} {observed} != locked commit {spec['commit']}")

    return {
        "schema_version": 1,
        "status": "PASS" if not errors else "FAIL",
        "checkout": str(checkout.resolve()),
        "release": lock["openpilot"]["release"],
        "expected_commit": expected_head,
        "observed_commit": observed_head,
        "critical_submodules": observed_submodules,
        "errors": errors,
        "mode": lock["safety_policy"]["default_mode"],
        "actuation_authority": "NONE",
    }


def prepare_checkout(target: Path, lock: dict[str, Any], *, with_submodules: bool) -> dict[str, Any]:
    if target.exists() and any(target.iterdir()):
        raise BaselineError(f"refusing to use non-empty target directory: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir(exist_ok=True)

    _git(target, ["init"])
    _git(target, ["remote", "add", "origin", lock["openpilot"]["repository"]])
    _git(target, ["fetch", "--depth", "1", "origin", lock["openpilot"]["ref"]])
    fetched_commit = _git(target, ["rev-parse", "FETCH_HEAD"])
    if fetched_commit != lock["openpilot"]["commit"]:
        raise BaselineError(
            "the locked upstream ref moved; review and update the lock instead of building an unreviewed commit"
        )
    _git(target, ["checkout", "--detach", fetched_commit])
    if with_submodules:
        _git(target, ["submodule", "update", "--init", "--recursive"])
    return verify_checkout(target, lock)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--overlay", type=Path, default=DEFAULT_OVERLAY)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate the lock and read-only overlay without network access")
    verify = subparsers.add_parser("verify", help="verify an existing upstream checkout")
    verify.add_argument("checkout", type=Path)
    prepare = subparsers.add_parser("prepare", help="create a detached checkout at the locked commit")
    prepare.add_argument("target", type=Path)
    prepare.add_argument("--with-submodules", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        lock = load_lock(args.lock)
        overlay = load_overlay(args.overlay, lock)
        if args.command == "validate":
            report = {
                "status": "PASS",
                "release": lock["openpilot"]["release"],
                "openpilot_commit": lock["openpilot"]["commit"],
                "opendbc_commit": lock["critical_submodules"]["opendbc_repo"]["commit"],
                "overlay_phase": overlay["phase"],
                "actuation_authority": "NONE",
            }
        elif args.command == "verify":
            report = verify_checkout(args.checkout, lock)
        else:
            report = prepare_checkout(args.target, lock, with_submodules=args.with_submodules)
    except (BaselineError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2, sort_keys=True))
        return 2

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
