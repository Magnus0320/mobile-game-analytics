"""§7.7 step 1 (resolve and record the environment) and step 19 (write manifest)."""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import config
from .run_state import RunState


def _installed_versions() -> dict[str, str]:
    import importlib.metadata as md
    return {name: md.version(name) for name in config.DIRECT_DEPENDENCIES}


def _lockfile_pins() -> dict[str, str]:
    pins: dict[str, str] = {}
    if not config.LOCKFILE_PATH.exists():
        return pins
    for line in config.LOCKFILE_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        name, _, version = line.partition("==")
        pins[name.strip().lower().replace("_", "-")] = version.strip()
    return pins


def resolve_environment(state: RunState) -> dict:
    """§7.7 step 1. Hard stop if the interpreter minor is not 3.12 or a pinned
    package version does not match the lock file."""
    minor = sys.version_info[:2]
    if minor != config.REQUIRED_PYTHON_MINOR:
        raise RuntimeError(
            f"Interpreter minor version is {minor[0]}.{minor[1]}, but "
            f"{config.REQUIRED_PYTHON_MINOR[0]}.{config.REQUIRED_PYTHON_MINOR[1]} is "
            "pinned in .python-version (§7.5, A-026). The minor version may not "
            "change without a superseding assumptions.md entry."
        )

    installed = _installed_versions()
    pins = _lockfile_pins()
    mismatches = {
        name: {"installed": version,
               "locked": pins.get(name.lower().replace("_", "-"))}
        for name, version in installed.items()
        if pins.get(name.lower().replace("_", "-")) not in (None, version)
    }
    if mismatches:
        raise RuntimeError(
            "Installed package versions do not match requirements.lock.txt "
            f"(§7.5): {mismatches}. Install for reproduction from the lock file."
        )

    # §7.5 requires the Agg backend to be set explicitly. It is set HERE, at
    # step 1, so that what the manifest records is what the run actually used.
    import matplotlib

    matplotlib.use(config.FIG_BACKEND, force=True)

    environment = {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "packages": installed,
        "matplotlib_version": matplotlib.__version__,
        "matplotlib_backend": matplotlib.get_backend(),
        "random_seed": config.RANDOM_SEED,
        "n_resamples": config.N_RESAMPLES,
    }
    state.finding(
        step=1,
        finding_id="environment.resolved",
        description=(
            "Interpreter, resolved package versions, matplotlib backend and the "
            "single RNG seed recorded. Package versions were checked against "
            "requirements.lock.txt."
        ),
        values=environment,
    )
    return environment


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_manifest(*, environment: dict, provenance: dict, raw_rows: int,
                   decision, srm: dict, primary: dict, guardrail: dict,
                   state: RunState, outputs: list[Path]) -> Path:
    """Byte-identical across machines except for `run_timestamp_utc`, which §7.5
    exempts. Keys are sorted and floats are written by json's repr, so the file
    is stable under re-run."""
    manifest = {
        "part": 3,
        "preregistration": {
            "architecture_commit": config.PREREGISTRATION_COMMIT,
            "architecture_blob_sha": config.ARCHITECTURE_BLOB_SHA,
            "architecture_file_sha256": _sha256(config.ARCHITECTURE_PATH),
            "assumptions_file_sha256": _sha256(config.ASSUMPTIONS_PATH),
            "note": (
                "The Part 3 report cites the architecture commit. The file hashes "
                "let a reader confirm the document was not altered after that "
                "commit without needing the repository."
            ),
        },
        "environment": environment,
        "input": {
            "dataset_slug": config.DATASET_SLUG,
            "file_name": provenance["file_name"],
            "sha256": provenance["sha256"],
            "raw_rows": raw_rows,
            "recorded_row_count": provenance["recorded_row_count"],
            "committed": False,
            "note": "data/raw/ is git-ignored (§5.5); the README documents the fetch.",
        },
        "integrity": {
            "downgraded": state.is_downgraded,
            "downgrade_sources": [d.source for d in state.downgrades],
            "downgrade_details": [d.detail for d in state.downgrades],
            "srm_exact_binomial_p": srm["exact_binomial_p"],
            "srm_tripped": srm["tripped"],
        },
        "decision": {
            "precondition": decision.precondition or "clean",
            "stage2_branch": decision.stage2_branch,
            "stage2_drives_recommendation": decision.stage2_drives_recommendation,
            "stage3_modifier": decision.stage3_modifier or "not applied",
            "recommendation": decision.recommendation or "WITHHELD",
            "recommendation_withheld": decision.recommendation_withheld,
            "rule_path": decision.rule_path,
        },
        "headline": {
            "delta_7_pp": primary["delta_pp"],
            "p_7": primary["p_value"],
            "ci_7_bootstrap_pp": [primary["bootstrap_ci_low_pp"],
                                  primary["bootstrap_ci_high_pp"]],
            "ci_7_analytic_pp": [primary["analytic_ci_low_pp"],
                                 primary["analytic_ci_high_pp"]],
            "bootstrap_mc_se_pp": primary["bootstrap_mc_se_pp"],
            "delta_1_pp": guardrail["delta_pp"],
            "ci_1_bootstrap_pp": [guardrail["bootstrap_ci_low_pp"],
                                  guardrail["bootstrap_ci_high_pp"]],
        },
        "denominators": dict(sorted(state.denominators.items())),
        "outputs": [
            {"path": str(p.relative_to(config.PROJECT_ROOT)), "sha256": _sha256(p)}
            for p in sorted(outputs, key=lambda p: str(p))
        ],
        "findings": [
            {"step": f.step, "finding_id": f.finding_id, "description": f.description}
            for f in state.findings
        ],
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    config.MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return config.MANIFEST_PATH
