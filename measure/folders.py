"""The twelve synthetic dev folders: each one's design, seed and file hashes (designs/dev-NN/), the labels
the reviewer and the scorer read, and the project list a run types into the `projects` box."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .generator import build, to_design
from .reviewer import ANY, MODES

DESIGNS = Path(__file__).resolve().parent / "designs"


def folder_names() -> List[str]:
    return sorted(path.name for path in DESIGNS.glob("dev-*") if path.is_dir())


def design_file(folder: str, name: str) -> Any:
    path = DESIGNS / folder / name
    if not path.is_file():
        raise ValueError(f"no {name} for {folder!r}; the folders are {', '.join(folder_names())}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_folder(folder: str, target: Path) -> None:
    """The folder's files under `target`, which is emptied first."""
    record, plan = design_file(folder, "design.json"), design_file(folder, "build.json")
    build(target, to_design(record["design"], record["language"]), int(plan["seed"]))


def hash_tree(top: Path, skip: Iterable[str] = ()) -> Dict[str, str]:
    """sha256 of every file under `top` by its path there, leaving out anything under a skipped name."""
    skipped = set(skip)
    paths = sorted(path for path in top.rglob("*") if path.is_file())
    return {path.relative_to(top).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths if not skipped & set(path.relative_to(top).parts)}


def expected_hashes(folder: str) -> Dict[str, str]:
    """build.json keys each file as the dev folder holds it, under `files/`."""
    hashes = design_file(folder, "build.json")["hashes"]
    return {name.removeprefix("files/"): digest for name, digest in hashes.items()}


def differing(folder: str, found: Dict[str, str]) -> List[str]:
    """Files whose bytes differ from the recorded hashes, or that are missing or extra."""
    expected = expected_hashes(folder)
    return sorted(name for name in set(expected) | set(found) if expected.get(name) != found.get(name))


def rebuild(out_dir: Path, folder: str) -> List[str]:
    """Builds one folder as `<out_dir>/<folder>/files` and names the files that differ from build.json."""
    files = out_dir / folder / "files"
    build_folder(folder, files)
    return differing(folder, hash_tree(files))


def labels(folder: str, mode: str = "edit") -> Dict[str, Any]:
    """What the reviewer answers from and the ladder scores against, as a recorded run's `expect` holds it."""
    if mode not in MODES:
        raise ValueError(f"unknown reviewer mode {mode!r}; known: {', '.join(MODES)}")
    data = design_file(folder, "answers.json")
    return {"answers": data["answers"], "known_by": data["known_by"], "keep_in_place": data["keep_in_place"],
            "ignore": data.get("ignore", []), "mode": mode}


def project_lines(folder: str) -> str:
    """Every labelled project in name order, as `name: about` where the folder has an about for it."""
    about, answers = design_file(folder, "oracle_about.json"), design_file(folder, "answers.json")["answers"]
    names = sorted({label for label in answers.values() if label and label != ANY})
    return "\n".join(f"{name}: {about[name]}" if name in about else name for name in names)


__all__ = ["build_folder", "differing", "folder_names", "hash_tree", "labels", "project_lines", "rebuild"]
