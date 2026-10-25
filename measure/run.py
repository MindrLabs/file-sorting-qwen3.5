"""`run`: one dev folder at a time against a running server. Stage the folder in the server's root, run the
workflow with the folder's project list, answer each approval stop as the stand-in reviewer, undo every
applied plan, and score the run the way the published numbers were scored.

Next to the table it keeps each run's bundle and a run file in the recorded form, so `score` can read it."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from .final import score_run
from .folders import differing, labels, project_lines
from .reviewer import answer, plan_moves, with_ignored
from .server import Answer, run_task, run_workflow
from .table import first_plan_sha256, read_table, table_row, write_table
from .workspace import events, journals, stage, tree

UNDO = "undo"


class Settings(NamedTuple):
    api: str
    root: Path       # the server's ORGANIZE_ROOT
    workflow: str
    line: str
    mode: str
    out: Path        # the table; `<stem>.json` and `<stem>-runs/` go next to it
    resume: bool = False


class Earlier(NamedTuple):
    jobs: List[Dict[str, Any]]
    rows: List[Dict[str, str]]


class WrongRoot(RuntimeError):
    """The plan names a file the staged folder does not have: the server organizes another folder."""


def plan_of(point: Dict[str, Any]) -> str:
    plan = (point.get("metadata") or {}).get("plan", "")
    return plan if isinstance(plan, str) else json.dumps(plan, ensure_ascii=False)


def check_same_root(plan: str, root: Path) -> None:
    missing = [move.source for move in plan_moves(plan) if not (root / move.source).is_file()]
    if missing:
        raise WrongRoot(f"the plan moves {missing[0]!r}, which is not in {root}. Start the server with "
                        "ORGANIZE_ROOT set to that folder. Nothing was approved; cancel the waiting run "
                        "in the web UI.")


def reviewer_reply(expect: Dict[str, Any], root: Path) -> Answer:
    answers = with_ignored(expect["answers"], list(expect.get("ignore") or []))
    keep, rejected = set(expect.get("keep_in_place") or []), [0]

    def reply(point: Dict[str, Any], before: int) -> Optional[str]:
        check_same_root(plan_of(point), root)
        text = answer(plan_of(point), expect["mode"], rejected[0], answers, keep)
        rejected[0] += bool(text and text.startswith("REJECT:"))
        return text
    return reply


def run_folder(settings: Settings, folder: str, expect: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
    """The run as one bundle, in the form the recorded runs keep, and its seconds to finish."""
    root = settings.root
    stage(root, folder)
    fields = {"projects": project_lines(folder)}
    task = run_task(settings.api, settings.workflow, fields, reviewer_reply(expect, root))
    applied, logged, after = journals(root), events(root), sorted(tree(root))
    for _ in applied:
        run_workflow(settings.api, UNDO, {})
    stops = [{"plan": plan_of(stop["interrupt"]), "answer": stop["answer"]} for stop in task.stops]
    state = task.state
    return {"status": state.get("status"), "output": state.get("output"), "error": state.get("error"),
            "stops": stops, "journals": applied, "events": logged, "files_after": after,
            "undo_clean": not differing(folder, tree(root))}, task.gen_sec


def job_record(settings: Settings, folder: str, expect: Dict[str, Any], bundle: Dict[str, Any],
               gen_sec: float) -> Dict[str, Any]:
    runtime = {"gen_sec": gen_sec, "peak_mb": None, "status": bundle["status"], "stops": len(bundle["stops"]),
               "undo_clean": bundle["undo_clean"]}
    return {"input_id": f"{folder}-{settings.mode}", "fields": {"projects": project_lines(folder)},
            "expect": {"fixture": f"{folder}/files", **expect}, "runtime": runtime,
            "quality": score_run(bundle, expect) or {},
            "artifact": {"path": f"{settings.out.stem}-runs/{folder}.json"}}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def progress(folder: str, job: Dict[str, Any], bundle: Dict[str, Any]) -> str:
    runtime, quality = job["runtime"], job["quality"]
    undo = "clean" if runtime["undo_clean"] else "NOT clean"
    return (f"{folder}: {runtime['status']}, {runtime['stops']} stop(s), {runtime['gen_sec']}s, "
            f"first plan {first_plan_sha256(bundle)[:12] or 'none'}, "
            f"wrong share {quality.get('wrong_share')}, undo {undo}")


def spec_of(settings: Settings) -> Dict[str, str]:
    return {"id": settings.line, "workflow": settings.workflow}


def earlier_runs(settings: Settings) -> Earlier:
    """With resume, the folders a stopped run of the same line, workflow and mode already wrote."""
    results = settings.out.with_suffix(".json")
    if not settings.resume or not results.is_file() or not settings.out.is_file():
        return Earlier([], [])
    data = json.loads(results.read_text(encoding="utf-8"))
    jobs, rows = list(data.get("jobs") or []), read_table(settings.out)
    ids = {f"{row['folder']}-{settings.mode}" for row in rows}
    if data.get("spec") != spec_of(settings) or ids != {job["input_id"] for job in jobs}:
        raise ValueError(f"{results} is a run of another line, workflow or mode, or its table differs; "
                         "resume adds only to the same run")
    return Earlier(jobs, rows)


def run(settings: Settings, folders: List[str]) -> None:
    """Writes the table, the run file and the bundles after every folder, so a stopped run keeps its rows."""
    earlier = earlier_runs(settings)
    rows, jobs = list(earlier.rows), list(earlier.jobs)
    done = {row["folder"] for row in rows}
    for folder in folders:
        if folder in done:
            print(f"{folder}: already in {settings.out}, not run again", flush=True)
            continue
        expect = labels(folder, settings.mode)
        bundle, gen_sec = run_folder(settings, folder, expect)
        job = job_record(settings, folder, expect, bundle, gen_sec)
        write_json(settings.out.parent / job["artifact"]["path"], bundle)
        jobs.append(job)
        rows.append(table_row(settings.line, folder, job["quality"], job["runtime"], bundle))
        write_table(settings.out, rows)
        write_json(settings.out.with_suffix(".json"), {"spec": spec_of(settings), "jobs": jobs})
        print(progress(folder, job, bundle), flush=True)


__all__ = ["Settings", "WrongRoot", "run"]
