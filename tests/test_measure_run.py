"""`run` against a stand-in server shaped like the release compose: one approval stop with the plan in its
metadata, the answered plan moved with an undo journal, and an undo workflow that puts it back."""
from fixtures import run_tests, scratch_root

import hashlib
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from measure import server  # noqa: E402
from measure.__main__ import main  # noqa: E402
from measure.folders import differing, project_lines  # noqa: E402
from measure.rescore import rescore  # noqa: E402
from measure.table import read_table  # noqa: E402
from measure.workspace import tree  # noqa: E402

server.POLL_SEC = 0.01
LINE = "dev-9b-q4km-names-about-vote-8k"
# For dev-01: two right lines and a file nobody could file, which the reviewer removes.
PLAN = "bank_closures_notes.txt => bank-closures\nbank_closures_tracker.xlsx => bank-closures\nclipboard.txt => bank-closures"


def move(root: Path, plan: str) -> None:
    pairs = [line.split(" => ") for line in plan.splitlines() if " => " in line]
    for source, project in pairs:
        (root / project).mkdir(exist_ok=True)
        (root / source).rename(root / project / source)
    record = {"moves": [{"from": source, "to": f"{project}/{source}"} for source, project in pairs],
              "created_dirs": sorted({project for _, project in pairs})}
    (root / ".organizer" / "runs").mkdir(parents=True, exist_ok=True)
    (root / ".organizer" / "runs" / "0001.json").write_text(json.dumps(record), encoding="utf-8")


def undo(root: Path) -> str:
    journal = sorted((root / ".organizer" / "runs").glob("*.json"))[-1]
    record = json.loads(journal.read_text(encoding="utf-8"))
    for step in reversed(record["moves"]):
        (root / step["to"]).rename(root / step["from"])
    for name in record["created_dirs"]:
        (root / name).rmdir()
    journal.rename(journal.with_suffix(".undone"))
    return "restored"


class FakeCompose(BaseHTTPRequestHandler):
    root, plan = Path("."), PLAN
    inputs: List[Dict[str, Any]] = []
    answers: List[Optional[str]] = []

    def log_message(self, *args: Any) -> None:
        pass

    def reply(self, body: Any) -> None:
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path.endswith("/resume"):
            FakeCompose.answers.append(body["answer"]["approve-1"])
            move(FakeCompose.root, FakeCompose.answers[-1] or FakeCompose.plan)
            return self.reply({"ok": True})
        if body["workflow_id"] == "undo":
            return self.reply(undo(FakeCompose.root))
        FakeCompose.inputs.append(body["input"])
        self.reply({"task_id": "t1"})

    def do_GET(self) -> None:
        if len(FakeCompose.answers) < len(FakeCompose.inputs):
            return self.reply({"status": "interrupted", "interrupt": [{"id": "approve-1", "metadata": {"plan": FakeCompose.plan}}]})
        self.reply({"status": "completed", "output": "2 moved, 0 skipped."})


def serve(root: Path, plan: str = PLAN) -> str:
    FakeCompose.root, FakeCompose.plan, FakeCompose.inputs, FakeCompose.answers = root, plan, [], []
    http = ThreadingHTTPServer(("127.0.0.1", 0), FakeCompose)
    threading.Thread(target=http.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{http.server_port}/api"


def run(api: str, root: Path, out: Path, *extra: str) -> int:
    return main(["run", "--api", api, "--root", str(root), "--folders", "dev-01", "--line", LINE, "--out", str(out),
                 *extra])


def test_resume_keeps_the_folders_already_written_and_does_not_run_them_again():
    scratch = scratch_root({})
    root, out = scratch / "workspace", scratch / "results.csv"
    assert run(serve(root), root, out) == 0
    first = out.read_text(encoding="utf-8")
    api = serve(root)
    assert run(api, root, out, "--resume") == 0
    assert FakeCompose.inputs == [] and out.read_text(encoding="utf-8") == first
    assert rescore(out.with_suffix(".json")).matched == 1
    assert run(api, root, out) == 0 and len(FakeCompose.inputs) == 1  # without --resume it runs again


def test_resume_refuses_a_run_file_of_another_line_or_mode():
    scratch = scratch_root({})
    root, out = scratch / "workspace", scratch / "results.csv"
    assert run(serve(root), root, out) == 0
    api = serve(root)
    assert main(["run", "--api", api, "--root", str(root), "--folders", "dev-01", "--line", "other", "--out", str(out),
                 "--resume"]) == 1
    assert run(api, root, out, "--resume", "--mode", "reject") == 1
    assert FakeCompose.inputs == []


def test_a_folder_is_staged_run_reviewed_undone_and_scored():
    scratch = scratch_root({})
    root, out = scratch / "workspace", scratch / "out" / "results.csv"
    assert run(serve(root), root, out) == 0
    assert FakeCompose.inputs == [{"projects": project_lines("dev-01")}]
    assert FakeCompose.answers == ["bank_closures_notes.txt => bank-closures\nbank_closures_tracker.xlsx => bank-closures"]
    assert differing("dev-01", tree(root)) == []
    [row] = read_table(out)
    assert (row["line"], row["folder"], row["edited_lines"], row["approvals"]) == (LINE, "dev-01", "1", "1")
    assert row["first_plan_sha256"] == hashlib.sha256(PLAN.encode("utf-8")).hexdigest()
    assert (row["step1_tool"], row["usable"], row["peak_mb"]) == ("", "0", "")  # no tool log, too little moved, not measured
    assert rescore(out.with_suffix(".json")).matched == 1


def test_a_plan_from_another_folder_is_never_answered():
    root = scratch_root({}) / "workspace"
    assert run(serve(root, "somewhere_else.txt => notes"), root, root.parent / "results.csv") == 1
    assert FakeCompose.answers == []


def test_a_folder_with_someone_elses_files_is_left_alone():
    root = scratch_root({"my-notes.txt": "keep me"})
    assert run(serve(root), root, root.parent / "results.csv") == 1
    assert (root / "my-notes.txt").read_text(encoding="utf-8") == "keep me" and FakeCompose.inputs == []


run_tests(globals())
