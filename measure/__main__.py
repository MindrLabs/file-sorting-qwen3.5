"""`python3 -m measure <command>` from the release folder: rebuild, run, score and check (README.md)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, List, Optional, Sequence

from . import folders, hashes, rescore, run
from .reviewer import MODES
from .server import ServerError
from .table import write_table
from .workspace import NotStageable

EVERY_FOLDER = "dev-01,dev-02 (default: all twelve)"


def chosen(text: Optional[str]) -> List[str]:
    """`dev-01,dev-02`, or every folder."""
    names = folders.folder_names()
    picked = [name.strip() for name in text.split(",") if name.strip()] if text else names
    unknown = [name for name in picked if name not in names]
    if unknown:
        raise ValueError(f"unknown folder {unknown[0]}; the folders are {', '.join(names)}")
    return picked


def rebuild_command(args: argparse.Namespace) -> int:
    differing = 0
    for folder in chosen(args.folders):
        wrong = folders.rebuild(Path(args.out_dir), folder)
        differing += bool(wrong)
        verdict = f"{len(wrong)} files differ, first {wrong[0]}" if wrong else "every file matches its hash"
        print(f"{folder}: {verdict}")
    return int(differing > 0)


def run_command(args: argparse.Namespace) -> int:
    out = Path(args.out)
    if out.suffix != ".csv":
        raise ValueError("--out names the table and ends in .csv; the run file and the bundles go next to it")
    settings = run.Settings(args.api.rstrip("/"), Path(args.root).expanduser().resolve(), args.workflow,
                            args.line or args.workflow, args.mode, out, args.resume)
    run.run(settings, chosen(args.folders))
    print(f"wrote {out}, {out.with_suffix('.json')} and {out.stem}-runs/ next to it")
    return 0


def score_command(args: argparse.Namespace) -> int:
    result = rescore.rescore(Path(args.results), args.line)
    print("\n".join(result.notes))
    if args.out:
        write_table(Path(args.out), result.rows)
    if args.hashes:
        hashes.write_hashes(Path(args.hashes), result.rows, rescore.provenance(Path(args.results)))
    return int(result.matched != result.jobs)


def check_command(args: argparse.Namespace) -> int:
    lines, same = hashes.check(Path(args.table), Path(args.hashes))
    print("\n".join(lines))
    return int(not same)


def add_rebuild(commands: Any) -> None:
    command = commands.add_parser("rebuild", help="build the dev folders and check every file's hash")
    command.add_argument("out_dir", help="each folder is built as <out_dir>/dev-NN/files")
    command.add_argument("--folders", help=EVERY_FOLDER)
    command.set_defaults(handler=rebuild_command)


def add_run(commands: Any) -> None:
    command = commands.add_parser("run", help="run the organizer on dev folders against a running server")
    command.add_argument("--api", default="http://localhost:8080/api", help="the server's HTTP API")
    command.add_argument("--root", required=True, help="the server's ORGANIZE_ROOT; emptied each time")
    command.add_argument("--workflow", default="organize", help="organize (default) or organize-quick")
    command.add_argument("--folders", help=EVERY_FOLDER)
    command.add_argument("--mode", choices=MODES, default="edit", help="how the stand-in reviewer answers")
    command.add_argument("--line", help="as in first-plans/<line>.sha256 (default: the workflow)")
    command.add_argument("--out", default="results.csv", help="the table (.csv); run files go beside it")
    command.add_argument("--resume", action="store_true",
                         help="keep the folders --out already holds from the same line and mode; run the rest")
    command.set_defaults(handler=run_command)


def add_score(commands: Any) -> None:
    command = commands.add_parser("score", help="score a recorded run file again and compare")
    command.add_argument("results", help="a run file: the <stem>.json that run writes, or a recorded one")
    command.add_argument("--line", help="the table's line name (default: the run file's id)")
    command.add_argument("--out", help="write the rows as a table (.csv)")
    command.add_argument("--hashes", help="write first-plans/<line>.sha256 from the rows")
    command.set_defaults(handler=score_command)


def add_check(commands: Any) -> None:
    command = commands.add_parser("check", help="compare first plans with first-plans/<line>.sha256")
    command.add_argument("table")
    command.add_argument("hashes")
    command.set_defaults(handler=check_command)


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="python3 -m measure", description=__doc__)
    commands = top.add_subparsers(required=True, metavar="command")
    for add in (add_rebuild, add_run, add_score, add_check):
        add(commands)
    return top


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (ServerError, NotStageable, run.WrongRoot, ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
