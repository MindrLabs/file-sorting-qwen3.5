"""`score`: a run file (jobs with their labels, recorded quality and run bundle, in the form the published
measurements and `run` write) scored again without a model, compared key by key with what it recorded."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, NamedTuple, Optional

from .final import score_run
from .table import QUALITY_KEYS, table_row

MISSING = "(none)"


class JobScore(NamedTuple):
    row: Dict[str, str]
    differences: List[str]  # `key recorded -> scored`, empty when every key matches


class Rescored(NamedTuple):
    rows: List[Dict[str, str]]
    notes: List[str]  # a line per run that differs or could not be scored, then a summary
    matched: int
    jobs: int


def artifact_path(results: Path, relative: str) -> Path:
    """A bundle sits next to the run file or under a folder above it, as the measurements keep them."""
    for base in [results.parent, *results.parent.parents]:
        if (base / relative).is_file():
            return base / relative
    raise FileNotFoundError(f"no {relative} next to {results.name} or under a folder above it")


def folder_of(job: Dict[str, Any]) -> str:
    fixture = PurePosixPath(str((job.get("expect") or {}).get("fixture", "")))
    return fixture.parent.name if fixture.name == "files" else str(job.get("input_id", ""))


def differences(recorded: Dict[str, Any], scored: Dict[str, Any]) -> List[str]:
    if not recorded:
        return ["no recorded quality to compare with"]
    return [f"{key} {recorded.get(key, MISSING)} -> {scored.get(key, MISSING)}" for key in QUALITY_KEYS
            if recorded.get(key, MISSING) != scored.get(key, MISSING)]


def score_job(results: Path, job: Dict[str, Any], line: str) -> Optional[JobScore]:
    """None when the job kept no bundle or carries no labels."""
    artifact = (job.get("artifact") or {}).get("path")
    if not artifact:
        return None
    bundle = json.loads(artifact_path(results, artifact).read_text(encoding="utf-8"))
    scored = score_run(bundle, job.get("expect") or {})
    if scored is None:
        return None
    row = table_row(line, folder_of(job), scored, job.get("runtime") or {}, bundle)
    return JobScore(row, differences(job.get("quality") or {}, scored))


def job_note(job: Dict[str, Any], result: Optional[JobScore]) -> str:
    if result is None:
        return f"{job.get('input_id')}: no run bundle or no labels, not scored"
    return f"{job.get('input_id')}: {', '.join(result.differences)}"


def rescore(results: Path, line: Optional[str] = None) -> Rescored:
    data = json.loads(results.read_text(encoding="utf-8"))
    name = line or str((data.get("spec") or {}).get("id") or results.stem)
    jobs: List[Dict[str, Any]] = data.get("jobs", [])
    scored = [(job, score_job(results, job, name)) for job in jobs]
    matched = sum(1 for _, result in scored if result and not result.differences)
    notes = [job_note(job, result) for job, result in scored if result is None or result.differences]
    notes.append(f"{name}: {matched} of {len(jobs)} runs match the recorded quality "
                 f"on all {len(QUALITY_KEYS)} keys")
    return Rescored([result.row for _, result in scored if result], notes, matched, len(jobs))


def provenance(results: Path) -> List[str]:
    """What a first plan depends on, as the run file recorded it: model file, server settings, machine."""
    data = json.loads(results.read_text(encoding="utf-8"))
    spec, run = data.get("spec") or {}, (data.get("runs") or [{}])[-1]
    env = {key: value for key, value in (spec.get("serve_env") or {}).items() if key != "ORGANIZE_ROOT"}
    version, machine = run.get("version") or {}, run.get("machine") or {}
    revision = (version.get("checkpoint") or {}).get("revision", "not recorded")
    compose = (version.get("model_compose") or {}).get("version", "not recorded")
    device = machine.get("gpu") or machine.get("cpu") or "machine not recorded"
    return ["sha256 of the plan shown at the first approval stop (UTF-8), one dev folder per line",
            "server env: " + (" ".join(f"{key}={value}" for key, value in env.items()) or "not recorded"),
            f"model revision {revision}; {device}; model-compose {compose}"]


__all__ = ["Rescored", "provenance", "rescore"]
