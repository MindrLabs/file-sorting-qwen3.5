"""The model-compose HTTP API the way the web UI uses it: start a workflow as a task, follow it, answer every
approval stop through the resume endpoint, and run a workflow that needs no answer (undo) to the end."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, NamedTuple, Optional

POLL_SEC = 2.0
TIMEOUT_SEC = 1800.0
DONE = ("completed", "failed", "cancelled")
JSON = {"Content-Type": "application/json"}

# (the stop as the server sent it, how many stops came before) -> the answer; None approves as is.
Answer = Callable[[Dict[str, Any], int], Optional[str]]


class ServerError(RuntimeError):
    """The server answered with an error, or a task did not finish in time."""


class ServerUnreachable(ServerError):
    """Nothing answered at the API address."""


class TaskRun(NamedTuple):
    state: Dict[str, Any]
    stops: List[Dict[str, Any]]  # {"interrupt": ..., "answer": ...} in the order they came
    gen_sec: float


def call(method: str, url: str, body: Optional[Dict[str, Any]] = None, timeout: float = 60.0) -> bytes:
    data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers=JSON)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            answer: bytes = response.read()
            return answer
    except urllib.error.HTTPError as error:
        raise ServerError(f"HTTP {error.code} on {url}: {error.read()[:300]!r}") from error
    except (urllib.error.URLError, OSError) as error:
        raise ServerUnreachable(f"{url} unreachable: {error}") from error


def call_json(method: str, url: str, body: Optional[Dict[str, Any]] = None) -> Any:
    return json.loads(call(method, url, body))


def start_task(api: str, workflow: str, fields: Dict[str, Any]) -> str:
    payload = {"workflow_id": workflow, "input": fields, "wait_for_completion": False}
    return str(call_json("POST", f"{api}/workflows/runs", payload)["task_id"])


def pending_points(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    points = state.get("interrupt") or []
    if not isinstance(points, list):
        raise ServerError("the server sent one stop, not a list: model-compose is older than batched resume")
    if not all(isinstance(point, dict) and point.get("id") for point in points):
        raise ServerError(f"a stop without an id cannot be answered: {points!r:.300}")
    return points


def answer_stops(api: str, task_id: str, points: List[Dict[str, Any]], answer: Answer,
                 before: int) -> List[Dict[str, Any]]:
    """Stops that come together go back in one resume, keyed by the id the server gave each."""
    if not points:
        return []
    replies = [answer(point, before + index) for index, point in enumerate(points)]
    answers = {point["id"]: reply for point, reply in zip(points, replies)}
    call_json("POST", f"{api}/tasks/{task_id}/resume", {"answer": answers})
    return [{"interrupt": point, "answer": reply} for point, reply in zip(points, replies)]


def run_task(api: str, workflow: str, fields: Dict[str, Any], answer: Answer,
             timeout_sec: float = TIMEOUT_SEC) -> TaskRun:
    task_id, started = start_task(api, workflow, fields), time.perf_counter()
    stops: List[Dict[str, Any]] = []
    while time.perf_counter() - started < timeout_sec:
        state = call_json("GET", f"{api}/tasks/{task_id}")
        if state.get("status") in DONE:
            return TaskRun(state, stops, round(time.perf_counter() - started, 3))
        if state.get("status") == "interrupted":
            stops.extend(answer_stops(api, task_id, pending_points(state), answer, len(stops)))
        time.sleep(POLL_SEC)
    raise ServerError(f"task {task_id} still running after {timeout_sec:.0f}s")


def run_workflow(api: str, workflow: str, fields: Dict[str, Any]) -> str:
    """A workflow with no stop, waited for; its output as the server sends it."""
    payload = {"workflow_id": workflow, "input": fields, "wait_for_completion": True, "output_only": True}
    answer = call("POST", f"{api}/workflows/runs", payload, timeout=TIMEOUT_SEC)
    return answer.decode("utf-8", errors="replace")


__all__ = ["Answer", "ServerError", "ServerUnreachable", "TaskRun", "run_task", "run_workflow"]
